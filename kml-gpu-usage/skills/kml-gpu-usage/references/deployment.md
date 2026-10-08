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

### 占卡程序与正式任务的协调

本机约定的共享入口是 `/mmu_vlm_hdd/home/rhsu/idle-job-can-kill-anytime/idle-job`，目录内有该程序的 `AGENTS.md` 和 `README.md`。按目标实例的 launcher 执行，先确认身份和范围；同一共享目录中的其他实例有独立清单、进程记录、暂停与预约，当前实例的 `stop` 不应影响它们。

用户授权 Agent 在需要使用 GPU 时直接停止此程序，无需再询问。纯只读调查先检查程序路径、本实例已有 manifest/status，记录启用、暂停、未登记或未知；不为查看资源而运行 `start`、`stop`、`discover` 或 `run`。保存状态摘要和核对时间即可，不把其他实例的清单当本项目资源。

资源范围已知时，在目标 launcher 查询状态并使用逐卡入口；以下节点和卡号只是语法示例，按当前清单及项目授权替换：

```bash
/mmu_vlm_hdd/home/rhsu/idle-job-can-kill-anytime/idle-job status
/mmu_vlm_hdd/home/rhsu/idle-job-can-kill-anytime/idle-job run --gpus worker-0:0,1 -- bash /path/to/project-task.sh
```

`run --gpus` 在 CPU 数据准备之前预约选定卡，只清理这些卡的占卡子进程、确认显存与进程释放，再执行已验证的项目 conda 前台命令。多节点可重复 `--gpus`；不同卡的独立任务各自包装，允许并行、拒绝重叠预约，任务结束只解除自己的预约。保持本实例原有监测启用状态，某任务先结束时，它释放的卡自动补位，其他任务与未选中卡继续运行。

`--gpus` 是预约声明，不负责派发远端命令或设置 GPU 绑定；项目脚本用 `CUDA_VISIBLE_DEVICES` / 框架资源映射确保只使用预约卡。选定卡仍有真实作业时不能抢占或删除其预约，改选项目允许的空闲资源。占卡程序自身解释器不替代项目 conda 环境。不要把结束时间不同的独立任务包在一个一直持有全批次预约的 wrapper 中。

整实例任务或资源范围不明时，兼容入口 `run --` 仍预约全部卡。无法让 wrapper 等待所有前台、后台及远端 GPU 作业结束时，先 `stop` 并保持暂停；停止后核对全部节点的本程序进程为零、显存释放。`stop` 是整实例持续暂停，不能作为逐卡任务的默认步骤。真实训练、推理和其他用户作业必须保留；剩余资源仍按项目权限、峰值和余量准入。程序缺失记“未部署”，不额外部署占卡；身份或连接失败不能声称已释放。

不要依赖“看见 CUDA 进程再自动退出”：CPU 数据准备没有 CUDA 上下文，仍有启动竞态。直接杀单个子进程可能被守护重启。手动暂停后，只有核实本次全部真实 GPU 作业已结束且先前此实例确在启用占卡，才恢复 `start`；逐卡 `run` 正常结束后自动解除自己的预约，无需暂停或重启其他卡。`run` 被 SIGKILL 后可能保留预约，先查真实作业与当前实例对应预约，再处理，不能清空其他任务或其他实例状态。旧版未记录卡范围的预约仍保护整实例。`--local` 仅管理本容器，各操作须保持该模式一致。

程序会拒绝不匹配的容器/GPU 身份，发现异常时读错误和现有清单，重新核对实例，不跳过验证。默认小显存负载及时间占空比以实际配置为准，不把占卡利用率当实验吞吐，也不保证其满足平台回收阈值。

### 多节点作业启动

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
