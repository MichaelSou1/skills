# KML 本机免密 SSH 与自动海外代理 SOP

适用工具：`/Users/suruihan/dev/kml-remote-helper`。本文根据实际配置整理，更新于 2026-10-18。

目标：使用 `ssh kml-<name>` 登录指定开发机或训练实例，并在新 SSH 会话中自动设置海外代理。

## 0. 默认先复用已有连接

用户要求使用或切换到已有别名时，只执行一次：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=30 kml-<name> hostname
```

连接成功即停止 SSH 检查，继续用户任务。若本次任务已通过该别名成功执行命令，直接复用结果，不再探测。无需读取后续配置章节，也不强制关闭 ControlMaster 或另做交互式验收。

仅任务需要代理时，将检查合并进同一次连接：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=30 kml-<name> \
  'hostname; printenv http_proxy https_proxy no_proxy NO_PROXY'
```

需要访问网络时，以任务中的实际请求验证即可，不额外重复探测。代理变量缺失不等于 SSH 失败，只处理代理部分。

快速路径不查询平台记录、不读取 helper 源码、不枚举全部 worker、不核对端口或指纹、不运行 `add`/`update-server`/`doctor`，也不修改配置或另建项目独立 SSH 通道。没有目标冲突证据时，不为寻找冲突展开核验；用户明确指定的新记录与已有绑定冲突时，不能仅凭连接成功认定满足请求。

仅以下情况进入后续流程：

- 别名不存在，或用户明确要求新建、重新配置、变更绑定：按第 1–6 节中适用部分执行。
- 连接失败：先按第 7 节的对应错误处理，仅读取和执行需要的修复步骤；修复后验收受影响部分一次即停止。
- 已知绑定与用户指定目标不符：核对目标并重新绑定。

主机密钥冲突仅在实际报错时针对性处理，不自行关闭检查绕过。切换执行服务器不触发全量 SSH 重配，也不自动扩展到 GPU、共享存储、环境或 checkpoint 审计；这些由实际作业需求决定。

**第 1–6 节为新建或重新配置流程，不是每次调用的检查清单。局部修复只验收受影响部分；全部 worker 的配置与验收仅用于新建或重新配置整组 launcher 连接。**

## 1. 先确定目标实例

一个训练任务可以有多个运行记录，一个运行记录可以有 launcher 和多个 worker。SSH 配置必须绑定具体开发机或具体运行记录中的实例。

配置前记录以下信息：

| 字段 | 来源与用途 |
| --- | --- |
| SSH 别名 | 用户指定，例如 `kml-1003`；helper 参数写 `1003` |
| 项目 ID | 页面 URL 的 `/project/<id>`，优先用数字 ID |
| 开发机 ID | 开发机详情；用于开发机配置 |
| 任务 ID、运行记录 ID | 训练任务 URL 的 `unifiedTasks/<taskId>` 与 `selectedRecordId=<recordId>` |
| Pod、容器、集群、命名空间 | 目标实例的 WebShell 链接或详情 |
| 实际主机名、IP | 该运行记录的实例列表；最终必须用 `hostname` 核对 |
| 实例 SSH 端口 | 目标容器里的 `$SSHD_PORT`、sshd 启动参数或监听信息 |

规则：

- 训练任务必须使用带 `selectedRecordId` 的 URL，或明确的运行记录 ID。URL 中的 `_t` 只是时间戳。
- 普通 `kml add` 将训练记录绑定到该记录的 Running launcher。
- **以后配置含 worker 的训练记录时，默认同时在 launcher 上配置全部 worker 的免密 SSH 连接和快捷别名，并逐台验证；只有 launcher 可登录不算完成。** 此步骤需要按下文执行，不能假定 `kml add` 已自动完成。
- 单独配置 worker 时，必须明确完整 Pod 名，例如 `kml-task-<taskId>-record-<recordId>-prod-worker-0`。
- 只有机器名称或截图时，先在 KML 核对它所属的记录、Pod 与项目，再执行配置。不要把机器名称直接当作开发机 ID。
- `gpu1/gpu2/...` 可能指向镜像预置或其他集群地址。必须核对 `/etc/hosts`；SSH 端口也不能默认认为是 22。

