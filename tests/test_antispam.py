from utils import antispam


def test_group_not_warned_initially():
    assert antispam.is_group_warned("group_new") is False


def test_group_warned_after_manual_add():
    antispam._warned_groups.add("group_x")
    assert antispam.is_group_warned("group_x") is True


def test_group_not_warned_after_clear():
    antispam._warned_groups.add("group_y")
    antispam._warned_groups.discard("group_y")
    assert antispam.is_group_warned("group_y") is False


def test_different_groups_isolated():
    antispam._warned_groups.add("group_a")
    assert antispam.is_group_warned("group_a") is True
    assert antispam.is_group_warned("group_b") is False


def test_multiple_groups_independent():
    antispam._warned_groups.add("g1")
    antispam._warned_groups.add("g2")
    assert antispam.is_group_warned("g1") is True
    assert antispam.is_group_warned("g2") is True
    assert antispam.is_group_warned("g3") is False
