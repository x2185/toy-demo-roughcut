# 玩具实拍视频粗剪

供 Codex 使用的玩具实拍粗剪技能。提供素材路径和要求，由 Codex 观察画面、选择剪辑区间，再通过本机 FFmpeg 输出视频。

适用于玩具演示、开箱、装配及其他新类型玩具。根据操作关系和可见结果判断取舍，不固定30秒、统一倍速或特定品类分镜。经验来自八组前后对照，未验证所有玩具类型的效果。

## 首次安装

### 方法一 让Codex精确定位并安装

复制下面整段到Codex，无需先手动下载或填写本机目录：

```text
请在GitHub精确定位并核对这个项目，然后下载并安装为我的个人技能：
仓库：https://github.com/x2185/toy-demo-roughcut
所有者：x2185
仓库名：toy-demo-roughcut
分支：main
技能子目录：toy-demo-roughcut

请核对所有者、仓库名及该子目录的SKILL.md，避免下载同名项目。
安装完整技能目录，并检查Python、FFmpeg、ffprobe和Pillow依赖。
如果已安装，请先备份再更新，保留local-memory-location.txt和本机记忆。
```

提供准确链接即可定位，不必依赖搜索排名或模糊关键词。Codex可使用GitHub技能安装工具下载；网络或目录权限受限时，按应用提示授权。每台电脑安装一次，下次直接调用技能。

### 方法二 从GitHub手动下载

1. 打开 [仓库主页](https://github.com/x2185/toy-demo-roughcut)。仓库已公开，浏览和下载ZIP无需协作者权限。
2. 点击绿色 **Code → Download ZIP**，下载后完整解压。不要只下载 SKILL.md。
3. 打开解压目录，确认能看到 `toy-demo-roughcut` 文件夹、`docs` 和 `安装到Codex.ps1`。复制资源管理器地址栏中的实际完整路径，在 Codex 中发送：

```text
请把这个目录中的 toy-demo-roughcut 安装为我的个人技能：
D:\下载\toy-demo-roughcut-main
```

每台电脑只需安装一次。Windows也可运行根目录 `安装到Codex.ps1`；遇到已有同名目录会停止，不覆盖。

上面的路径只是示例，须替换为自己电脑上解压后能看到技能文件夹的目录。ZIP下载不需要安装Git。Word手册位于解压后的 `docs` 文件夹。

依赖 Python 3.10+、FFmpeg、ffprobe，观察联系表另需 Pillow。无需额外模型API Key，不依赖OpenStoryline或剪映；Codex分析仍依赖当前会话服务。

## 日常使用

```text
使用 $toy-demo-roughcut 粗剪 D:\素材\玩具.mp4。
删除多余动作，保留关键操作、原声和原生分辨率，成片另存。
```

可加“全程原速”“保留HDR”或参考片路径。默认保留构图与展示顺序，不新增字幕、配乐、特效。HDR源默认正确转换SDR；4K源保持原生尺寸。

分类、复核和经验记录在当前任务中自动处理。反馈可直接说“第二版第8秒多留一点回弹”。本机记忆按适用范围积累，不自动共享，不随仓库更新上传；没有后台常驻学习程序。

## 更新技能

后续更新时，重新从本仓库 **Code → Download ZIP** 下载并解压最新版，再把解压目录的实际路径交给 Codex：

```text
请用这个目录中的 toy-demo-roughcut 更新我的个人技能：
D:\下载\toy-demo-roughcut-main
先备份旧版，保留 local-memory-location.txt 和本机记忆。
```

仓库更新不等于已安装技能自动更新。个人记录不应复制进仓库。

## 文件

- `toy-demo-roughcut/`：完整技能、经验参考与执行脚本。
- `docs/玩具实拍视频粗剪使用手册.docx`：给同事的Word手册。
- `docs/使用说明.md`：安装与使用说明。
- `安装到Codex.ps1`：Windows首次安装脚本。

原视频、研究帧、本机偏好、反馈和机器路径配置均不在仓库中。首次使用及新玩法仍需人工复核关键动作和实际效果。

## 调用时检查更新

升级到带 `release.json` 的版本后，每个新对话首次调用技能时，Codex按技能指令检查GitHub上游。有新版会先暂存、核对文件及本地差异、备份后更新；本机经验和配置保留。网络失败继续用本地版，有自行修改冲突则保留本地并提示。此流程由Codex执行，仍受网络、工具和目录权限限制，不是常驻后台程序。

已经安装旧版的同事需要先主动升级一次：

```text
请从 https://github.com/x2185/toy-demo-roughcut
更新本机 toy-demo-roughcut 到带release.json的最新版。
先完整备份旧技能，保留本机路径配置和所有经验记录。
```

发布者后续修改技能时须同步更新release.json的版本及文件哈希，才能可靠检测。具体流程见技能内references/updates.md。