## 2. 本机准备

需要系统 OpenSSH、Python 3、`nc`、`curl`、`agent-browser`，以及能完成 KML 企业 SSO 的浏览器会话。

直接使用源码 CLI，避免依赖可能缺失的 `~/.local/bin/kml` 链接：

```bash
KML=/Users/suruihan/dev/kml-remote-helper/bin/kml
"$KML" list
cp -p ~/.ssh/config ~/.ssh/config.before-kml-$(date +%Y%m%d-%H%M%S)
```

默认公钥为 `~/.ssh/id_ed25519_kml.pub`，私钥为同名无 `.pub` 文件。仅将公钥加入远端，保留原有 `authorized_keys` 内容。

## 3. 开发机或正常 launcher：主流程

以运行记录 `100882024` 为例：

```bash
KML_HTTP_PROXY=http://oversea-squid1.jp.txyun:11080 \
  "$KML" add 1003 \
  'https://kml.corp.kuaishou.com/#/project/10278/training/unifiedTasks/100041666?tab=records&selectedRecordId=100882024' \
  --project 10278
```

开发机使用对应开发机 ID 或 URL：

```bash
KML_HTTP_PROXY=http://oversea-squid1.jp.txyun:11080 \
  "$KML" add <name> <开发机ID或URL> --project <项目ID>
```

helper 会创建本机 SSH 配置、实例脚本目录、隧道配置，并通过目标 WebShell 安装公钥和启动远端转发守护。需要 SSO 时，在打开的浏览器中完成一键登录或 KIM 验证，再继续。

配置后检查 `~/dev/relay/kml-ws/<name>/env.sh` 中的项目、记录、Pod、容器。看到 `is ready` 后仍执行第 6 节的独立验证。

**本机 `SetEnv` 不能保证远端接收代理变量。还必须执行第 5 节的远端环境配置。**

### 3.1 同时配置 launcher 到全部 worker 的免密连接

1. 从该运行记录的实例列表取得全部 worker 的 Pod、主机名和 IP；分别通过 worker 的 WebShell 查询 `$SSHD_PORT`，并核对监听端口。
2. 在 launcher 检查 SSH 密钥。KML 镜像通常已有 `/root/.ssh/id_rsa`，优先使用现有密钥，通过实际专用端口逐台测试公钥登录。若密钥确实未获授权，通过对应 worker 的 WebShell 将 **launcher 的公钥** 加入其 `authorized_keys`，保留已有内容。私钥留在 launcher。
3. 备份 launcher 的 `/root/.ssh/config`，为每个 worker 写入独立配置块：包含 `worker-<编号>`、`kml-w<编号>`、其真实 `gpuN` 别名、IP 和完整主机名；明确设置 `HostName`、实际 `Port`、`User root`、`IdentityFile`、`IdentitiesOnly yes` 与 `BatchMode yes`。
4. 按 `/etc/hosts` 核对 `gpuN` 与 worker 的对应关系。**gpu 编号不一定等于 worker 编号加一。** 对已有同名配置先核对并替换，避免 OpenSSH 优先使用旧块中的端口。不要直接追加互相冲突的 Host 块。
5. 在 launcher 上使用配置后的快捷名称逐台执行 `ssh worker-<编号> hostname` 和 `ssh gpuN hostname`，核对返回的主机名。不能仅验证带 `-p` 参数的命令后就交付。

例如，运行记录 **100890188** 的 worker-0 对应 gpu1，在 launcher 的 `/root/.ssh/config` 中配置为：

```sshconfig
# >>> kml-record-100890188-workers
Host worker-0 kml-w0 gpu1 10.48.50.22 aiplatform-wlf3-ge99-12.idchb2az3.hb2.kwaidc.com
    HostName 10.48.50.22
    Port 21024
    User root
    IdentityFile /root/.ssh/id_rsa
    IdentitiesOnly yes
    BatchMode yes
    StrictHostKeyChecking accept-new
    ServerAliveInterval 30
    ServerAliveCountMax 3
# 为同一记录的其他 worker 添加各自 Host 块
# <<< kml-record-100890188-workers
```

