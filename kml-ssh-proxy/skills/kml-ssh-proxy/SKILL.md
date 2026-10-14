---
name: kml-ssh-proxy
description: 配置或修复 KML 开发机、训练运行记录及指定 worker 的本机免密 SSH 与登录时自动海外代理。适用于“把这个配成 kml-xxxx”、KML SSH 断连、launcher 到 worker 登录失败；已有别名优先快速复用；新建或重新配置 launcher 时同时配好该记录全部 worker。仅涉及 GPU 作业调度或吞吐优化时不使用。
---

# KML 免密 SSH 与自动代理

优先复用已有 SSH 别名；只有连接失败、目标绑定不符、别名不存在或用户明确要求新建/重新配置时，才进入配置或排障流程。

## 默认入口：已有连接快速复用

- 用户要求使用或切换到已配置的 `kml-xxxx` 时，直接执行一次 `ssh -o BatchMode=yes -o ConnectTimeout=30 kml-xxxx hostname`。已有成功的本次任务 SSH 命令也可作为连接证据，不再单独探测。
- 连接成功即结束本技能的检查，继续用户的实际任务；不强制禁用连接复用，不追加独立或交互式验收。不要求为了确认成功而另查平台记录、Pod、端口、指纹或全部 worker。
- 用户明确给出的记录/实例若与已有绑定冲突，按重新绑定处理；不要以别名可连接覆盖明确的目标要求。没有冲突证据时，不为寻找冲突展开核验。
- 只有任务需要代理时，才在同一次连接中顺带检查代理变量；需要实际网络访问时以该请求结果为准。SSH 成功而代理失败，只修复代理。
- 快速路径不读取 helper 源码或整份 SOP，不运行 `add`、`update-server`、`doctor`，不重写 SSH 或代理配置，不枚举和验收全部 worker。
- 不自行新增项目独立 SSH 通道、指纹审计或修改主机密钥策略。若连接确实报主机密钥冲突，再针对该错误排障，不能通过关闭检查绕过。
- 切换任务执行服务器不等于重新配置 SSH。GPU、存储、环境、checkpoint 等检查由实际任务决定，不由本技能自动扩展；同一任务中已成功的检查不重复执行。

## 进入配置或排障流程时

以下配置、worker 与验收要求仅适用于新建、重新配置或需要修复的范围。失败时先定位对应环节，修复后验收该环节一次即停止；不得因单点失败重跑整套流程。

默认使用本机已有 `/Users/suruihan/dev/kml-remote-helper/bin/kml`；需要调用时才检查文件是否存在，不假定 `~/.local/bin/kml` 链接可用。

详细命令见 [references/sop.md](references/sop.md)：已有连接的简短示例见第 0 节；新建或重新配置开发机/launcher 读第 1–3、5–6 节；独立 worker 按需读第 4 节；排障只读第 7 节及对应失败环节；移除读第 8 节。旧实例信息均为示例，仅新配置或绑定变更需要重新核对目标。

## 目标与范围

- 从用户的 URL、截图或机器名称确定项目 ID、开发机 ID 或运行记录 ID、具体 Pod 与容器。训练记录用 `selectedRecordId`，不使用任务 ID 或 `_t` 时间戳作为实例标识。
- 单一任务可有多个并存运行记录。默认为选定记录的 Running launcher 创建本机别名；指定 worker 时绑定该 worker 的完整 Pod。新建配置只有名称时先查 KML 实例详情。
- 沿用用户指定的别名和代理；没有新要求时使用下方本机约定。同一物理主机上不同记录可能有不同 SSH 端口，不能凭主机名沿用端口。
- 用户要求配置训练记录的 launcher 时，默认同时完成 launcher 到该记录全部 worker 的免密 SSH 与别名配置。仅明确要求单独 worker 或开发机时，按其范围处理。
- 移除旧别名仅在用户要求时执行。删除 SSH 配置块与 `kml remove --yes` 的范围不同，后者还删除生成文件、cookie 与缓存。

## 本机约定

生成目录为 `~/dev/relay/kml-ws/<name>/`，公钥为 `~/.ssh/id_ed25519_kml.pub`。按需检查 helper 代码与现有生成文件，尤其是 `env.sh`、`proxy-command.sh`，不要把旧目录中的信息当成当前记录。

海外代理默认值：

