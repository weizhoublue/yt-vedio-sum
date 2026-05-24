"""转录模块测试"""
import pytest
from unittest.mock import Mock, patch
import os


class TestTranscriber:
    """转录器测试套件"""

    def test_init_with_cpu(self):
        """测试 CPU 模式初始化"""
        from yt_transcribe import WhisperTranscriber

        with patch('yt_transcribe.WhisperModel') as mock_model:
            with patch('yt_transcribe.torch.cuda.is_available', return_value=False):
                transcriber = WhisperTranscriber(model_size="turbo")
                mock_model.assert_called_once_with(
                    'turbo', device='cpu', compute_type='int8'
                )

    def test_init_with_gpu(self):
        """测试 GPU 模式初始化"""
        from yt_transcribe import WhisperTranscriber

        with patch('yt_transcribe.WhisperModel') as mock_model:
            with patch('yt_transcribe.torch.cuda.is_available', return_value=True):
                with patch('yt_transcribe.torch.cuda.get_device_name', return_value="RTX 4090"):
                    transcriber = WhisperTranscriber(model_size="turbo")
                    mock_model.assert_called_once_with(
                        'turbo', device='cuda', compute_type='float16'
                    )

    def test_init_with_pascal_gpu(self):
        """测试 Pascal 架构 GPU 初始化"""
        from yt_transcribe import WhisperTranscriber

        with patch('yt_transcribe.WhisperModel') as mock_model:
            with patch('yt_transcribe.torch.cuda.is_available', return_value=True):
                with patch('yt_transcribe.torch.cuda.get_device_name', return_value="GTX 1080"):
                    transcriber = WhisperTranscriber(model_size="turbo")
                    mock_model.assert_called_once_with(
                        'turbo', device='cuda', compute_type='int8_float16'
                    )

    def test_transcribe_auto_language(self):
        """测试自动语言检测"""
        from yt_transcribe import WhisperTranscriber

        mock_model = Mock()
        mock_segments = [
            Mock(start=0, end=5, text="测试文本"),
            Mock(start=5, end=10, text="第二段文本"),
        ]
        mock_model.transcribe.return_value = (mock_segments, Mock(language="zh", language_probability=0.99))

        with patch('yt_transcribe.WhisperModel', return_value=mock_model):
            with patch('yt_transcribe.torch.cuda.is_available', return_value=False):
                with patch('yt_transcribe.os.path.exists', return_value=True):
                    transcriber = WhisperTranscriber()
                    result = list(transcriber.transcribe("dummy.mp3", language="auto"))

        assert len(result) == 2
        assert result[0]["text"] == "测试文本"

    def test_transcribe_specified_language(self):
        """测试指定语言转录"""
        from yt_transcribe import WhisperTranscriber

        mock_model = Mock()
        mock_segments = [Mock(start=0, end=5, text="Hello world")]
        mock_model.transcribe.return_value = (mock_segments, Mock(language="en", language_probability=0.99))

        with patch('yt_transcribe.WhisperModel', return_value=mock_model):
            with patch('yt_transcribe.torch.cuda.is_available', return_value=False):
                with patch('yt_transcribe.os.path.exists', return_value=True):
                    transcriber = WhisperTranscriber()
                    result = list(transcriber.transcribe("dummy.mp3", language="en"))

        mock_model.transcribe.assert_called_once()
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "en"

    def test_transcribe_with_timestamps(self):
        """测试带时间戳输出"""
        from yt_transcribe import WhisperTranscriber

        mock_model = Mock()
        mock_segments = [
            Mock(start=0, end=5.5, text="第一句"),
            Mock(start=5.5, end=12.3, text="第二句"),
        ]
        mock_model.transcribe.return_value = (mock_segments, Mock(language="zh", language_probability=0.99))

        with patch('yt_transcribe.WhisperModel', return_value=mock_model):
            with patch('yt_transcribe.torch.cuda.is_available', return_value=False):
                with patch('yt_transcribe.os.path.exists', return_value=True):
                    transcriber = WhisperTranscriber()
                    result = list(transcriber.transcribe("dummy.mp3"))

        assert result[0]["start"] == 0
        assert result[0]["start_formatted"] == "00:00"
        assert result[1]["start_formatted"] == "00:05"