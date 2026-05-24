# 🚀 yt-vedio-sum

YouTube 视频转录工具，支持自动语音识别。

## 功能特性

| 功能 | 说明 |
|------|------|
| 🎙️ 语音转录 | 使用 Faster-Whisper 进行高精度语音识别 |
| 🌍 多语言支持 | 自动检测语言或手动指定语言代码 |
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

### 2. 模型说明

本项目使用 Faster-Whisper 模型：

- 自动下载，无需授权
- 支持语言：`auto`（自动检测）或 `zh`, `en`, `ja`, `ko`, `es`, `fr`, `de` 等 100+ 种语言

### 3. 使用虚拟环境运行

```bash
cd src && uv venv && source .venv/bin/activate && uv pip install -e .

cd src && uv run python -m yt_cli "https://www.youtube.com/watch?v=43kikAbL8u8"
```

### 4. 安装使用

```bash

# 安装
cd src 
uv cache clean
uv tool install --force .

# 默认， 只使用 --whisper-model 模型进行本地转录
yt-summarize-vedio "https://www.youtube.com/watch?v=43kikAbL8u8"
    # 生成  output/output.opus 下载的音频文件
    # 生成  output/output.txt  转录的文字
    # 生成  output/readme.md   说明转录源

# 可以基于之前下载的音频文件来重新转录
yt-summarize-vedio "./output/output.opus"

# 指定语言. 默认自动检测
yt-summarize-vedio "URL" --language en

# 指定输出目录（默认 ./output）
yt-summarize-vedio "URL" -o ./my_output


```

### 5. 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | YouTube 视频 URL | （必填） |
| `-o, --output-dir` | 输出目录 | `./output` |
| `--language` | 使用什么语言来理解视频，值包括 zh / en / | `auto` |
| `--whisper-model` | Whisper 模型大小 | `turbo` |
| `--log-level` | 日志级别 | `INFO` |
| `-v, --verbose` | 详细输出 | - |

- **Whisper 模型选项**: tiny, base, small, medium, large, turbo (默认 turbo)

## 输出格式

根据一句话的长度自动分段：

```
[00:00] 在硅谷采访100个有意思的人
[00:02] 同学你好
[00:03] 请你自我介绍一下自己
```

## 常见问题

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

### 支持语言

--language    Whisper 支持的语言代码：

  en, zh, de, es, ru, ko, fr, ja, pt, tr, pl, ca, nl, ar, sv, it, id, hi, fi, vi, he, uk, el, ms, cs, ro, da, hu, ta, no, th, ur, hr, bg,
  lt, la, mi, ml, cy, sk, te, fa, lv, bn, sr, az, sl, kn, et, mk, br, eu, is, hy, ne, mn, bs, kk, sq, sw, gl, mr, pa, si, km, sn, yo, so,
  af, oc, ka, be, tg, sd, gu, am, yi, lo, uz, fo, ht, ps, tk, nn, mt, sa, lb, my, bo, tl, mg, as, tt, haw, ln, ha, ba, jw, su, yue

  常用：
  - en - 英语
  - zh - 中文
  - ja - 日语
  - ko - 韩语
  - es - 西班牙语
  - fr - 法语
  - de - 德语

  建议使用 auto（默认），让模型自动检测语言。