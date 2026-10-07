# 指定服务器后的部署、资源与 deploy key

仅用户指定远端时读取。本流程授权的是工作区部署和只读资源调查；不安装训练环境、不初始化 CUDA、不做 benchmark、不启动作业。复用当前项目范围内已验证的连接和传输通道，不复用其他仓库的 deploy key。

## A. 主机身份、实例与路径

1. 以用户给出的 SSH alias/连接信息为起点，读取有效 SSH 配置而不打印私钥、代理凭据或完整环境。连接保持 `StrictHostKeyChecking=yes`；可复用已信任的 known_hosts。
2. 新主机或指纹变化时，用平台控制面、可信记录或用户给出的指纹核验。`ssh-keyscan` 只能采集候选公钥，不能独立证明身份。没有可信来源时询问指纹/实例身份，不用关闭校验绕过。
3. 只读核实 hostname、登录用户、实际实例/record、目录权限、挂载和空间。KML 使用 `/mmu_vlm_hdd/home/rhsu/playground`；路径不可写或缺失时报告具体阻塞，不擅自改 `/root` 或其他人的目录。
4. 代码目录为 `<root>/<project>`，运行时为 `<root>/<project>-data`。其他服务器从用户指令、项目文档或已核实的使用记录确定常用根；没有证据时询问根目录，同时继续本机和 GitHub 步骤。
5. 远端已有同名路径时先检查文件、Git root、branch、remotes、HEAD 和工作树。已有无关目录不能覆盖；已有未提交修改先保留并审阅，禁止 reset/clean。共用挂载只保存一份 checkout，worker 不复制到 `/root`。

## B. 首次复制与 Git 通道

- 新私有仓库尚无远端读取凭据时，可通过已验证 SSH 将本机已提交历史制作的 Git bundle 复制到远端项目根，再在空代码目录 clone；先核实不会覆盖已有路径。bundle 放允许根内，bootstrap 完成后记录并清理本次临时文件。
- 或使用 `rsync` 明确复制代码和 `.git` 的必要内容到空目录，先审阅传输清单；排除 `.env`、私钥、私有配置、环境、模型、数据、缓存。不要无审核 `--delete`，不要上传整个家目录。
- 数据不随代码自动复制；需要的原始依赖和执行环境仍为未准备状态。不要因复制完成而写“环境验收通过”。
- 完成 deploy key 配置后，remote `origin` 使用对应 GitHub SSH URL。已有正确 remote 不反复改写。共享代码目录只有 launcher 进行 Git 写入。

## C. 本次允许节点的只读资源调查

KML 必须读取并应用本环境可用的 `kml-gpu-usage` 技能，按需读其 deployment 参考。真实技能名不是 `kml-gpu-use`。技能不可用时查找其实际入口；仍缺失就记录阻塞并推进其他步骤，不伪称已应用。

1. 从当前平台记录、分配清单、hostfile 和用户授权识别 launcher 与 workers。只调查本次允许的节点，不扫描网段；能 SSH 到某机器不自动等于有权调度其 GPU。
2. 先保存 launcher 的资源和挂载摘要，再按平台提供的方式核验 worker 连接与主机身份。不要沿用其他实例的 IP、端口、record、alias 或指纹，不用 GitHub deploy key 登录 worker。
3. 每个节点查询 GPU UUID、型号、总/空闲显存和利用率，CPU/RAM、项目目录与共享挂载可见性。例如：

   ```bash
   hostname
   nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.free,utilization.gpu --format=csv
   ```

   没有 `nvidia-smi` 不等于没有 GPU；结合设备/平台信息判断“未发现”或“检测失败”。只读 snapshot 不能证明 CUDA、Fabric、通信或训练正常，不导入 torch 做隐式健康测试。
4. 在项目文档保存本次原始或脱敏 snapshot，用 AGENTS 表列 `role / 连接方法 / hostname / GPU UUID或索引 / 型号与数量 / 总显存 / 空闲显存范围 / 允许使用范围 / 核查时间 / 状态`。可链接较长的 UUID 清单，不把 hostfile slots 当 GPU 实测数量。
5. 分别汇总：平台分配、成功连接且检测到的资源、允许调度的范围、不可达或未知节点。写明确时间与时区、瞬时空闲不保证未来可用、每次作业前重新核验。CPU-only 服务器如实记“已核实无可见 GPU”；不凭模板写 4 节点或 32×H100。

AGENTS 的 KML 约定必须要求负责 GPU 工作的代理应用 `kml-gpu-usage`，按实测峰值加余量准入、记录节点/卡号/端口、保护其他作业和系统驱动、统计实际预留 GPUh。具体卡数、训练拓扑和预算由新项目实测和用户决定。

### KML 占卡程序写入新 AGENTS

若目标服务器确为 KML，在模板 KML 段中写入共享入口 `/mmu_vlm_hdd/home/rhsu/idle-job-can-kill-anytime/idle-job`，保留用户已授权 Agent 在执行 GPU 任务前直接停止当前实例、无需再次确认的规则。生成的 AGENTS 必须包含 launcher 执行位置、`status` / `stop`、前台 `run --`、停止后验收、实例隔离、保护真实作业及子进程可能被守护重新拉起的说明；不复制 kml-1007、旧 record 或固定卡数。

