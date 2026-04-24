import pytest
from unittest.mock import MagicMock
from utils.censorship import checker


@pytest.fixture(autouse=True)
def disable_ai():
    """Отключает AI-цензуру по умолчанию для каждого теста."""
    original = checker.toxicity_checker
    checker.toxicity_checker = None
    yield
    checker.toxicity_checker = original


# ── AI отключён ──────────────────────────────────────────────────────────────

async def test_clean_text_passes():
    assert await checker.censor_check("Привет! Как дела? Всё хорошо.") is True


async def test_banned_word_blocked():
    assert await checker.censor_check("хуй") is False


async def test_banned_phrase_blocked():
    assert await checker.censor_check("иди нахуй") is False


async def test_case_insensitive_word():
    assert await checker.censor_check("ХУЙ") is False


async def test_word_with_punctuation_blocked():
    # re.sub заменяет пунктуацию пробелами, слово всё равно найдётся
    assert await checker.censor_check("хуй!") is False


async def test_empty_string_passes():
    assert await checker.censor_check("") is True


async def test_english_banned_word_blocked():
    assert await checker.censor_check("fuck") is False


async def test_text_with_banned_english_phrase():
    assert await checker.censor_check("fuck you") is False


# ── AI включён (мок) ──────────────────────────────────────────────────────────

async def test_ai_blocks_toxic_text(monkeypatch):
    mock = MagicMock()
    mock.predict.return_value = {"toxicity": 0.95, "severe_toxicity": 0.1}
    monkeypatch.setattr(checker, "toxicity_checker", mock)

    result = await checker.censor_check("обычный текст без запрещённых слов")
    assert result is False


async def test_ai_passes_clean_text(monkeypatch):
    mock = MagicMock()
    mock.predict.return_value = {"toxicity": 0.01, "severe_toxicity": 0.0}
    monkeypatch.setattr(checker, "toxicity_checker", mock)

    result = await checker.censor_check("обычный текст без запрещённых слов")
    assert result is True


async def test_ai_error_fallback(monkeypatch):
    mock = MagicMock()
    mock.predict.side_effect = RuntimeError("model crash")
    monkeypatch.setattr(checker, "toxicity_checker", mock)

    # При ошибке AI функция возвращает True (пропускает текст безопасно)
    result = await checker.censor_check("обычный текст")
    assert result is True


async def test_ai_not_called_when_word_filter_blocks(monkeypatch):
    mock = MagicMock()
    mock.predict.return_value = {"toxicity": 0.0}
    monkeypatch.setattr(checker, "toxicity_checker", mock)

    result = await checker.censor_check("хуй")
    assert result is False
    mock.predict.assert_not_called()
