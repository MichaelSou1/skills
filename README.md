# Skills

Personal skills collection for Claude and Codex.

## Claude marketplace

在 Claude Desktop / Claude Code 中导入这个仓库作为 marketplace：

- GitHub 仓库：`MichaelSou1/skills`
- 或：`/plugin marketplace add MichaelSou1/skills`

识别所需的清单文件在 `.claude-plugin/marketplace.json`。导入后可安装 `paper-reading`、`unpack`、`professor-research`、`write-experiment-plan` 和 `kml-gpu-usage`。

## paper-reading（论文精读）

用大同行的口吻分段精读 CS/AI/ML 论文，先讲动机，再讲方法、实验和局限。

- 公式里的字母首次出现时，说明它在当前公式中的具体意义。
- 讲解方法时尽量用具体例子走通输入、关键操作和输出，区分原文例子与教学简化。
- 在适合的机制处穿插图示或交互演示。
- 作者公开数据或论文展示数据时，主动在对应环节展示可追溯的真实样例，说明字段作用、数据处理前后变化和样例来源。
- 结合公开代码、配置与附录，用具体样例和图示讲清数据构造、训练设计及评测判分，区分论文描述、代码实现与教学简化。
- 主入口：[SKILL.md](paper-reading/skills/paper-reading/SKILL.md)。Codex 可用 `$skill-installer` 安装此子路径；Claude 可用 `/plugin install paper-reading@michaelsou-skills` 安装。
- 独立包：[paper-reading 1.2.0 ZIP](https://github.com/MichaelSou1/skills/releases/download/paper-reading-v1.2.0/paper-reading-1.2.0.zip)，校验文件位于同一 Release。ZIP 根目录为 `paper-reading/`，直接包含 `SKILL.md`。

## professor-research

给一个老师相关链接（个人主页、院系介绍、Google Scholar 或论文页），调研近年来的研究方向，并逐篇用两三句话介绍 Scholar 上今年的工作。

- 梳理研究主线的演进及代表论文。
- 展开完整 Scholar 列表，去重并补查年份缺失的条目。
- 核对摘要和来源，区分首次公开、正式发表、录用及预印本状态。
- “今年”按执行日期确定，也可指定年份。

### Claude Code

添加上面的 marketplace 后安装：

```text
/plugin install professor-research@michaelsou-skills
```

手动调用并附上链接：

```text
/professor-research:professor-research <老师相关链接>
```

### Codex

调用 `$skill-installer`，指定仓库 `MichaelSou1/skills` 和技能子路径 `professor-research/skills/professor-research`，然后手动调用：

```text
$professor-research <老师相关链接>
```

Claude Code 的手动触发设置位于 `SKILL.md` 的 `disable-model-invocation: true`；Codex 的设置位于 `agents/openai.yaml` 的 `allow_implicit_invocation: false`。

## unpack

把黑话展开成人话。当大模型的解释太抽象凝练、术语堆砌、跳步推理时，用这个 skill 让它展开说。

适用场景：调用 `/unpack` 或者说"说人话""解释一下""展开讲讲"。

### 安装

在 Claude Code 中：

```
/install-skill https://github.com/MichaelSou1/skills/tree/main/unpack
```


## write-experiment-plan（写实验计划）

将具体机器学习实验想法整理为可接手实施的实验计划：

- 按需联网核实训练/验证/测试数据集、模型版本和下载入口。
- 根据实时空闲显存、任务峰值与必要余量安排 GPU，尽量提高并行度，支持同卡插入任务。
- 明确代码模块、输入输出、配置、实施依赖与验收方式。
- 设计基线、消融、阶段步骤、结果分析和停止条件。

写计划本身不自动启动长时实验；支持按请求继续实施。

### Claude Code

添加上面的 marketplace 后安装：

```text
/plugin install write-experiment-plan@michaelsou-skills
```

调用：

```text
/write-experiment-plan:write-experiment-plan 实验想法：…… 项目位置：…… 可用资源：……
```

### Codex

调用 `$skill-installer`，指定仓库 `MichaelSou1/skills` 和技能子路径 `write-experiment-plan/skills/write-experiment-plan`。安装后可自动匹配实验计划请求，也可显式调用：

```text
$write-experiment-plan
实验想法：……
项目位置：……
可用资源：……
```


## kml-gpu-usage（KML 机器 GPU 使用）

适用于每节点八张 H100、多节点、共享挂载盘的 KML 作业；节点数、地址、网卡和软件版本由每次训练记录核对。帮助 Agent 完成 GPU 资源准入、部署、训练/推理吞吐优化与 NCCL/IO 排障，并验证训练语义、真实成本和恢复能力。

- 主入口：[SKILL.md](kml-gpu-usage/skills/kml-gpu-usage/SKILL.md)。
- 按需参考：部署与共享盘、精度/算子/并行、NCCL/网络、官方文档/论文/社区来源。
- 只读脚本 `scripts/node_snapshot.py` 在目标 Linux 节点采集资源与当前解释器元数据，不导入 torch、不初始化 CUDA、不运行 benchmark。
- 支持用户显式调用和模型按 KML GPU 任务自动匹配。调用 skill 本身不授权额外训练或资源消耗；已有任务授权按上下文继续。

### Claude Code

```text
/plugin marketplace add MichaelSou1/skills
/plugin install kml-gpu-usage@michaelsou-skills
/kml-gpu-usage:kml-gpu-usage 检查本次 KML 资源并优化这个训练作业。
```

保留 Claude 的默认调用策略，未设置 `disable-model-invocation: true` 或 `user-invocable: false`，因此用户与模型均可触发。

### Codex

调用 `$skill-installer`，指定仓库 `MichaelSou1/skills`、技能子路径 `kml-gpu-usage/skills/kml-gpu-usage`。安装后在下一轮使用：

```text
$kml-gpu-usage 检查本次 KML 资源，定位训练瓶颈并实施任务范围内的优化。
```

也可用自然语言提出 KML GPU 部署、调度、提速或排障请求，让模型自动选择。`agents/openai.yaml` 显式设置 `policy.allow_implicit_invocation: true`。

### 其他 Agent / 独立包

下载 [kml-gpu-usage 1.0.0 ZIP](https://github.com/MichaelSou1/skills/releases/download/kml-gpu-usage-v1.0.0/kml-gpu-usage-1.0.0.zip) 和同一 Release 中的 SHA256 文件。ZIP 根目录是 `kml-gpu-usage/`，直接包含 `SKILL.md`、`agents/`、`references/` 和 `scripts/`，不要求 Claude 插件系统。

将整个目录放入目标 Agent 的 skill 发现路径；保留相对目录结构。用户显式调用与模型自动选择的入口取决于该 Agent 的 skill 加载机制。该包不包含运行记录的固定节点/IP/SSH 密钥、资源快照或私有模型数据。