初始化时仅检查程序路径和本实例已有 manifest/status 的启用状态，把带时间摘要填入 `kml_idle_job_status`。优先读取已有元数据；未部署、未登记、无权限或查询失败如实填入，不为调查执行 `discover`、`start`、`stop` 或 `run`，也不安装占卡依赖。未来 GPU 任务按 `kml-gpu-usage` 的占卡协调流程处理。

非 KML 或没有指定远端时删除整个模板 KML 块及其状态占位符；不把这条本机 KML 约定写给其他服务器。创建工作区本身不消耗额外 GPU 资源，不因补充文档而改变现有占卡或训练状态。

## D. 为单个仓库配置读写 deploy key

deploy key 提供 Git 传输权限，不提供 GitHub API 登录。所有 GitHub API 操作使用本机 `gh`；不将本机 `gh` token、keychain 或账号配置复制到服务器。

1. 先检查此项目是否已有经核验的专属 deploy key：本机公钥指纹、仓库 key 列表中的指纹/ID、`read_only=false`、远端对应公钥及 transport 配置。完整且有效时复用，不每次生成重复 key。已有不明或其他仓库的 key 不覆盖、不借用。
2. 尚无专属 key 时，本机生成唯一 Ed25519 key。示例仅表示参数，应使用已核实项目名、账号、仓库和本机私有目录：

   ```bash
   ssh-keygen -t ed25519 -f '<local-private-dir>/<owner>-<project>-deploy' -N '' -C '<owner>/<project> deploy'
   gh repo deploy-key add '<local-private-dir>/<owner>-<project>-deploy.pub' --repo '<owner>/<project>' --allow-write --title '<server>-<project>'
   ```

   自动化 key 无交互口令，安全边界由单仓库权限和私有目录提供。生成前拒绝覆盖已有文件；目录权限 700、私钥 600、公钥 644。保留本机备份但不入库。
3. 公钥通过本机 `gh` 注册后核对仓库、key ID、指纹和读写标志。注册失败先查是否已成功，不自动删除现有 key；重复注册按现有状态处理。
4. 通过已核实 SSH 私有通道传私钥和公钥到 `<runtime-root>/secrets/github/`，权限同上。不经过代码仓库、不放临时公共目录、不输出 key 内容、请求 headers 或带凭据的代理配置。
5. 在此私有目录写仓库专用 SSH config 和 GitHub known_hosts；通过 GitHub 官方公开指纹等可信来源核实 host key。关键设置是 `IdentityFile` 指向专属私钥、`IdentityAgent none`、`IdentitiesOnly yes`、`BatchMode yes`、`StrictHostKeyChecking yes`、`UserKnownHostsFile` 指向项目私有文件；强制使用该 key，不回退个人 SSH agent 或账号凭据。保留其他项目/平台配置，不改全局文件。
6. 仓库级 `git config core.sshCommand` 指向该 SSH config；remote 使用 `git@github.com:<owner>/<project>.git` 或经过核验的独立 GitHub alias。配置包含允许的实际绝对路径，worker 不默认继承 launcher 的缓存或代理环境。
7. 常规端口不可达时，可在项目私有 config 使用 `ssh.github.com:443`；HTTP(S) 代理只用现场已验证通道，记录无凭据摘要，不把代理地址硬编码进代码。不能通过关闭主机校验排障。
8. 用远端无 `gh` 登录的 Git 进程执行 fetch/`ls-remote`，确认读取可用；核对 `read_only=false`。最终由 launcher 提交真实的资源/部署文档改动并正常 push，再读取 GitHub ref 验证该提交，才作为实际写入证据。不制造测试 commit 或临时 branch，不 force push。up-to-date/dry-run push 仅记录连接检查，不冒充已经写入远端；不能把 SSH“认证成功但不提供 shell”的退出码直接当 Git 失败。

记录 key ID、公开指纹、仓库、服务器、私钥存放路径和读写验证时间，不记录私钥内容。网络暂时失败保留已生成配置与 key ID，基础设施重试最多 2 次，先核对已完成状态；不靠连续生成 key 解决网络问题。只有声明权限和读取证据时写“声明读写权限已核、Git 读取成功、实际写入待验”，不能宣称远端可以 push。交接时提示 key 生命周期：撤销创建它的 token/App 后，该 key 可能被删除，按 [gh 官方说明](https://cli.github.com/manual/gh_repo_deploy-key_add) 重新核查。

## E. 收尾同步

1. 将连接路径、资源表、credential 使用入口写入 AGENTS；私有 SSH/key 文件留运行时。若项目公开过文档，重新检查资源信息适不适合 Git 收录，不混入凭据。
2. 选择唯一提交端。优先在 launcher 补齐 AGENTS 的真实部署/资源信息，本机审阅差异后由 launcher 提交推送，核实 deploy key 的真实写入；本机检查 clean working tree 和相同 branch，再 fetch/pull `--ff-only`。若最终提交在本机完成则反向同步，远端写入状态按实际证据报告。有修改或分叉先保留，不能强制覆盖。
3. 比较本机 `git rev-parse HEAD`、GitHub `refs/heads/<branch>` 与远端 HEAD，并核对两端 `git status --short`；本机/远端提交应串行完成，避免竞争。
4. 交付中说明实际代码版本、private 可见性、远端部署与 key 验证、调查范围、未知节点和未验证的执行环境。完成 bootstrap 后不自动启动后续研究作业。
