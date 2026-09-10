# Skills

Personal skills collection for Claude and Codex.

## Claude marketplace

在 Claude Desktop / Claude Code 中导入这个仓库作为 marketplace：

- GitHub 仓库：`MichaelSou1/skills`
- 或：`/plugin marketplace add MichaelSou1/skills`

识别所需的清单文件在 `.claude-plugin/marketplace.json`。导入后可安装 `paper-reading`、`unpack` 和 `professor-research`。

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
