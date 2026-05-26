#!/usr/bin/env python3
"""YouTube 视频转录 CLI 主入口"""
import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yt_utils import setup_logging, check_dependencies, retry


logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="YouTube 视频转录工具 (支持 Speaker Diarization)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "https://www.youtube.com/watch?v=xxx"
  %(prog)s "URL" --language en
  %(prog)s "URL" -o ./my_output

依赖:
  - ffmpeg: 系统依赖，需单独安装
  - yt-dlp: pip install yt-dlp
  - faster-whisper: pip install faster-whisper
        """
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube 视频 URL"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default="./output",
        help="输出目录 (默认: ./output)"
    )

    parser.add_argument(
        "--language",
        default="auto",
        help="语言代码 (auto 为自动检测，默认: auto)"
    )

    parser.add_argument(
        "--whisper-model",
        default="turbo",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper 模型大小 (默认: turbo)"
    )
    parser.add_argument(
        "--diarize",
        action="store_true",
        default=False,
        help="(已废弃) 说话人分离功能已移除"
    )
    parser.add_argument(
        "--diarize-model",
        default="pyannote/speaker-diarization-3.1",
        help="(已废弃) 说话人分离功能已移除"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出 (等价于 --log-level DEBUG)"
    )

    parser.add_argument(
        "--cpu",
        action="store_true",
        help="强制使用 CPU，不使用 GPU"
    )

    args = parser.parse_args()

    if args.verbose:
        args.log_level = "DEBUG"

    if not args.url:
        parser.print_help()
        sys.exit(1)

    return args


def validate_url(url: str) -> bool:
    """验证 URL 是否可访问"""
    import re

    # YouTube URL 模式
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtu\.be/[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
    ]

    for pattern in patterns:
        if re.match(pattern, url):
            # 使用 yt-dlp 验证 URL 是否可访问
            import subprocess
            try:
                result = subprocess.run(
                    ["yt-dlp", "--skip-download", "--flat-playlist", url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return True
                else:
                    logger.error(f"❌ 无法访问 YouTube URL: {result.stderr[:200]}")
                    return False
            except subprocess.TimeoutExpired:
                logger.error("❌ 验证 URL 超时")
                return False
            except FileNotFoundError:
                logger.error("❌ yt-dlp 未安装")
                return False
            except Exception as e:
                logger.error(f"❌ 验证 URL 失败: {e}")
                return False

    logger.error(f"❌ 无效的 YouTube URL 格式: {url}")
    return False


def is_local_audio_file(path: str) -> bool:
    """判断是否为本地音频文件"""
    if not os.path.exists(path):
        return False
    ext = os.path.splitext(path)[1].lower()
    return ext in ['.opus', '.mp3', '.wav', '.m4a', '.flac']


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def download_audio(url: str, output_path: str) -> str:
    """下载 YouTube 音频"""
    import subprocess

    logger.info(f"📥 [下载] 正在从 YouTube 下载音频: {url}")

    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "wav",
        "--postprocessor-args", "ffmpeg:-ac 1 -ar 16000",
        "-o", output_path.replace(".opus", ".wav"),
        url
    ]
    output_path = output_path.replace(".opus", ".wav")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"音频下载失败: {result.stderr}")

    # 调整音频长度到 10 秒的整数倍（pyannote 要求）
    import subprocess
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
    if duration_result.returncode == 0:
        try:
            duration = float(duration_result.stdout.strip())
            target_duration = int((duration // 10 + 1) * 10)
            # 裁剪或填充音频到临时文件，再替换
            import tempfile
            import shutil
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            subprocess.run([
                "ffmpeg", "-y", "-i", output_path,
                "-t", str(target_duration),
                "-ac", "1", "-ar", "16000",
                tmp_path
            ], capture_output=True)
            shutil.move(tmp_path, output_path)
            logger.debug(f"音频已调整至 {target_duration} 秒")
        except Exception as e:
            logger.debug(f"音频调整失败: {e}")

    file_size = os.path.getsize(output_path)
    if file_size == 0:
        raise RuntimeError("下载的音频文件为空")

    size_mb = file_size / (1024 * 1024)
    logger.info(f"✅ [下载] 音频已保存至: {output_path} ({size_mb:.1f} MB)")
    return output_path


def main():
    """主入口函数"""
    from yt_transcribe import WhisperTranscriber

    args = parse_args()

    # 先检查是否是本地文件（避免对本地路径调用 validate_url）
    if is_local_audio_file(args.url):
        setup_logging(level=args.log_level)
    else:
        setup_logging(level=args.log_level)
        if not validate_url(args.url):
            sys.exit(1)

    logger.info("🎬 YouTube 视频转录工具启动")
    logger.info(f"📌 URL: {args.url}")
    logger.info(f"🌐 语言: {args.language}")
    logger.info(f"🎙️ Whisper 模型: {args.whisper_model}")

    if not check_dependencies():
        logger.error("❌ 系统依赖检查失败，请安装 ffmpeg")
        sys.exit(1)

    # 创建输出目录
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_txt = os.path.join(output_dir, "output.txt")
    output_audio = os.path.join(output_dir, "output.wav")

    # 判断是本地文件还是 URL
    input_path = args.url
    if is_local_audio_file(input_path):
        # 本地音频文件
        audio_path = os.path.abspath(input_path)
        file_size = os.path.getsize(audio_path) / (1024 * 1024)
        # 如果源文件和目标文件相同，不复制
        if os.path.abspath(output_audio) != audio_path:
            import shutil
            shutil.copy2(audio_path, output_audio)
            audio_path = output_audio
        logger.info(f"📂 使用本地音频文件: {audio_path} ({file_size:.1f} MB)")
        source_type = f"本地文件: {input_path}"
    elif not validate_url(input_path):
        logger.error("❌ 无效的 YouTube URL")
        sys.exit(1)
    else:
        # 下载 YouTube 音频
        audio_path = download_audio(input_path, output_audio)
        source_type = f"YouTube URL: {input_path}"

    try:
        logger.info("🎙️ 开始转录...")
        device = "cpu" if args.cpu else None
        transcriber = WhisperTranscriber(model_size=args.whisper_model, device=device)

        transcription_segments = []
        for seg in transcriber.transcribe(audio_path, language=args.language):
            logger.info(f"  [{seg['start_formatted']}] {seg['text']}")
            transcription_segments.append(seg)

        output_text = WhisperTranscriber.format_output(
            iter(transcription_segments),
            include_speaker=False
        )

        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(output_text)

        # 生成 readme.md
        readme_path = os.path.join(output_dir, "readme.md")
        readme_content = f"""# 转录结果

## 来源
{source_type}

## 参数
- Whisper 模型: {args.whisper_model}
- 语言: {args.language}
- 输出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 文件
- `output.wav` - 音频文件
- `output.txt` - 转录文本
"""
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        logger.info(f"✅ 完成! 转录结果已保存至: {output_txt}")

    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        sys.exit(1)

    finally:
        # 音频文件保留在输出目录，不删除
        pass


if __name__ == "__main__":
    main()