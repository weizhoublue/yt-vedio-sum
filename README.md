# 🚀 yt-summarize-vedio

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

### 1. 安装依赖

```bash
cd /Users/weizhoublue/Documents/git/aiAgent/my-exec/yt-summarize-vedio

# 使用 uv（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 2. 系统依赖

- **ffmpeg** - 音频处理（必须）
  ```bash
  # macOS
  brew install ffmpeg

  # Ubuntu/Debian
  sudo apt install ffmpeg
  ```

- **HF_TOKEN** - 说话人分离功能需要（可选）
  ```bash
  export HF_TOKEN=your_huggingface_token
  ```

### 3. 基本用法

```bash
# 使用 uv 运行
uv run python yt_cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 或激活虚拟环境后直接运行
source .venv/bin/activate
./yt-summarize-vedio "URL"
```

### 4. 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | YouTube 视频 URL | （必填） |
| `-o, --output` | 输出文件路径 | `./transcript_<timestamp>.txt` |
| `--language` | 语言代码或 `auto` | `auto` |
| `--diarize` | 启用说话人分离 | 启用 |
| `--no-diarize` | 禁用说话人分离 | - |
| `--log-level` | 日志级别 | `INFO` |
| `-v, --verbose` | 详细输出 | - |

### 5. 使用示例

```bash
# 基本转录（禁用说话人分离）
uv run python yt_cli.py "https://www.youtube.com/watch?v=43kikAbL8u8" --no-diarize

# 指定语言转录
uv run python yt_cli.py "URL" --language en

# 指定输出路径
uv run python yt_cli.py "URL" -o ./my_transcript.txt

# 启用说话人分离（需要 HF_TOKEN）
export HF_TOKEN=your_token
uv run python yt_cli.py "URL" --diarize

# 详细日志输出
uv run python yt_cli.py "URL" -v
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

### Q: 说话人分离功能报错？

A: 需要设置 HuggingFace Token：
```bash
export HF_TOKEN=your_token_here
```

### Q: 转录速度慢？

A: 可以使用更小的模型：
```python
# 在代码中修改 model_size
# tiny (快, 精度低) -> base -> small -> medium -> large -> turbo (慢, 精度高)
transcriber = WhisperTranscriber(model_size="tiny")
```

### Q: GPU 不被识别？

A: 确保安装了支持 CUDA 的 PyTorch：
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## 项目结构

```
yt-summarize-vedio/
├── yt-summarize-vedio    # Shell 入口
├── yt_cli.py             # CLI 主入口
├── yt_transcribe.py      # 转录模块
├── yt_diarize.py         # 说话人分离模块
├── yt_utils.py           # 工具函数
├── pyproject.toml        # 项目配置
└── requirements.txt      # 依赖列表
```