# KML 多节点通信与 GPU 排障

## 三层证据

1. **设备与拓扑**：每节点 `nvidia-smi topo -m`、Fabric、RDMA 设备、端口 state/rate/link_layer、GPU/NIC/NUMA 映射、容器可见 `/sys` 和 `/dev/infiniband`、共享内存/memlock/CPU 限制。
2. **实际 transport**：短探针用 `NCCL_DEBUG=INFO`，必要时 `NCCL_DEBUG_SUBSYS=INIT,NET,GRAPH`；检查网络插件、HCA 与 GPU 映射，区分 RDMA、Socket fallback 和正常 TCP bootstrap。
3. **通信与训练性能**：在已准入资源上测单节点及跨节点 collective，覆盖真实消息/bucket 大小；再检查训练中 all-reduce/all-gather/reduce-scatter 与计算重叠，不能只引用链路速率。

若用户只要求分析，给拟执行的探针与判断标准；用户要求部署/修复时，执行所需的短验证，避免展开成无关大规模 benchmark。

## 最容易照抄错的配置

| 项目 | 判断方式 |
|---|---|
| `/sys/class/infiniband` 有设备 | 不说明物理网络是 IB；看 port `link_layer`，Ethernet 对应 RoCE 方向继续核实。 |
| `mlx5_0` / `eth0` | 编号和端口速率可能逐节点不同，不能硬编码整个记录同一清单。保留自动选择基线。 |
| `NCCL_SOCKET_IFNAME` | 选择 IP/socket 接口，不能代替选择 RDMA HCA。 |
| `NCCL_IB_HCA` | 选择 RDMA HCA，变量名字虽然含 IB，也用于 RoCE；只有发现错误选择后按逐节点映射干预。 |
| `UCX_NET_DEVICES` | 属于 MPI/UCX 方向，不等同于 NCCL HCA 配置。 |
| 没有 `nvidia-peermem` | 某些内核/驱动栈可用 DMA-BUF，不能单凭模块缺失判定 GDR 不可用。 |
| `NCCL_IB_GID_INDEX` | 旧 RoCE recipe 不可直接套新版；核对安装的 NCCL，官方文档指出 2.21 及以后不应设置该旧式变量。 |
| `NCCL_IB_DISABLE=1`、禁用 P2P、固定算法 | 通常是诊断或对照，不是通用性能优化；改后重新测量并恢复合适基线。 |

看到 400Gb/s 等速率只能说明设备报告的链路能力，约 50GB/s 线速不等于模型吞吐；多轨聚合、拓扑、拥塞、消息大小、协议和 collective 算法均影响结果。`nccl-tests` 的 algbw/busbw 是 collective 指标，busbw 不是单条物理链路的直接测量。

## 按症状推进

| 症状 | 下一步 |
|---|---|
| CUDA Error 802 / Fabric 未完成 | 确认 GPU 枚举、Fabric state/status 与实际 CUDA 错误；作为节点基础设施问题记录，使用允许范围内的健康节点或交平台修复。 |
| 单节点好、跨节点慢 | 看 NCCL 选 HCA/transport，RDMA/GDR、端口速率、多轨、容器可见性，再测跨节点真实消息大小。 |
| NCCL init hang / timeout | 查内部 rendezvous 可达性、rank/world size、端口、接口、各 rank 是否执行同样的 collective；不能把所有 timeout 都归因于网络。 |
| 小消息特别差 | 启动/延迟、collective 数量、FSDP 分片过细、CPU 排队；不要仅追求大消息峰值带宽。 |
| 某 rank 长时间落后 | 数据长度/解码、CPU quota/NUMA、其他任务干扰、PP stage、MoE 路由不均；训练同步会等待最慢 rank。 |
| compile 后扩展变差 | 分别检查 graph breaks、重复编译、峰值与 compute/comm overlap，比较 eager/区域 compile 对照。 |

节点内高频通信优先放 NVLink 域，前提是本次拓扑和健康检查支持；不要假设每一条 KML 记录都是同样的 NVSwitch、RDMA 端口数或网络带宽。PP、CP、MoE/EP 的通信模式不同，不能只测 all-reduce 就证明全部路径最佳。

Fabric Manager、驱动、宿主 ACS/IOMMU、网络拥塞/配置属于平台层。不要在容器里重装驱动、修改 PCI 寄存器或复制网上脚本改宿主配置。只清理本作业拥有的进程，不能用 NVML PID 直接当容器 PID。

参考官方 NCCL 文档及 NVIDIA nccl-tests issue #290，见 [sources.md](sources.md)。社区变量用于生成待验证的假设，一次改一个因素；不要把他人的一组环境变量当本次记录的最优解。
