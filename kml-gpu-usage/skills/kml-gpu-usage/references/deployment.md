# KML 部署、资源安排和共享盘

## 本次记录才是资源入口

项目授权节点清单优先于完整 hostfile；只检查和使用允许的范围。重新核对 record、launcher/worker、SSH 主机身份与连接参数，不沿用其他记录的地址或关闭校验来绕过连接问题。

每节点通常八张 H100；总节点数、参与计算的 launcher、可用卡和显存由本次记录决定。发现不符合八卡前提时先报告并调整映射，不隐式补卡。逐节点保存带时间的快照，不能用 hostfile slots 推断设备健康。

```bash
# 在目标节点，使用项目 Python；脚本与输出路径取自实际 skill/project 位置。
python /path/to/kml-gpu-usage/scripts/node_snapshot.py \
  --mount /mmu_vlm_hdd --output /project/run/resource-node.json
```

快照包含当前解释器、GPU 枚举/Fabric/拓扑、RDMA 端口与 link layer、CPU affinity/可见 cgroup 限制、内存、共享盘、共享内存和包元数据。不分配 CUDA tensor、不测 NCCL 吞吐，不证明某个已安装包可导入或被模型使用。选择实际项目 Python，而非误用基础镜像 Python。详细资源输出留在项目内，分享时按需去除内部地址/设备标识。

## 环境与资产

- 代码、项目环境、权重、数据、下载分片、缓存、编译产物、临时文件、日志和 checkpoints 放到项目指定的共享存储根；通常在 `/mmu_vlm_hdd` 下，具体路径由项目决定。
- 每节点确认相同挂载和权限；worker 启动时显式 source 项目环境。基础镜像已有 torch 不等于项目环境已就绪。
- 锁定镜像 digest、代码 commit、数据/模型 revision、PyTorch/CUDA/NCCL/Triton/attention/TE 版本；避免各节点 `pip install -U` 形成不一致环境。
- 明确 HF、datasets、Torch、Triton、Inductor、XDG 等缓存位置与并发策略，提前准备资产，避免大量 rank 同时下载、解压和争抢共享编译缓存。
- 只有项目与平台允许时才用节点本地 NVMe；确认容量、生命周期、恢复流程。不默认把环境/数据写到 `/root` 或容器根盘，也不修改 HOME 来迁移缓存。
- 共享 checkout 在运行时固定 commit；并行不同版本用隔离 checkout，避免 worker 运行中 pull/checkout 造成代码漂移。

## 启动与调度

hostfile 不会自动启动所有 rank。普通每卡一进程、完整使用各节点八卡的 DDP，可以在每个参与节点启动一个 agent：

```bash
torchrun \
  --nnodes="$NUM_NODES" \
  --nproc-per-node=8 \
  --node-rank="$NODE_RANK" \
  --master-addr="$MASTER_ADDR" \
  --master-port="$MASTER_PORT" train.py
```

变量由本次分配生成：节点 rank 唯一且连续，所有节点对节点数和内部 rendezvous 地址一致，进程绑定正确的本地 GPU。部分卡准入或 TP/PP/CP/Ray/actor-rollout 混合资源使用框架专用 launcher 和通信组映射，不把上面的 DDP 示例直接套进去。

作业使用独立 exp_id、输出目录、端口和资源映射，有可靠的多机进程管理、退出/失败传播、checkpoint 和游标。仅清理本作业拥有的进程，不使用全局 pkill 或 `ray stop --force`。

GPU 分享按实时空闲显存、新增任务峰值与余量准入。若没有项目规定，可将 `max(8GiB, 峰值的15%)` 作为保守初值，随后用代表性 profile 修订；它不是普遍保证。正式性能比较还需控制共驻干扰。OOM 首先查最长输入、并发、padding、临时缓冲和显存碎片，再降低微批/并发或修改显存策略；不能停止其他任务腾卡。

GPU-hours 按分配/预留 GPU 数对时间积分，包含工具等待与作业空转；不能用利用率折扣卡时。对小模型、LoRA、seed/消融，比较多个独立作业和一个大作业完成研究矩阵的成本。

## 数据和 checkpoint

- 预 tokenize、索引和按任务语义预处理；将大量小文件整理为可顺序读取的 shards 或适合随机读取的列式/索引格式。冻结模块的表征缓存须记录模型版本，保持随机增强语义。
- 每 rank 的分片/sampler 正确，保存恢复游标；不要各节点重复扫描/读取整个数据集。
- loader worker 数按 rank 累加，还需计入解码/OpenMP 线程。结合实际 CPU quota、NUMA、共享盘和内存调 worker、prefetch、persistent_workers、pinned memory 与异步 H2D，不能越多越好。
- checkpoint 优先框架支持的分片保存/DCP，避免每 rank 写完整权重或 rank 0 聚集全部状态。异步 staging 占内存和 IO，限制并发保存，等待完成后认定可恢复。
- 恢复核对包括 optimizer、scheduler、RNG、sampler/global step；评估、保存和故障恢复都计入完整 wall time。大产物按项目保留/备份策略管理。
