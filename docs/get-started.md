# 🚀 yt-vedio-sum

YouTube 视频转录工具，支持自动语音识别和说话人分离。

## 功能特性

| 功能 | 说明 |
|------|------|
| 🎙️ 语音转录 | 使用 Faster-Whisper 进行高精度语音识别 |
| 🌍 多语言支持 | 自动检测语言或手动指定语言代码 |
| 👥 说话人分离 | 使用 pyannote.audio 识别不同说话人 |
| ⚙️ 智能硬件适配 | 自动检测 GPU 并选择最优计算精度 |
| 📝 带时间戳输出 | 输出包含时间戳的转录文本 |
| 🔄 错误重试 | 网络失败自动重试（指数退避） |

## 快速开始

### 1. 系统依赖

- **ffmpeg** - 音频处理（必须）
  ```bash
  # macOS
  brew install ffmpeg

  # Ubuntu/Debian
  sudo apt install ffmpeg
  ```

- **GPU（可选）** - 用于加速转录
  - 程序会自动检测 GPU，有 GPU 时自动使用
  - NVIDIA GPU 需要 CUDA 驱动支持（最低 CUDA 11.8）
  - 没有 GPU 时自动回退到 CPU 模式

### 2. 首次使用准备（模型下载）

```bash
uv tool install huggingface_hub

# 登录 HuggingFace（需要先申请访问权限）
hf auth login

# 下载 Whisper 模型（默认使用 turbo） ， Faster-Whisper 模型（必选）
hf download --local-dir ~/.cache/huggingface/hub/openai/whisper-turbo openai/whisper-turbo

# 访问 https://huggingface.co/pyannote/speaker-diarization-3.1 点击 "Request access"
# 再下载 pyannote 说话人分离模型（可选）
hf download pyannote/speaker-diarization-3.1 --local-dir ~/.cache/huggingface/hub/models--pyannote--speaker-diarization-3.1

```

###  3 使用虚拟环境运行

```bash
cd src && uv venv && source .venv/bin/activate && uv pip install -e .

cd src && uv run python -m yt_cli "https://www.youtube.com/watch?v=43kikAbL8u8"
```

### 3. 安装使用

```bash

# 安装
cd src && uv tool install -e .

# 默认，禁用说话人分离， 只使用 --whisper-model 模型进行本地转录
yt-summarize-vedio "https://www.youtube.com/watch?v=43kikAbL8u8"

# 指定语言
yt-summarize-vedio "URL" --language en

# 指定输出路径
yt-summarize-vedio "URL" -o ./my_transcript.txt

# 启用说话人分离， 在使用 --whisper-model 模型进行本地转录后，再使用 --diarize-model 模型进行分离
yt-summarize-vedio --diarize "https://www.youtube.com/watch?v=43kikAbL8u8"


```

### 5. 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | YouTube 视频 URL | （必填） |
| `-o, --output` | 输出文件路径 | `./transcript_<timestamp>.txt` |
| `--language` | 语言代码或 `auto` | `auto` |
| `--diarize` | 启用说话人分离 | 启用 |
| `--no-diarize` | 禁用说话人分离 | - |
| `--whisper-model` | Whisper 模型大小 | `turbo` |
| `--diarize-model` | 说话人分离模型 | `pyannote/speaker-diarization-3.1` |
| `--log-level` | 日志级别 | `INFO` |
| `-v, --verbose` | 详细输出 | - |

- **Whisper 模型选项**: tiny, base, small, medium, large, turbo (默认 turbo)
- **说话人分离模型**: 支持 pyannote 官方模型

## 输出格式

### 默认输出（无说话人分离），他根据一句话的长度自动分段

```
[00:00] 在硅谷采访100个有意思的人
[00:02] 同学你好
[00:03] 请你自我介绍一下自己
```

### 启用说话人分离

```
[00:00] [SPEAKER_00] 在硅谷采访100个有意思的人
[00:02] [SPEAKER_01] 同学你好
[00:03] [SPEAKER_00] 请你自我介绍一下自己
```

## 常见问题

### Q: 403 Forbidden 错误？

A: pyannote/speaker-diarization-3.1 是 gated model，需要：
1. 访问 https://hf.co/pyannote/speaker-diarization-3.1 申请访问权限
2. 审核通过后使用 `--no-diarize` 或确保已登录 HuggingFace

### Q: 转录速度慢？

A: 使用更小的 Whisper 模型：
```bash
yt-summarize-vedio "URL" --whisper-model tiny
```

### Q: 模型下载失败？

A: 确保能访问 huggingface.co，或配置代理。

## 运行测试

```bash
cd src && uv venv && source .venv/bin/activate && PYTHONPATH=. python -m pytest ../tests/test_transcribe.py -v
```