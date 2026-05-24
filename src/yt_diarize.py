"""Speaker Diarization 模块"""
import os
import logging
from typing import Generator, Dict, Any, List, Optional
from dataclasses import dataclass

import numpy as np


logger = logging.getLogger(__name__)


try:
    from pyannote.audio import Pipeline
    from pyannote.core import Segment
    PYANNOTE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"pyannote.audio 未安装，Speaker Diarization 功能不可用: {e}")
    PYANNOTE_AVAILABLE = False


@dataclass
class DiarizationResult:
    """说话人分离结果"""
    start: float
    end: float
    speaker: str
    confidence: float


class SpeakerDiarizer:
    """说话人分离器"""

    DEFAULT_MODEL = "pyannote/speaker-diarization-3.1"

    def __init__(
        self,
        model_name: Optional[str] = None
    ):
        """初始化说话人分离器

        Args:
            model_name: 模型名称，默认 pyannote/speaker-diarization-3.1
        """
        if not PYANNOTE_AVAILABLE:
            raise RuntimeError("pyannote.audio 未安装，请运行: pip install pyannote.audio")

        self.model_name = model_name or self.DEFAULT_MODEL
        self._pipeline = None

    @property
    def pipeline(self):
        """懒加载 pipeline"""
        if self._pipeline is None:
            logger.info(f"📥 [模型加载] 正在加载说话人分离模型: {self.model_name}")
            try:
                self._pipeline = Pipeline.from_pretrained(self.model_name)
                logger.info("✅ [模型加载] 说话人分离模型加载成功")
            except Exception as e:
                logger.error(f"❌ [模型加载失败] {e}")
                raise
        return self._pipeline

    def diarize(
        self,
        audio_path: str,
        min_speakers: int = 1,
        max_speakers: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """执行说话人分离

        Args:
            audio_path: 音频文件路径
            min_speakers: 最少说话人数量
            max_speakers: 最多说话人数量

        Yields:
            说话人片段字典
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        logger.info(f"🎯 [说话人分离] 正在处理: {audio_path}")

        try:
            diarization = self.pipeline(
                audio_path,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )

            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                })

            segments.sort(key=lambda x: x["start"])

            unique_speakers = sorted(set(s["speaker"] for s in segments))
            speaker_map = {spk: f"SPEAKER_{i:02d}" for i, spk in enumerate(unique_speakers)}

            for seg in segments:
                seg["speaker_normalized"] = speaker_map[seg["speaker"]]
                yield seg
                logger.debug(f"  [{seg['start']:.1f}-{seg['end']:.1f}] {seg['speaker_normalized']}")

            logger.info(f"✅ [说话人分离] 完成，检测到 {len(unique_speakers)} 位说话人")

        except Exception as e:
            logger.error(f"❌ [说话人分离失败] {e}")
            raise

    @staticmethod
    def format_diarized_output(segments: List[Dict[str, Any]]) -> str:
        """格式化带说话人的输出"""
        lines = []
        for seg in segments:
            start_formatted = f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}"
            speaker = seg.get("speaker_normalized", seg.get("speaker", "UNKNOWN"))
            text = seg.get("text", "")
            line = f"[{start_formatted}] [{speaker}] {text}"
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def merge_transcription_diarization(
        transcription_segments: List[Dict[str, Any]],
        diarization_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并转录和说话人分离结果"""
        result = []

        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_text = trans_seg["text"]

            overlapping_speakers = [
                d["speaker_normalized"]
                for d in diarization_segments
                if d["start"] < trans_end and d["end"] > trans_start
            ]

            if overlapping_speakers:
                speaker = max(set(overlapping_speakers), key=overlapping_speakers.count)
            else:
                speaker = "SPEAKER_00"

            result.append({
                "start": trans_start,
                "end": trans_end,
                "start_formatted": trans_seg.get("start_formatted", ""),
                "end_formatted": trans_seg.get("end_formatted", ""),
                "speaker": speaker,
                "text": trans_text,
            })

        return result


def diarize_file(
    audio_path: str,
    output_path: str,
    transcription_segments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """说话人分离便捷函数"""
    diarizer = SpeakerDiarizer()

    if transcription_segments:
        diarization_segments = list(diarizer.diarize(audio_path))
        merged = SpeakerDiarizer.merge_transcription_diarization(
            transcription_segments,
            diarization_segments
        )
        output_text = SpeakerDiarizer.format_diarized_output(merged)
    else:
        diarization_segments = list(diarizer.diarize(audio_path))
        output_text = SpeakerDiarizer.format_diarized_output([
            {"start": d["start"], "end": d["end"], "speaker_normalized": d["speaker_normalized"], "text": ""}
            for d in diarization_segments
        ])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    logger.info(f"💾 [保存] 说话人分离结果已保存至: {output_path}")
    return output_path