此示例的 IP、端口和 gpu 映射只适用于该记录，配置新记录时必须重新核对。launcher 上的 `kml-w0` 是远端 SSH 别名，与本机 `~/.ssh/config` 中的同名别名属于不同配置，不能混用。

## 4. launcher 故障：独立配置 worker

此方式经目标 worker 的 KML WebShell 转发 SSH，不经过 launcher。每个 worker 使用独立别名、脚本目录和 `KML_POD_NAME`。

### 4.1 核对 worker 并安装公钥

打开该 worker 自己的 WebShell，执行：

```bash
hostname
printf 'SSHD_PORT=%s\n' "$SSHD_PORT"
ss -ltnp
```

本机执行 `cat ~/.ssh/id_ed25519_kml.pub`，将输出的一整行公钥替换下面占位符，在目标 worker 的 WebShell 执行：

```bash
mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys
cp -p /root/.ssh/authorized_keys /root/.ssh/authorized_keys.before-kml-local
key='替换为本机公钥完整一行'
if ! grep -Fqx "$key" /root/.ssh/authorized_keys; then
  printf '\n%s\n' "$key" >> /root/.ssh/authorized_keys
fi
chmod 600 /root/.ssh/authorized_keys
```

然后在该 worker 的 WebShell 执行第 5 节的代理配置。

### 4.2 生成本机配置并切换到 WebShell 模式

如果 launcher 已故障，普通记录解析可能无法通过 Running launcher 检查。可以使用底层生成器。下例采用曾实际配置过的记录，使用前必须替换成目标记录的真实数据：

```bash
KML_HTTP_PROXY=http://oversea-squid1.jp.txyun:11080 \
  /Users/suruihan/dev/kml-remote-helper/resources/scripts/kml-add-machine \
  w0 \
  'wss://kml-task-100041666-record-100841521-prod-tensorboard.kce-aip-wlf1-hb2az1.corp.kuaishou.com/dtmachine-100841521'
```

生成器创建 `kml-w0` 并自动选择本机端口。随后编辑 `~/dev/relay/kml-ws/w0/env.sh`，将 `KML_TUNNEL_MODE` 改成 `webshell`，补齐或替换以下字段，不保留冲突的重复定义：

```bash
export KML_TUNNEL_MODE='webshell'
export KML_PROJECT_ID='10278'
export KML_CREATOR='suruihan'
export KML_CLUSTER_NAME='kce-aip-wlf1-hb2az1'
export KML_NAMESPACE='kubekml'
export KML_POD_NAME='kml-task-100041666-record-100841521-prod-worker-0'
export KML_CONTAINER_NAME='kaiv2'
export KML_TARGET_PORT='21048'
```

上面的 `21048` 是该旧实例的端口，不能套用到新记录。WebShell 模式实际使用 Pod 和 `KML_TARGET_PORT` 建立连接；生成器保存的 `KML_WS_URL` 不作为该模式的传输入口。

对 worker-1 等实例重复操作，分别使用 `w1` 等名称、对应 Pod 与实际端口。WebShell 模式依赖有效的企业 SSO；首次连接可能打开浏览器，启动速度通常比普通 WebSocket 隧道慢。

## 5. 在目标实例配置自动代理

新建配置使用以下默认值；已有实例仅修改直连规则时保留代理地址：

```bash
export http_proxy=http://oversea-squid1.jp.txyun:11080
export https_proxy=http://oversea-squid1.jp.txyun:11080
export no_proxy=localhost,127.0.0.1,localaddress,localdomain.com,internal,.internal,corp.kuaishou.com,test.gifshow.com,staging.kuaishou.com
export NO_PROXY="$no_proxy"
```

只配置本次指定的实例。先读取环境与两个配置文件，合并已有的 `no_proxy` / `NO_PROXY` 排除项。下方脚本从当前环境保留代理地址和排除项；若文件中还有未加载的自定义项，先加入 `values`。检查旧代理赋值的位置，清理已确认的重复赋值，避免后续覆盖。复杂条件或动态赋值应按原意手动合并。

