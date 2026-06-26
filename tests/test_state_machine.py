from reliability.state_machine import is_valid_task_state, is_valid_task_transition


def test_valid_terminal_state():
    assert is_valid_task_state("completed")


def test_allowed_transition():
    assert is_valid_task_transition("planned", "active")


def test_rejects_invalid_transition_from_completed():
    assert not is_valid_task_transition("completed", "active")