```text
http_proxy=http://oversea-squid1.jp.txyun:11080
https_proxy=http://oversea-squid1.jp.txyun:11080
no_proxy=localhost,127.0.0.1,localaddress,localdomain.com,internal,corp.kuaishou.com,test.gifshow.com,staging.kuaishou.com
```

`KML_HTTP_PROXY` 控制生成的本机 SSH `SetEnv`，但远端可能不接受这些变量。还需在每台本次配置的目标实例更新 `/etc/environment` 与 `/root/.bashrc`，保留原有内容并备份；`.bashrc` 的代理块置于提前返回语句之前。用新的非交互式和交互式 SSH 会话验证。

## 配置与排障决策

1. 查看现有别名和生成目录，先备份将修改的 SSH 配置，核对实际 KML 记录状态。
2. 正常开发机或 launcher 使用 helper 的 `add` 与 `update-server` 流程。普通 WebSocket 转发由记录专属守护管理，不能用广泛 `pkill` 停掉其他记录。
3. launcher 故障而 worker 存活时，采用 worker 自己的 WebShell 模式，设置该 worker 的 `KML_POD_NAME` 和实测 `KML_TARGET_PORT`。此连接不能依赖已故障 launcher 的中转。
4. 401 或登录过期时核对项目、账号权限和 SSO。保留有效浏览器会话；登录按钮可能显示中文“一键登录”或英文“One-Click Login”。涉及扫码或人工认证时等待用户完成认证，不声称配置已通过。不要持续重复会清空登录状态的操作；同样的失败再次出现时检查具体失败层或换用 SOP 中保留会话的路径。
5. 502、握手关闭和 `Permission denied` 分别检查实例/桥接服务、端口、身份与密钥。若本机端口被占用，先核实进程命令和归属，再清理确认属于旧隧道的进程。不要把所有登录失败解释成缺少公钥。
6. 不输出 cookie、SSO token 或私钥。安装公钥保留远端现有 `authorized_keys`；已有 KML 密钥能用时不必另造或分发私钥。

## launcher 到 worker：新建或重新配置时的必需项

- 按选定记录枚举全部 worker，从每个实例的 WebShell 或服务信息核对 IP、主机名和 SSH 端口。
- 优先使用 launcher 已有 `/root/.ssh/id_rsa`，先测试实际专用端口。确实缺授权时，只将 launcher 的公钥添加到对应 worker。
- 在 launcher 的 `/root/.ssh/config` 为每个 worker 配置 `worker-N`、`kml-wN`、实际 `gpuN` 别名、IP 与完整主机名，明确指定 `HostName`、`Port`、`User`、`IdentityFile`、`IdentitiesOnly yes` 与 `BatchMode yes`。使用带运行记录 ID 的标记块，保留其他 Host，处理冲突的旧块。
- `gpuN` 映射以该 launcher 的 `/etc/hosts` 与实例身份为准，不能假定 gpu 编号等于 worker 编号加一。SSH 默认 22 端口通常不是 KML 容器专用端口。
- 对每个 `worker-N` 和对应 `gpuN`，使用新连接、公钥认证执行 `hostname`。只测试带 `-p` 的命令不足以证明快捷别名配置完成。
- launcher 内的 `kml-wN` 与本机同名别名属于不同 SSH 配置。交付时明确命令在哪台机器执行。

## 验收与交付

快速复用仅简要报告连接可用并继续任务，不补齐下述配置验收清单。以下要求用于本次新建或修改的配置；局部修复仅验收受影响的部分。

使用 `BatchMode=yes`、`ControlMaster=no`、`ControlPath=none` 新建 SSH 连接，核对返回主机名与目标实例，并检查三个代理变量。密码登录不算免密完成，环境变量存在也不代表代理请求已成功；用户需要网络可用性时实际请求验证。

含 worker 的 launcher 配置需全部 worker 和快捷名称通过验收。失败实例明确报告原因，不能将整组标记为成功。

持久性描述限定到实际机制：普通 WebSocket 守护能重启当前容器内退出的转发子进程；守护自身退出、容器销毁或重建仍需恢复配置，已有 SSH 会话也需重连。WebShell 模式按每条连接创建桥接，并依赖有效 SSO。

最终简要给出本机 SSH 命令、绑定运行记录与实例、代理验证结果，以及 launcher 内各 worker 的命令和映射。报告当前实测结果，标明未验证的部分。
