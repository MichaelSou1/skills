# H100 训练效率：按瓶颈选措施

## 先分类再优化

| 观察 | 优先检查与候选措施 |
|---|---|
| GPU 间歇空闲、loader 等待高 | 解码/预处理、共享盘小文件、数据分片、worker/线程、prefetch、CPU quota/NUMA、H2D。 |
| CPU 忙、很多很短 kernel | 同步 `.item()`/`.cpu()`、Python 循环、graph breaks、融合算子和区域 compile。 |
| GEMM/attention 占主要时间 | BF16、实际 Tensor Core/kernel、attention 后端、矩阵形状、microbatch、packing、FP8。 |
| OOM/微批被压得很小 | 分解模型状态/激活/临时缓冲，按来源选择分片、重算、CP/SP、varlen、logits/CE 优化。 |
| 扩展节点后吞吐增长很小 | 网络路径/带宽、FSDP gather、TP group、通信重叠、最慢 rank、PP bubble，阅读 networking.md。 |
| RL GPU 等待工具/环境 | 有效 episode/hour、CPU sandbox 并发/缓存、rollout 队列、actor/rollout 比例、权重同步与 staleness。 |

## 精度、attention 与融合

BF16 autocast 是 H100 常用基线，必要的归约、统计和 optimizer state 使用合适精度。BF16 通常不需要 FP16 的 GradScaler。FP32 GEMM 可评估 TF32；FP8 通过框架/Transformer Engine 支持的 scaling recipe 评估，不直接把所有 tensor 转成 FP8。检查 loss、梯度、溢出/NaN 和验证质量，H100 支持某种 dtype 不保证某个模型提速或稳定。

SDPA 是接口，会选择融合 kernel，不能视为朴素 attention。检查 profiler 中实际实现和 fallback 原因；比较适配模型的 FA2/FA3/FA4/cuDNN 等路径，测训练 forward **与 backward**。核对 head dim、dtype、causal/任意 mask、GQA、dropout、varlen、滑窗和布局。安装包、模型配置字符串、forward 可运行，都不代替上述证据。

2026-10-04 调研时 FA4 官方 README 已列出 Hopper/H100 与 Blackwell 支持；FA3 条目仍为 beta，FP16/BF16 forward/backward、FP8 forward。该历史快照仅作为线索，选择版本时刷新官方仓库和兼容性，不能用 FP8 forward benchmark 代替 FP8 完整训练收益。

除 attention 外，检查 fused/foreach optimizer、RMSNorm/LayerNorm、MLP、RoPE 和大词表 logits/cross-entropy；采用训练框架支持的实现，保持数值和模型语义。

## microbatch、长度与负载均衡

在代表性的最长输入上测峰值后增加每卡 microbatch。gradient accumulation 维持有效 batch，但过小 microbatch 仍可能吃不满 H100。纯 DP 的 global batch 为 `microbatch × DP degree × accumulation`；TP/PP/CP 下 DP degree 不等于总 GPU 数。

长度、分辨率、帧数/视觉 token 分桶，rank 间按计算量均衡。varlen/packing 减少 padding，但保留样本隔离、position IDs、attention/loss mask。不同 rank 有效 token 数不同，检查全局 loss 归一化，不能直接平均每个 rank 的局部均值。

microbatch 峰值覆盖 optimizer step、通信、CUDA Graph/compile、评估切换和 checkpoint staging。冻结编码器可缓存确定性表征；训练中的编码器、变化的增强或不一致 VAE 版本不能复用过期结果。

## 显存与并行选择

| 条件 | 优先比较 |
|---|---|
| 完整训练状态和有用微批放得下 | DDP；不要为“高级”而增加 gather。 |
| optimizer/梯度状态大 | ZeRO-1/2 或对应状态分片。 |
| 参数、梯度、optimizer 都大 | FSDP2/ZeRO-3，调分片粒度、prefetch、reshard。 |
| 节点内分片足够，继续跨节点扩展 | HSDP/分层分片，把频繁 gather 留在节点内。 |
| 激活/长上下文/多帧大 | Flash/varlen、选择性 activation checkpointing；必要时 CP/SP。 |
| 需要多维模型并行 | TP/PP/CP 与 DP/FSDP；高频通信 group 尽量节点内，检查 PP stage/microbatch/bubble。 |

参数、梯度、optimizer 与激活是不同显存来源；FSDP/ZeRO 与 activation checkpointing 可以组合。重算有计算代价，分片有通信代价，比较最终有效吞吐。Transformer 通常按 block 分片；过粗峰值高、难重叠，过细 hook/collective 多。先采用框架推荐的预取默认值，再按 trace 调整。

DDP accumulation 的前几次 microstep 通常用 `no_sync()`，最后同步，上下文涵盖 forward/backward。FSDP2/ZeRO 使用各自 API，核对无同步时的梯度内存与 reshard 行为。

## compile 与同步

- 优先编译形状较稳定的 block/MLP，查看 `TORCH_LOGS=graph_breaks,recompiles`；长度分桶或区域编译可减少重编译。`dynamic=True` 是否更快需要对照。
- 单独报告编译冷启动、稳定吞吐和完整实验耗时。短作业可能无法摊销编译时间；CUDA Graph/`reduce-overhead`/`max-autotune` 也可能增加显存或破坏通信重叠。
- 不把 IO、日志和工具/网络调用一起编译。核对自定义 kernel 的 compile 支持。
- `.item()`、`.cpu()`、打印 CUDA tensor 和依赖 CUDA 结果的 Python 分支可能同步。先在 GPU 上累计 detached 指标，再低频读取；所有需参与指标 collective 的 rank 都参与，最终 rank 0 写日志。
- 正式性能窗口关闭 anomaly detection、无关 debug、`CUDA_LAUNCH_BLOCKING=1` 和逐步 barrier。`.item()` 的计时可能包含之前排队 kernel 的等待，不能只按调用归因。

## 测量与决策

固定代码/数据/模型版本、训练目标、有效 token/样本预算和可比的干扰条件；先 correctness smoke，再短 profile，一次改一个关键因素，入选组合再完整复测。数值浮点差异不要求逐位一致，按任务核对 loss/梯度趋势与质量。

预热后在完整测量窗口边界适当同步 CUDA，必要时取最慢 rank 耗时，别仅计 CPU enqueue；profiler/Nsight 只采短代表性窗口。记录非 padding token/s、监督 token/s 或 sample/s、step p50/p95、读盘等待、慢 rank、通信暴露时间、allocated/reserved 峰值及真实 GPU-hours。完整 wall time 包括编译、保存、验证和恢复。

弱扩展每卡工作量相同：`E(N) = T(N) / (N × T(1))`。若最小可运行组为 N0 节点，则 `E(N; N0) = T(N) / ((N/N0) × T(N0))`。强扩展固定总工作量；不要把 global batch 增大的吞吐收益当作同一收敛目标的加速。小模型、LoRA、seed/消融应比较单大作业与多独立作业的矩阵完成时间和 GPU-hours。