以下脚本在远端以 root 执行，可通过已经可用的 SSH 或该实例自己的 WebShell 执行。它备份并更新 `/etc/environment`，在 `/root/.bashrc` 的提前返回语句之前加入代理设置：

```bash
python3 - <<'PY'
from pathlib import Path
import re
import os
import shlex

values = {
    'http_proxy': 'http://oversea-squid1.jp.txyun:11080',
    'https_proxy': 'http://oversea-squid1.jp.txyun:11080',
    'no_proxy': 'localhost,127.0.0.1,localaddress,localdomain.com,internal,.internal,corp.kuaishou.com,test.gifshow.com,staging.kuaishou.com',
}
for key in ('http_proxy', 'https_proxy'):
    values[key] = os.environ.get(key) or values[key]
items = []
for source in (os.environ.get('no_proxy', ''), os.environ.get('NO_PROXY', ''), values['no_proxy']):
    for item in source.split(','):
        item = item.strip()
        if item and item not in items:
            items.append(item)
values['no_proxy'] = values['NO_PROXY'] = ','.join(items)
def backup(path, original):
    dest = Path(str(path) + '.before-kml-proxy')
    if not dest.exists():
        dest.write_text(original)
        dest.chmod(path.stat().st_mode & 0o777)

path = Path('/etc/environment')
original = path.read_text()
backup(path, original)
lines = [x for x in original.splitlines()
         if not any(re.match(r'^\s*' + k + r'\s*=', x) for k in values)]
lines += [f'{k}="{v}"' for k, v in values.items()]
path.write_text('\n'.join(lines) + '\n')

path = Path('/root/.bashrc')
original = path.read_text()
backup(path, original)
start, end = '# >>> kml-proxy', '# <<< kml-proxy'
original = re.sub(r'(?ms)^' + re.escape(start) + r'\n.*?^' +
                  re.escape(end) + r'\n?', '', original)
# 仅移除独占一行的简单赋值；执行前已确认这些旧值已合并。
original = re.sub(r'(?m)^(?:export\s+)?(?:http_proxy|https_proxy|no_proxy|NO_PROXY)=[^\n]*\n?', '', original)
block = '\n'.join([start] + [f'export {k}={shlex.quote(v)}' for k, v in values.items()] + [end, ''])
path.write_text(block + original)
PY
```

已打开的 SSH 会话不会自动刷新环境。关闭后新建连接进行验证；若新会话仍缺变量，检查 sshd 的 PAM 环境加载和 shell 启动文件。

## 6. 新建或修改配置后的验收

仅对本次新建或修改的配置禁用连接复用，避免已有 ControlMaster 掩盖配置问题。已有连接快速复用不执行本节，局部修复不触发整组验收；通过后停止检查：

```bash
ssh -o BatchMode=yes -o ControlMaster=no -o ControlPath=none \
  -o ConnectTimeout=30 kml-<name> \
  'hostname; whoami; printenv http_proxy https_proxy no_proxy NO_PROXY'
```

验收条件：公钥登录成功、不要求密码；`hostname` 与目标实例一致；HTTP/HTTPS 代理地址符合预期，`no_proxy` 与 `NO_PROXY` 一致且包含原有排除项与 `internal,.internal`。交互式 shell 也检查这四个变量，确认后续启动文件未覆盖设置。

**新建或重新配置含 worker 的整组 launcher 连接时，还必须通过 launcher 到全部 worker 的验收。** 在 launcher 上执行以下命令，并将名称列表替换为该记录全部 worker：

```bash
set -e
for node in worker-0 worker-1 worker-2; do
  printf '%s -> ' "$node"
  ssh -n -o BatchMode=yes -o ControlMaster=no -o ControlPath=none \
    -o ConnectTimeout=10 "$node" hostname
done
```

再逐台验证配置的 `gpuN` 快捷名称。每次必须使用新连接；全部返回正确主机名且无需密码才算完成。若某个 worker 已故障或无法通过 WebShell 配置，应明确列出该实例和失败原因，不将整组连接标记为已完成。

若要确认代理网络可用，可在远端执行 `curl -I --connect-timeout 10 --max-time 20 https://huggingface.co`。环境变量存在只证明已配置，网络连通性以实际请求为准。

