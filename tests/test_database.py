import pytest
import aiosqlite
from contextlib import asynccontextmanager

import database
from database import xp_to_level, xp_for_next_level



@pytest.mark.parametrize("xp,xp_per_level,expected_level", [
    (0,   100, 1),
    (1,   100, 1),
    (99,  100, 1),
    (100, 100, 2),
    (199, 100, 2),
    (200, 100, 3),
    (0,   50,  1),
    (49,  50,  1),
    (50,  50,  2),
    (100, 50,  3),
])
def test_xp_to_level(xp, xp_per_level, expected_level):
    assert xp_to_level(xp, xp_per_level) == expected_level


@pytest.mark.parametrize("xp,xp_per_level,expected", [
    (0,   100, 100),
    (1,   100, 99),
    (99,  100, 1),
    (100, 100, 100),
    (150, 100, 50),
    (0,   50,  50),
    (25,  50,  25),
    (49,  50,  1),
    (50,  50,  50),
])
def test_xp_for_next_level(xp, xp_per_level, expected):
    assert xp_for_next_level(xp, xp_per_level) == expected


# Фикстура: in-memory SQLite

@pytest.fixture
async def test_db(monkeypatch):
    """Создаёт изолированную in-memory БД и подменяет get_connection."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")

    @asynccontextmanager
    async def mock_get_connection():
        try:
            yield conn
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            raise e

    monkeypatch.setattr(database, "get_connection", mock_get_connection)
    await database.init_db()
    yield conn
    await conn.close()


XP_REWARDS = {"water_goal": 20, "water_add": 5, "sleep_good": 40}
XP_PER_LEVEL = 100


# Пользователи

async def test_add_and_get_user_status(test_db):
    await database.add_user(1, "alice", "User")
    status = await database.get_user_status(user_id=1)
    assert status == "User"


async def test_add_user_returns_default_status_for_unknown(test_db):
    # Пользователь не существует — должен вернуться 'User' по умолчанию
    status = await database.get_user_status(user_id=9999)
    assert status == "User"


async def test_add_user_idempotent_updates_status(test_db):
    await database.add_user(1, "alice", "User")
    await database.add_user(1, "alice_v2", "Admin")
    status = await database.get_user_status(user_id=1)
    assert status == "Admin"


async def test_is_user_valid_exists(test_db):
    await database.add_user(1, "alice", "User")
    result = await database.is_user_valid(user_id=1)
    assert result is not None


async def test_is_user_valid_not_exists(test_db):
    result = await database.is_user_valid(user_id=9999)
    assert result is None


# Водный трекер

async def test_water_stats_after_goal_set(test_db):
    await database.add_user(1, "alice", "User")
    await database.update_water_goal(1, 2000)
    goal, today = await database.water_stats(1)
    assert goal == 2000
    assert today == 0


async def test_add_water_accumulates(test_db):
    await database.add_user(1, "alice", "User")
    await database.update_water_goal(1, 2000)
    await database.add_water_ml(1, 300)
    await database.add_water_ml(1, 200)
    _, today = await database.water_stats(1)
    assert today == 500


# ── XP и лидерборд ───────────────────────────────────────────────────────────

async def test_add_xp_returns_correct_result(test_db):
    await database.add_user(1, "alice", "User")
    result = await database.add_xp(1, "water_goal", XP_REWARDS, XP_PER_LEVEL)
    assert result["xp_gained"] == 20
    assert result["total_xp"] == 20
    assert result["new_level"] == 1
    assert result["leveled_up"] is False


async def test_add_xp_unknown_action_gives_zero(test_db):
    await database.add_user(1, "alice", "User")
    result = await database.add_xp(1, "nonexistent_action", XP_REWARDS, XP_PER_LEVEL)
    assert result["xp_gained"] == 0


async def test_add_xp_level_up(test_db):
    await database.add_user(1, "alice", "User")
    # Начисляем 40 XP дважды + 20 XP = 100 XP → уровень 2
    await database.add_xp(1, "sleep_good", XP_REWARDS, XP_PER_LEVEL)
    await database.add_xp(1, "sleep_good", XP_REWARDS, XP_PER_LEVEL)
    result = await database.add_xp(1, "water_goal", XP_REWARDS, XP_PER_LEVEL)
    assert result["leveled_up"] is True
    assert result["new_level"] == 2


async def test_get_leaderboard_empty(test_db):
    board = await database.get_leaderboard()
    assert board == []


async def test_get_leaderboard_with_users(test_db):
    await database.add_user(1, "alice", "User")
    await database.add_user(2, "bob", "User")
    await database.add_xp(1, "sleep_good", XP_REWARDS, XP_PER_LEVEL)   # 40 XP
    await database.add_xp(2, "water_goal", XP_REWARDS, XP_PER_LEVEL)   # 20 XP

    board = await database.get_leaderboard()
    assert len(board) == 2
    # Формат: (rank, user_id, username, xp, level)
    assert board[0][0] == 1          # первое место
    assert board[0][1] == 1          # alice (больше XP)
    assert board[1][0] == 2          # второе место
    assert board[1][1] == 2          # bob


async def test_get_user_rank(test_db):
    await database.add_user(1, "alice", "User")
    await database.add_user(2, "bob", "User")
    await database.add_xp(1, "sleep_good", XP_REWARDS, XP_PER_LEVEL)   # 40 XP
    await database.add_xp(2, "water_goal", XP_REWARDS, XP_PER_LEVEL)   # 20 XP

    assert await database.get_user_rank(1) == 1
    assert await database.get_user_rank(2) == 2


async def test_get_user_xp_initial(test_db):
    await database.add_user(1, "alice", "User")
    xp, level = await database.get_user_xp(1)
    assert xp == 0
    assert level == 1


async def test_get_user_xp_after_award(test_db):
    await database.add_user(1, "alice", "User")
    await database.add_xp(1, "water_add", XP_REWARDS, XP_PER_LEVEL)
    xp, level = await database.get_user_xp(1)
    assert xp == 5
    assert level == 1
