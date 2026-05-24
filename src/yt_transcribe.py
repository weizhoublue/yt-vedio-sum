"""YouTube 视频转录模块"""
import os
import logging
from typing import Generator, Dict, Any, Optional
from dataclasses import dataclass

# 延迟导入 torch，允许在没有 torch 的环境中运行测试
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from faster_whisper import WhisperModel


logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """转录结果数据类"""
    text: str
    start: float
    end: float
    language: Optional[str] = None
    language_probability: Optional[float] = None


class WhisperTranscriber:
    """Whisper 转录器"""

    def __init__(
        self,
        model_size: str = "turbo",
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ):
        """初始化转录器

        Args:
            model_size: whisper 模型大小 (tiny, base, small, medium, large, turbo)
            device: 设备类型 (cuda, cpu)，自动检测时传 None
            compute_type: 计算精度 (int8, int8_float16, float16, float32)，自动检测时传 None
        """
        self.model_size = model_size
        self.device = device or self._auto_select_device()
        self.compute_type = compute_type or self._auto_select_compute_type()
        self.model = self._load_model()

    def _auto_select_device(self) -> str:
        """自动选择设备"""
        if _TORCH_AVAILABLE and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"🎮 [硬件探测] 发现 GPU 设备: {gpu_name}")
            return "cuda"
        logger.info("💻 [硬件探测] 未检测到 GPU 资源，使用 CPU")
        return "cpu"

    def _auto_select_compute_type(self) -> str:
        """自动选择计算精度"""
        if self.device == "cpu":
            return "int8"

        if not _TORCH_AVAILABLE:
            return "float16"

        # GPU: 根据架构选择
        gpu_name = torch.cuda.get_device_name(0).upper()
        is_pascal = any(x in gpu_name for x in ['1060', '1070', '1080', 'P4', 'P100', 'PASCAL'])

        if is_pascal:
            logger.warning("⚠️  [架构警告] 该显卡属于 Pascal 老旧架构，FP16 算力受限")
            return "int8_float16"

        return "float16"

    def _load_model(self) -> WhisperModel:
        """加载模型"""
        logger.info(f"⚙️  [模型加载] 设备: {self.device}, 精度: {self.compute_type}")

        try:
            model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info(f"✅ [模型加载] {self.model_size} 模型加载成功")
            return model
        except Exception as e:
            logger.error(f"❌ [模型加载失败] {e}")
            # 降级处理
            if self.compute_type == "float16":
                logger.info("🔄 [降级重试] 尝试 int8_float16 精度")
                return WhisperModel(self.model_size, device=self.device, compute_type="int8_float16")
            raise

    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        beam_size: int = 5
    ) -> Generator[Dict[str, Any], None, None]:
        """转录音频

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (auto 为自动检测)
            beam_size: beam size

        Yields:
            转录片段字典
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        logger.info(f"🎙️ [转录] 开始转录: {audio_path}")

        # 确定语言参数
        lang_param = None if language == "auto" else language

        segments, info = self.model.transcribe(
            audio_path,
            language=lang_param,
            beam_size=beam_size
        )

        logger.info(f"🌐 [语言检测] {info.language} (置信度: {info.language_probability:.2%})")

        for segment in segments:
            yield {
                "text": segment.text.strip(),
                "start": segment.start,
                "end": segment.end,
                "language": info.language,
                "language_probability": info.language_probability,
                "start_formatted": self._format_timestamp(segment.start),
                "end_formatted": self._format_timestamp(segment.end),
            }

        logger.info("✅ [转录] 转录完成")

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """格式化时间戳"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def format_output(
        segments: Generator[Dict[str, Any], None, None],
        include_speaker: bool = False,
        speaker_label: str = "SPEAKER"
    ) -> str:
        """格式化输出文本

        Args:
            segments: 转录片段生成器
            include_speaker: 是否包含说话人标签
            speaker_label: 说话人标签前缀

        Returns:
            格式化的文本
        """
        lines = []
        for seg in segments:
            if include_speaker:
                line = f"[{seg['start_formatted']}] [{speaker_label}] {seg['text']}"
            else:
                line = f"[{seg['start_formatted']}] {seg['text']}"
            lines.append(line)

        return "\n".join(lines)


def transcribe_file(
    audio_path: str,
    output_path: str,
    language: str = "auto",
    include_speaker: bool = False,
    speaker_label: str = "SPEAKER"
) -> str:
    """转录文件便捷函数

    Args:
        audio_path: 音频文件路径
        output_path: 输出文件路径
        language: 语言代码
        include_speaker: 是否包含说话人标签
        speaker_label: 说话人标签前缀

    Returns:
        输出的文件路径
    """
    transcriber = WhisperTranscriber()
    segments = list(transcriber.transcribe(audio_path, language=language))

    output_text = WhisperTranscriber.format_output(
        iter(segments),
        include_speaker=include_speaker,
        speaker_label=speaker_label
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    logger.info(f"💾 [保存] 转录结果已保存至: {output_path}")
    return output_path