### 6.1 修改 `.internal` 直连规则后的对照验证

在新的 SSH 会话中运行 curl 对照测试：用临时本地 HTTP 服务监听 `127.0.0.1` 的随机端口，以 `--resolve` 将一个 `.internal` 测试域名映射到该服务。命令显式指定不可用的本地代理，例如 `--proxy http://127.0.0.1:1`（先确认该端口未监听），保留会话中的 `no_proxy` / `NO_PROXY`，不传 `--noproxy`。

`.internal` 请求应直接返回本地服务响应。换成不在排除列表中的普通域名，使用同样的映射和代理，应出现代理连接失败。请求设置 `--max-time 5`，测试结束关闭临时服务。该对照证明 curl 按域名分流；内部 DNS、实际业务服务和其他客户端需以用户所用客户端的真实请求验证。

`.internal` 是域名后缀，不是 IP 网段。curl 支持该后缀匹配，不使用 `*.internal`；直接通过 IP 访问时需单独列出 IP 或客户端支持的 CIDR。参见 [curl 代理环境变量说明](https://github.com/curl/everything-curl/blob/master/usingcurl/proxies/env.md)。

## 7. 持久运行与故障处理

普通 WebSocket 模式下，远端转发守护位于：

```text
/root/.local/share/kml-remote-helper/record-<开发机ID或运行记录ID>/
```

`supervisor.pid`、`child.pid` 标识守护与转发进程，`supervisor.log` 记录启动和退出。守护脱离登录会话运行，转发子进程退出后约 2 秒重启。

```bash
"$KML" update-server <name>  # 通过目标 WebShell 更新当前实例的转发服务
"$KML" login <name>          # 刷新普通 WebSocket 模式的 SSO cookie
"$KML" restart <name>        # 重启本机隧道
"$KML" doctor <name>         # 检查本机配置
```

该守护保障当前容器中的转发子进程恢复；守护自身被终止、容器被删除或重建时，需要重新启动或配置。转发退出会中断已有 SSH 会话，服务恢复后需重连。WebShell 模式则为每条 SSH 连接建立自己的桥接进程，无需在 worker 上部署 launcher 的 WebSocket 服务。

| 现象 | 排查与处理 |
| --- | --- |
| `Unauthorized` / HTTP 401 | 核对项目 ID、账号权限及 SSO；打开目标项目与记录页完成登录后重试 |
| HTTP 502 / SSH 握手关闭 | 检查目标实例是否存活，以及远端转发进程、端口和守护日志 |
| `Permission denied (publickey)` | 核对实际 Pod、SSH 端口、客户端密钥及该实例的 `authorized_keys`；密码登录不算成功 |
| 本机端口被占用 | 用 `lsof -nP -iTCP:<端口> -sTCP:LISTEN` 和 `ps -p <PID> -o args=` 确认归属，处理已确认的旧隧道进程 |
| `gpu1` 等别名登录失败 | 核对它的 IP、端口及密钥；使用已核对的实例地址与专用 SSH 端口 |
| 新会话无代理 | 检查远端 `/etc/environment` 与 `.bashrc`；仅本机 `SetEnv` 不足以保证生效 |
| launcher 故障而 worker 存活 | 使用第 4 节对 worker 单独配置；先验证该 worker 的 WebShell 可用 |

## 8. 替换或移除旧别名

修改前备份 `~/.ssh/config`。只要求移除 SSH 配置时，删除该别名对应的完整标记块，并保留其他 Host：

```text
# >>> kml-remote-helper:kml-<name>
Host kml-<name>
...
# <<< kml-remote-helper:kml-<name>
```

`kml remove <name> --yes` 会同时删除生成目录、本机 cookie 与缓存，仅在明确要求完全移除时使用。旧别名移除后，再次验证新别名可以独立登录。

新建或重新配置的交付说明：别名、项目、运行记录、目标 Pod、实测主机名、代理验证结果，以及是否依赖 launcher。含 worker 时同时交付每个 worker 的 launcher 侧别名、gpu 映射、IP、SSH 端口和逐台验证结果。
