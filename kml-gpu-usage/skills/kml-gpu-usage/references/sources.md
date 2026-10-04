# 文献、官方文档和社区线索

整理基于 2026-10-04 调研。论文/benchmark 的数字只代表其模型、版本和机器条件；发布过的社区问题不说明今天所有版本仍有同一缺陷。选择新实现、引用“最新”支持或复用网络 recipe 时，先核对执行日期、安装版本和官方材料；页面变化/重定向/不可访问时区分已证实和待核实。

## 精度、算子与编译

- [PyTorch SDPA](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html)：自动选择融合后端、输入限制、数值差异及后端控制。接口名字不等于实际 kernel。
- [FlashAttention 官方仓库](https://github.com/Dao-AILab/flash-attention)；[2026-09-22 README 快照](https://github.com/Dao-AILab/flash-attention/blob/9c6d9297e5d43653c2ea5837ed9e0d10f76ed231/README.md)：FA3/FA4 的硬件、dtype、安装与接口。调研快照中 FA4 已支持 Hopper/H100 与 Blackwell。
- [FlashAttention-3，2024 作者文章和论文入口](https://pytorch.org/blog/flashattention-3/)：Hopper WGMMA/TMA/异步重叠和 attention benchmark。1.5–2× 等 kernel 收益不是整段训练收益。
- [Transformer Engine FP8/FP4 primer](https://docs.nvidia.com/deeplearning/transformer-engine/examples/fp8_primer.html) 与 [官方仓库](https://github.com/NVIDIA/TransformerEngine)：FP8 格式、scaling recipe、数值和硬件适用范围。
- [PyTorch Performance Tuning Guide](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html)：loader、NUMA、混合精度、融合、同步、accumulation 和 rank 负载均衡。
- [FSDP + torch.compile 吞吐报告，2024](https://pytorch.org/blog/maximizing-training-throughput/)：特定 Llama2/集群配置的 MFU 和数值检查；不能推广为每个 KML 模型的预期收益。

## 显存与分布式

- [ZeRO，2019/2020](https://arxiv.org/abs/1910.02054)：optimizer、梯度与参数状态的分片动机。
- [PyTorch Activation Checkpointing Techniques，2025](https://pytorch.org/blog/activation-checkpointing-techniques/)：激活重算、选择性重算和速度/显存权衡。
- [FSDP2 tutorial](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html)：fully_shard、粒度、prefetch、混合精度、HSDP mesh 和 checkpoint。
- [Megatron-LM 大规模 GPU 训练，2021](https://arxiv.org/abs/2104.04473)：多维并行、拓扑和 pipeline 调度。
- [TorchTitan 长上下文社区讨论，2025](https://discuss.pytorch.org/t/distributed-w-torchtitan-breaking-barriers-training-long-context-llms-with-1m-sequence-length-in-pytorch-using-context-parallel/215082)：CP/通信重叠/负载均衡与 compile 的组合结果；存在部分长序列配置 compile 后吞吐下降的历史案例。

## 网络、同步和排障

- [NCCL 排障入口](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting.html)、[环境变量](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html)：版本相关参数说明。
- [NCCL 网络排障](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/networking_troubleshooting.html)：IP 接口、IB/RoCE、GID 与网络验证。
- [NCCL GPU/GPUDirect 排障](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/gpu_troubleshooting.html)：P2P、GDR、nvidia-peermem/DMA-BUF 和容器拓扑。
- [NVIDIA nccl-tests issue #290，2025](https://github.com/NVIDIA/nccl-tests/issues/290)：H100 单节点/多节点、UCX 与 NCCL 配置区别、日志和带宽。诊断变量的使用条件不能抹掉。
- [PyTorch 社区 `.item()` 与 CUDA 异步计时，2022](https://discuss.pytorch.org/t/loss-item-causes-the-wrong-time-consumption/157912)：同步会改变耗时归因，正确计时必须等待实际 CUDA 完成。

先用项目的实测 snapshot/trace 建立事实，再用官方资料解释；社区讨论用于定位和设计对照，不作为本机容量、速度或最优配置的证明。
