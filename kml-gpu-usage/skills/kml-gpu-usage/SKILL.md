---
name: kml-gpu-usage
description: "KML 机器 GPU 使用：核对多节点 H100 资源，部署、调度并优化训练或推理吞吐。当用户调用 $kml-gpu-usage、要求 KML GPU 使用/提速/排障，或模型在已有 KML 项目中准备启动、修改 GPU 作业和并行配置时使用。适用于每节点八卡、共享挂载盘、节点数随记录变化的环境；不用于仅配置 SSH 或讨论无关平台的通用 GPU 原理。"
---

# KML 机器 GPU 使用

帮助用户在 KML 的每节点 8×H100、多节点、共享挂载盘环境中完成 GPU 部署、资源安排、吞吐优化和排障。总节点数由本次训练记录确定。衡量固定训练目标下的有效吞吐、wall time 和 GPU-hours，保证优化保持模型、数据和评测语义。

## 触发与任务范围

- 用户可以显式调用 `$kml-gpu-usage`，或说“使用 KML 机器 GPU 使用 skill”。Claude 插件调用名为 `/kml-gpu-usage:kml-gpu-usage`。
- 模型可以在 KML GPU 作业部署、调度、训练代码/并行配置优化、GPU/通信/IO 排障时主动应用；自动发现依赖 Agent 把该目录加载为 skill。
- 调研或写计划时交付建议与拟执行配置；用户要求实施时，继续完成范围内的准备、修改、短验证和运行，不重复索取已有授权。skill 触发本身不授权启动额外训练、大额下载或占用额外节点。
- SSH 别名、训练 record、worker 清单、允许使用的节点/卡和项目存储根从当前项目文档、用户指令与实测获取。缺少访问方式时先推进代码/配置分析，再询问真正缺失的信息。

## 开始工作

1. 明确这次是资源核对、部署、提速、排障还是执行作业；识别模型、训练/推理框架、精度、输入长度/分辨率/帧数、有效 batch/token 预算和现有性能基线。
2. 读取适用的项目约定；用当前日期和时区给检查结果标记时间。平台记录、节点端口、软件版本、可用显存和 attention 支持均可能变化，不能从旧 session 或截图直接断言当前状态。
3. 按需阅读下列参考；不要一次加载全部材料。
   - 部署、资源安排、共享盘与作业生命周期：[references/deployment.md](references/deployment.md)。
   - 精度、算子、编译、microbatch、分片和吞吐验证：[references/performance.md](references/performance.md)。
   - 多节点扩展变慢、NCCL/RDMA/Fabric 问题：[references/networking.md](references/networking.md)。
   - 需要引用文献、选择新后端/版本或核实社区建议：[references/sources.md](references/sources.md)，按任务刷新官方资料。

## 资源核对与准入

- 检查本次允许的节点；hostfile 是分配清单，单节点 `nvidia-smi` 只描述本节点，不证明全记录健康或空闲。明确 launcher 是否有 GPU、是否参与计算。
- 可在每个目标节点用实际项目 Python 执行 [scripts/node_snapshot.py](scripts/node_snapshot.py)。它仅查询资源和当前解释器的包元数据，不导入 torch、不初始化 CUDA、不运行 benchmark、不修改配置；输出保存在项目运行目录。检查失败的字段按 unknown 处理。
- 核对每节点 GPU UUID、空闲显存、Fabric、GPU/NIC/NUMA 拓扑、RDMA link layer、容器 CPU/RAM 配额、共享挂载和实际项目环境。随后按执行任务需要做 CUDA/通信 correctness smoke；资源快照不代替它们。
- 已允许资源中，实时空闲显存能容纳新增任务峰值与必要余量时可以共享 GPU，不要求整卡或整节点空闲。没有测过峰值时先保守估算并做短 profile；还要评估共驻对算力、IO 和通信的影响。
- 保持其他作业；只管理本作业进程。容器 PID 与 NVML 驱动 PID 可能不同，不直接用 `nvidia-smi` 的 PID 做 kill。Fabric/驱动/宿主网络问题交给平台处理。

## 用证据选择优化

- 先判断计算、CPU/kernel launch、数据供给、显存还是通信受限，再选择参考中的对应措施。建立单卡/最小可运行组、单节点八卡和所需多节点的基线；模型装不进单节点时不强求单节点训练。
- BF16 是 H100 的常用起点；FP8、compile、融合算子属于需验证的候选。检查实际 kernel，不能按 `sdpa`/`flash_attention` 的配置名断言速度或可用性。
- 按显存组成选择 DDP、ZeRO/FSDP、HSDP、TP/PP/CP 与选择性激活重算；不把分片和 checkpointing 当作互斥方案。高频通信组优先留在节点内，复杂并行须由框架正确配置通信组。
- 共享挂载盘不保证高并发 IO：关注小文件、解码、重复扫描、每 rank 的 loader/线程数量、预处理和编译缓存争用。
- 所有优化保持 attention/loss mask、position IDs、数据增强、token 预算、梯度归一化和评测契约。不要用减少难样本、截断轨迹或改变目标伪装提速。
- 节点数增加不保证成本更低；比较整个实验矩阵的完成时间，必要时把资源用于独立 seed、消融、评测或数据分片。

## 验证、恢复与交付

先做代表性 correctness smoke，再做短性能窗口；一次改变一个关键因素。覆盖最长输入、optimizer step、通信/编译缓冲与评估切换的显存峰值。仅短窗口启用 profiler，正式测量不保留 debug 同步与逐步 barrier。

记录有效非 padding token/s 或 sample/s、SFT 监督 token/s、step p50/p95、数据等待、慢 rank、未被计算遮住的通信、峰值显存和真实分配的 GPU-hours。RL/Agentic 任务另报有效 episode/hour、工具/环境等待、rollout、actor 更新和权重同步；推理任务按用户目标比较吞吐、延迟及 KV 容量。

比较固定总工作量的强扩展与固定每卡工作量的弱扩展时分别标明口径；DP degree 不等于含 TP/PP/CP 的总 GPU 数。测量窗口包含必要的 CUDA 完成等待，不能只计 CPU 提交时间。最终比较包含冷启动、checkpoint、验证与恢复的 wall time，核对 loss/梯度或对应质量指标。

交付与任务规模相称的结果：已核实的资源和时间、实际瓶颈与依据、配置/代码改动、前后吞吐和成本、数值/质量检查、可恢复产物、未验证项和下一步。区分估算、论文/社区结果、现场测量、拟执行与已执行动作，不承诺未经测量的倍数收益。
