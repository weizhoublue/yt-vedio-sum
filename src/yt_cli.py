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
  %(prog)s "URL" --language en --no-diarize
  %(prog)s "URL" -o ./output.txt -v

依赖:
  - ffmpeg: 系统依赖，需单独安装
  - yt-dlp: pip install yt-dlp
  - faster-whisper: pip install faster-whisper
  - pyannote.audio: pip install pyannote.audio (可选，用于说话人分离)
        """
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube 视频 URL"
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件路径 (默认: ./transcript_<timestamp>.txt)"
    )

    parser.add_argument(
        "--language",
        default="auto",
        help="语言代码 (auto 为自动检测，默认: auto)"
    )

    parser.add_argument(
        "--diarize",
        dest="diarize",
        action="store_true",
        default=True,
        help="启用说话人分离 (默认: 启用)"
    )

    parser.add_argument(
        "--no-diarize",
        dest="diarize",
        action="store_false",
        help="禁用说话人分离"
    )

    parser.add_argument(
        "--whisper-model",
        default="turbo",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper 模型大小 (默认: turbo)"
    )

    parser.add_argument(
        "--diarize-model",
        default="pyannote/speaker-diarization-3.1",
        help="说话人分离模型名称 (默认: pyannote/speaker-diarization-3.1)"
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

    args = parser.parse_args()

    if args.verbose:
        args.log_level = "DEBUG"

    if not args.url:
        parser.print_help()
        sys.exit(1)

    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"./transcript_{timestamp}.txt"

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


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def download_audio(url: str, output_path: str) -> str:
    """下载 YouTube 音频"""
    import subprocess

    logger.info(f"📥 [下载] 正在从 YouTube 下载音频: {url}")

    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "opus",
        "--ppa", "ffmpeg:-ac 1 -ar 16000",
        "-o", output_path,
        url
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"音频下载失败: {result.stderr}")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("下载的音频文件为空")

    logger.info(f"✅ [下载] 音频已保存至: {output_path}")
    return output_path


def main():
    """主入口函数"""
    # 延迟导入依赖模块
    from yt_diarize import PYANNOTE_AVAILABLE
    from yt_transcribe import WhisperTranscriber
    from yt_diarize import SpeakerDiarizer

    args = parse_args()

    # 验证 URL
    if not validate_url(args.url):
        sys.exit(1)

    setup_logging(level=args.log_level)

    logger.info("🎬 YouTube 视频转录工具启动")
    logger.info(f"📌 URL: {args.url}")
    logger.info(f"🌐 语言: {args.language}")
    logger.info(f"🎙️ Whisper 模型: {args.whisper_model}")
    logger.info(f"🎯 说话人分离: {'启用' if args.diarize else '禁用'}")
    if args.diarize:
        logger.info(f"🎯 说话人分离模型: {args.diarize_model}")

    if not check_dependencies():
        logger.error("❌ 系统依赖检查失败，请安装 ffmpeg")
        sys.exit(1)

    if args.diarize and not PYANNOTE_AVAILABLE:
        logger.warning("⚠️  pyannote.audio 未安装，将跳过说话人分离")
        args.diarize = False

    timestamp = datetime.now().strftime("%s")
    audio_path = f"/tmp/yt_audio_{timestamp}.opus"

    try:
        audio_path = download_audio(args.url, audio_path)

        logger.info("🎙️ 开始转录...")
        transcriber = WhisperTranscriber(model_size=args.whisper_model)

        transcription_segments = []
        for seg in transcriber.transcribe(audio_path, language=args.language):
            logger.info(f"  [{seg['start_formatted']}] {seg['text']}")
            transcription_segments.append(seg)

        if args.diarize:
            logger.info("🎯 开始说话人分离...")
            diarizer = SpeakerDiarizer(model_name=args.diarize_model)
            diarization_segments = list(diarizer.diarize(audio_path))

            merged = SpeakerDiarizer.merge_transcription_diarization(
                transcription_segments,
                diarization_segments
            )

            output_text = SpeakerDiarizer.format_diarized_output(merged)
        else:
            output_text = WhisperTranscriber.format_output(
                iter(transcription_segments),
                include_speaker=False
            )

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)

        logger.info(f"✅ 完成! 结果已保存至: {args.output}")

    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        sys.exit(1)

    finally:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.debug(f"🧹 已清理临时文件: {audio_path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()