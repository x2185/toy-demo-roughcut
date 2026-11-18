# 本地执行

Python3.10+，ffmpeg/ffprobe（libx264；HDR另需libx265；HDR→SDR需zscale、tonemap）。联系表用Pillow，缺失时`python -m pip install pillow`。无需其他剪辑项目或额外模型API。

首次安装、切换Python或遇到工具错误时运行 `python scripts/check_environment.py`，分别报告普通SDR、HDR转SDR和HDR输出能力；`--mode hdr-to-sdr`或`--mode preserve-hdr`可核对当前素材所需模式，缺项返回非零。检查只读、不下载安装，也不等同于真实素材已渲染成功。使用检查时同一个Python执行观察脚本。

## 观察

`python scripts/inspect_video.py "源.mp4" "观察目录" --step 2`

候选切点加密：`--start 12 --end 15 --step 0.1`。联系表时间是近似采样网格，不是自动检测的精确源帧。

## 计划

UTF-8 JSON，相对路径以计划文件目录为基准，区间是**原素材秒数**：

```json
{
  "source": "D:/素材/玩具.mp4",
  "output": "D:/输出/玩具_粗剪_4K.mp4",
  "fps": 30,
  "color_mode": "sdr",
  "audio": "keep",
  "clips": [
    {"start": 3.2, "end": 6.7, "speed": 1, "reason": "装入到首次释放"},
    {"start": 9.1, "end": 12.4, "speed": 1.5, "reason": "后续准备适度加速"}
  ]
}
```

示意区间不能复制给未看过素材。fps默认30（本批样例）；其他源帧率需显式按原帧率/要求设置。`color_mode=preserve-hdr`保留HLG/PQ；默认sdr正确映射HDR。无音轨源正常输出无音轨；静音用`audio=mute`。

默认不允许重排重叠；用户授权时设`allow_reorder=true`。输出必须不存在。速度支持0.25–4×，这是工具范围，不是推荐范围。

## 执行与验收

`python scripts/render_edit.py "计划.json" --check-only`

`python scripts/render_edit.py "计划.json"`

分段视频不带AAC，原声按同区间处理成连续音轨后一次编码，避免逐段AAC填充拖长。先在输出目录下的独立临时目录渲染，核对尺寸、时长、音轨及全片解码后，再以正式文件名交付MP4和`.edit.json`，不覆盖原片或已有文件。失败不会把未验收视频留作正式成片；仍需查看动作及切点。两份文件不是跨文件事务，异常断电可能只留下记录文件，不能据此认定已有成片。

HLG/PQ重编码不保留杜比视界动态元数据，也不是无损复制。SDR用H.264，HDR用HEVC10-bit。没有HDR信息不能硬标HDR。

失败时不要静默降1080p、改标签或丢声音。缺滤镜/编码器就说明缺项并解决。Windows沙箱临时目录写入被拒时按宿主权限流程重试，不改全局安全设置。已有成片使用新文件名再渲染，不覆盖。

脚本不自动识别动作、不生成字幕/音乐/特效。工具验证通过不代表风格获人工认可；听审能力缺失时如实注明。
