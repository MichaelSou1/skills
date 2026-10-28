# Skills

Personal skills collection for Claude and Codex.

## Claude marketplace

在 Claude Desktop / Claude Code 中导入这个仓库作为 marketplace：

- GitHub 仓库：`MichaelSou1/skills`
- 或：`/plugin marketplace add MichaelSou1/skills`

识别所需的清单文件在 `.claude-plugin/marketplace.json`。导入后可安装 `paper-archive`、`paper-reading`、`unpack`、`professor-research`、`write-experiment-plan`、`kml-gpu-usage`、`open-workspace`、`kml-ssh-proxy` 和 `gpt-progressive-research`。

## paper-reading（论文精读）

用大同行的口吻分段精读 CS/AI/ML 论文，先讲动机，再讲方法、实验和局限。

仅允许用户手动调用（`$paper-reading`、`/paper-reading`、技能选择器或明确要求使用此技能）；大模型不得自行触发。Codex 调用策略已设置 `allow_implicit_invocation: false`。

- 公式里的字母首次出现时，说明它在当前公式中的具体意义。
- 讲解方法时尽量用具体例子走通输入、关键操作和输出，区分原文例子与教学简化。
- 优先在对应讲解处呈递清晰、可追溯的论文原图或子图，并在适合的机制处补充图示或交互演示。
- 作者公开数据或论文展示数据时，主动在对应环节展示可追溯的真实样例，说明字段作用、数据处理前后变化和样例来源。
- 结合公开代码、配置与附录，用具体样例和图示讲清数据构造、训练设计及评测判分，区分论文描述、代码实现与教学简化。
- 维护论文阅读主线；回答中途插入的表格、公式或实现细节后，主动说明当前阅读位置并接回尚未讲完的章节，除非用户明确继续深挖该细节。
- 主入口：[SKILL.md](paper-reading/skills/paper-reading/SKILL.md)。Codex 可用 `$skill-installer` 安装此子路径；Claude 可用 `/plugin install paper-reading@michaelsou-skills` 安装。
- 独立包：[paper-reading 1.2.2 ZIP](https://github.com/MichaelSou1/skills/releases/download/paper-reading-v1.2.2/paper-reading-1.2.2.zip)，校验文件位于同一 Release。ZIP 根目录为 `paper-reading/`，直接包含 `SKILL.md`。

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

仅用户手动调用，将具体机器学习实验想法整理为可接手实施的实验计划：

- 按需联网核实训练/验证/测试数据集、模型版本和下载入口。
- 根据实时空闲显存、任务峰值与必要余量安排 GPU，尽量提高并行度，支持同卡插入任务。
- 明确代码模块、输入输出、配置、实施依赖与验收方式。
- 设计基线、消融、阶段步骤、结果分析和停止条件。

Codex 和 Claude Code 均禁止模型自动触发本技能。写计划本身不自动启动长时实验；支持按请求继续实施。

### Claude Code

添加上面的 marketplace 后安装：

```text
/plugin install write-experiment-plan@michaelsou-skills
```

手动调用：

```text
/write-experiment-plan:write-experiment-plan 实验想法：…… 项目位置：…… 可用资源：……
```

### Codex

调用 `$skill-installer`，指定仓库 `MichaelSou1/skills` 和技能子路径 `write-experiment-plan/skills/write-experiment-plan`。安装后仅能由用户手动调用：

```text
$write-experiment-plan
实验想法：……
项目位置：……
可用资源：……
```

Claude Code 的调用策略位于 `SKILL.md` 的 `disable-model-invocation: true`；Codex 的调用策略位于 `agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`。普通的“写实验计划”请求不会自动触发本技能。


## kml-gpu-usage（KML 机器 GPU 使用）

适用于每节点八张 H100、多节点、共享挂载盘的 KML 作业；节点数、地址、网卡和软件版本由每次训练记录核对。帮助 Agent 完成 GPU 资源准入、部署、训练/推理吞吐优化与 NCCL/IO 排障，并验证训练语义、真实成本和恢复能力。

- 主入口：[SKILL.md](kml-gpu-usage/skills/kml-gpu-usage/SKILL.md)。
- 按需参考：部署与共享盘、精度/算子/并行、NCCL/网络、官方文档/论文/社区来源。
- 只读脚本 `scripts/node_snapshot.py` 在目标 Linux 节点采集资源与当前解释器元数据，不导入 torch、不初始化 CUDA、不运行 benchmark。
- 支持用户显式调用和模型按 KML GPU 任务自动匹配。调用 skill 本身不授权额外训练或资源消耗；已有任务授权按上下文继续。
- 共享占卡程序 `idle-job-can-kill-anytime` 逐卡调度。GPU 任务优先使用 `run --gpus NODE:0,1 -- ...`，每项独立任务预约并释放自己的卡；某些卡先结束且没有后续任务时，立即启动占卡补位，不等待整批结束。监测已启用则自动补位，未启用或暂停则保护其余任务预约后 `start`，无需再次确认；保留整实例 `stop` / `run --`，保护真实作业与其他实例。

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

已发布独立包（1.0.0，不含逐卡预约更新）：下载 [kml-gpu-usage 1.0.0 ZIP](https://github.com/MichaelSou1/skills/releases/download/kml-gpu-usage-v1.0.0/kml-gpu-usage-1.0.0.zip) 和同一 Release 中的 SHA256 文件。ZIP 根目录是 `kml-gpu-usage/`，直接包含 `SKILL.md`、`agents/`、`references/` 和 `scripts/`，不要求 Claude 插件系统。

将整个目录放入目标 Agent 的 skill 发现路径；保留相对目录结构。用户显式调用与模型自动选择的入口取决于该 Agent 的 skill 加载机制。该包不包含运行记录的固定节点/IP/SSH 密钥、资源快照或私有模型数据。


## open-workspace（开辟新工作区）

仅用户手动调用，为论文复现或新研究想法建立本机工作区、通用 `AGENTS.md` 与私有 GitHub 仓库。生成的 `AGENTS.md` 要求每个可验收工作包通过必要检查后，及时、自主提交并推送 GitHub；指定远端服务器时同时同步服务器，不等待用户另行提醒。它还明确要求用 conda 管理项目环境依赖；GPU 服务器空间足够时，每次训练与评测必须持久化保留所有可保存的信息，包括完整 rollout 和 judge 评分详情（若有）。指定远端服务器时，部署仓库、探查实际 GPU/worker 资源、配置该仓库专属的读写 deploy key，并核对本机、GitHub 与服务器同步。KML 采用共享盘项目路径，GPU 使用交由 `kml-gpu-usage`。远端为 KML 时，新 AGENTS 会记录共享占卡路径、本实例状态、停止与补位启动授权，以及逐卡预约、每项独立任务各自释放、先结束且无后续任务的卡立即占卡补位的流程，不等待整批结束；工作区初始化仅查询已有状态。

- 主入口：[SKILL.md](open-workspace/skills/open-workspace/SKILL.md)。
- Codex 安装路径：`open-workspace/skills/open-workspace`；安装后手动调用 `$open-workspace`。
- Claude：`/plugin install open-workspace@michaelsou-skills`，然后手动调用 `/open-workspace:open-workspace`。
- 两端禁止模型自动调用：Codex `policy.allow_implicit_invocation: false`；Claude `disable-model-invocation: true`。
- 仓库版本：1.0.10，新增 KML 新工作区 AGENTS 的国内代理、海外代理和取消代理命令；保留自主同步、GPU/API 自主使用授权，以及长任务后台等待与定时轮询规则。
- 独立包：[open-workspace 1.0.10 ZIP](https://github.com/MichaelSou1/skills/releases/download/open-workspace-v1.0.10/open-workspace-1.0.10.zip)，同一 Release 提供 SHA256。ZIP 根目录为 `open-workspace/`，直接包含 `SKILL.md`、`agents/`、`assets/` 和 `references/`。包含自主 GitHub/服务器同步、GPU/API 自主使用授权，以及长任务（GPU 训练与评测、数据采集等）后台等待时的定时轮询要求：优先用 harness 循环定时任务，无则 `sleep` 后唤醒。

调用示例：

```text
$open-workspace
为刚讨论的论文复现建立工作区，项目名 my-reproduction。
远端服务器：ssh my-server。
```

省略服务器时只建立本机与 GitHub 两端；本技能不因讨论论文或 idea 自行触发，也不在开工作区时自动安装训练环境、下载数据或启动实验。


## paper-archive（论文归档）

仅由用户手动调用，将论文阅读讨论整理为 Notion 笔记：基础信息、按论文类型组织的主线、takeaways、个人追问与简答。尽量嵌入原论文方法图和案例截图，默认跳过实验数据图表，不添加“证据与回看入口”尾节。

- 仅依赖 Notion MCP，不要求 Codex、Notion 插件或 paper-reading；按宿主实际能力处理截图和上传。
- 主入口：[SKILL.md](paper-archive/skills/paper-archive/SKILL.md)。
- Codex：通过 `$skill-installer` 安装仓库 `MichaelSou1/skills` 中的 `paper-archive/skills/paper-archive`，手动调用 `$paper-archive`。
- Claude：`/plugin install paper-archive@michaelsou-skills`，手动调用 `/paper-archive:paper-archive`。
- Claude 设置 `disable-model-invocation: true`；Codex 设置 `policy.allow_implicit_invocation: false`；其他宿主遵守技能正文中的显式调用限制。
- 独立包：[paper-archive 1.0.0 ZIP](https://github.com/MichaelSou1/skills/releases/download/paper-archive-v1.0.0/paper-archive-1.0.0.zip)，同一 Release 提供 SHA256。ZIP 根目录为 `paper-archive/`，直接包含 `SKILL.md`、`agents/` 和 `references/`，可放入其他 Agent 的技能目录。

调用示例：`$paper-archive 将这次论文精读归档到 Notion`。

## kml-ssh-proxy（KML 免密 SSH 与代理）

已有别名优先直接连接，成功即停止检查；仅连接失败、别名缺失、目标绑定冲突或明确要求新建/重新配置时，进入对应流程。局部修复只验收受影响部分，避免重复核验和扩大范围。

- 主入口：[SKILL.md](kml-ssh-proxy/skills/kml-ssh-proxy/SKILL.md)。
- Codex 安装路径：`kml-ssh-proxy/skills/kml-ssh-proxy`。
- Claude：`/plugin install kml-ssh-proxy@michaelsou-skills`。
- 配置流程依赖本机已有的 `kml-remote-helper` 与企业 SSO；本仓库不包含该 helper。

- KML 代理默认排除 `internal,.internal`，同步 `no_proxy` 与 `NO_PROXY`；保留原有排除项，并提供 curl 直连对照验证。
- 独立包：[kml-ssh-proxy 1.0.1 ZIP](https://github.com/MichaelSou1/skills/releases/download/kml-ssh-proxy-v1.0.1/kml-ssh-proxy-1.0.1.zip)，同一 Release 提供 SHA256。


## gpt-progressive-research（渐进式与建设性科研推进）

用于克服大模型在科研辅助中常见的四大顽疾：因相似工作而过度防御否定、仅凭表面相似断定创新性不足、在构思期过度纠结细枝末节，以及只反复挑刺而不给低成本推进方案。

- **拓展 idea 的思路**：聚焦明确的新增价值与演进空间，拒绝因已有相似工作就提前泼冷水否定。
- **检查 idea 的创新性**：穿透调研近邻工作机制与局限，提炼有说服力的差异表述与验证方案；若核心高度重合则明确指出重合点与差异化调整方向，不强行造新。
- **避免过度纠结细枝末节**：按研究阶段（构思期 vs 落地方案期）与问题重要性（致命伤 vs 局部参数/边缘情况）合理分配分析深度。
- **从反复质疑转向建设性解决问题**：区分根本性缺陷与局部不足，遵循“最小改动原则”提供可执行改进方案，禁止对已解决的问题翻旧账，每轮收敛出核心待解问题与下一步工作。
- 主入口：[SKILL.md](gpt-progressive-research/skills/gpt-progressive-research/SKILL.md)。支持用户显式调用与模型在科研讨论中自动匹配。
- 独立包：[gpt-progressive-research 1.0.0 ZIP](https://github.com/MichaelSou1/skills/releases/download/gpt-progressive-research-v1.0.0/gpt-progressive-research-1.0.0.zip)，同一 Release 提供 SHA256。ZIP 根目录为 `gpt-progressive-research/`，直接包含 `SKILL.md` 和 `agents/`，可放入其他 Agent 的技能目录。

### Claude Code

```text
/plugin marketplace add MichaelSou1/skills
/plugin install gpt-progressive-research@michaelsou-skills
/gpt-progressive-research:gpt-progressive-research
```

### Codex

调用 `$skill-installer`，指定仓库 `MichaelSou1/skills`、技能子路径 `gpt-progressive-research/skills/gpt-progressive-research`。安装后可使用 `$gpt-progressive-research` 显式调用，或在讨论科研 idea 时自动触发。
