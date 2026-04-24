from utils.fsm import State


def test_set_and_get_state():
    State.set_state(1, "waiting_input", {"key": "value"})
    state, data = State.get_state(1)
    assert state == "waiting_input"
    assert data == {"key": "value"}


def test_get_state_unknown_user():
    state, data = State.get_state(9999)
    assert state is None
    assert data is None


def test_clear_state():
    State.set_state(1, "some_state", None)
    State.clear_state(1)
    state, data = State.get_state(1)
    assert state is None
    assert data is None


def test_clear_nonexistent_user_does_not_raise():
    State.clear_state(9999)


def test_set_data_updates_data_only():
    State.set_state(1, "my_state", "old_data")
    State.set_data(1, "new_data")
    state, data = State.get_state(1)
    assert state == "my_state"
    assert data == "new_data"


def test_set_data_creates_entry_for_unknown_user():
    State.set_data(42, "some_data")
    assert State.get_data_only(42) == "some_data"
    state, _ = State.get_state(42)
    assert state is None


def test_get_data_only_unknown_user():
    assert State.get_data_only(9999) is None


def test_isolation_between_users():
    State.set_state(1, "state_a", "data_a")
    State.set_state(2, "state_b", "data_b")
    state1, data1 = State.get_state(1)
    state2, data2 = State.get_state(2)
    assert state1 == "state_a" and data1 == "data_a"
    assert state2 == "state_b" and data2 == "data_b"


def test_overwrite_state():
    State.set_state(1, "first", "first_data")
    State.set_state(1, "second", "second_data")
    state, data = State.get_state(1)
    assert state == "second"
    assert data == "second_data"


def test_state_supports_complex_data():
    payload = {"step": 3, "items": [1, 2, 3], "nested": {"x": True}}
    State.set_state(1, "complex", payload)
    _, data = State.get_state(1)
    assert data == payload


def test_set_state_with_none_state():
    State.set_state(1, None, "some_data")
    state, data = State.get_state(1)
    assert state is None
    assert data == "some_data"
