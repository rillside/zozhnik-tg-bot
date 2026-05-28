import os
import sys

# Устанавливаем env-переменные ДО любых импортов модулей бота
os.environ.setdefault("TOKEN_BOT", "test_token_123")
os.environ.setdefault("MEDIA_STORAGE_CHANNEL_ID", "123456789")


import pytest
from utils.fsm import State
from utils import antispam


@pytest.fixture(autouse=True)
def clear_fsm_state():
    State.user_states.clear()
    yield
    State.user_states.clear()


@pytest.fixture(autouse=True)
def clear_antispam():
    antispam._warned_groups.clear()
    yield
    antispam._warned_groups.clear()
