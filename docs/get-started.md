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

### 方式一：使用 uv tool install（推荐）

```bash
# 全局安装（只需一次）
cd src && uv tool install -e .

# 之后可以直接运行
yt-summarize-vedio "https://www.youtube.com/watch?v=VIDEO_ID"

# 查看帮助
yt-summarize-vedio --help
```

### 方式二：使用虚拟环境

```bash
cd src && uv venv && source .venv/bin/activate && uv pip install -e .
```

### 2. 系统依赖

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
  - 支持大多数现代 NVIDIA 显卡（Maxwell 架构及以上，如 GTX 900 系列、RTX 系列等）
  - Pascal 老旧架构（GTX 1080/1070/1060 等）自动使用低精度模式

  ```bash
  # 检测 CUDA 是否可用
  cd src && uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
  ```

### 2.1 首次使用准备（模型下载）

模型会在首次运行时自动下载，无需手动下载。

确保网络通畅（能访问 huggingface.co）。首次运行后模型会缓存到 `~/.cache/huggingface/` 目录。

> 注意：说话人分离功能（`--diarize`）使用的 pyannote 模型需要在 [HuggingFace](https://huggingface.co/pyannote/speaker-diarization-3.1) 申请访问权限。

### 3. 基本用法

```bash
cd src

# 使用 uv 运行
uv run python -m yt_cli "https://www.youtube.com/watch?v=VIDEO_ID"

uv run python -m yt_cli "https://www.youtube.com/watch?v=43kikAbL8u8"  -o ./output.txt
```

### 4. 命令行参数

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

- **Whisper 模型选项**: tiny, base, small, medium, large, turbo (默认 turbo，精度和速度平衡)
- **说话人分离模型**: 支持 pyannote 官方模型，默认 `pyannote/speaker-diarization-3.1`

### 5. 使用示例

```bash
# 使用 uv tool install 安装后（推荐）
yt-summarize-vedio "https://www.youtube.com/watch?v=43kikAbL8u8" --no-diarize

# 指定语言
yt-summarize-vedio "URL" --language en

# 指定输出路径
yt-summarize-vedio "URL" -o ./my_transcript.txt

# 启用说话人分离
yt-summarize-vedio "URL" --diarize

# 使用更小的模型
yt-summarize-vedio "URL" --whisper-model tiny

# 或者使用虚拟环境
cd src
uv run python -m yt_cli "URL"
```

# 使用更小的 Whisper 模型（更快）
uv run python -m yt_cli "URL" --whisper-model tiny

# 使用不同的说话人分离模型
uv run python -m yt_cli "URL" --diarize-model pyannote/speaker-diarization-3.1

# 详细日志输出
uv run python -m yt_cli "URL" -v

# 运行测试
cd src && uv venv && source .venv/bin/activate && PYTHONPATH=. python -m pytest ../tests/test_transcribe.py -v
```

## 输出格式

### 默认输出（无说话人分离）

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

### Q: 模型首次下载失败？

A: 确保网络通畅，可以访问 huggingface.co。如果访问困难，可能需要配置代理。

### Q: 转录速度慢？

A: 可以使用更小的 Whisper 模型：
```bash
cd src
uv run python -m yt_cli "URL" --whisper-model tiny
```
