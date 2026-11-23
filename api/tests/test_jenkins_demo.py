"""Demo test used to show a failing Jenkins build (to be reverted)."""


def test_jenkins_demo_failure() -> None:
    """Fail on purpose so Jenkins reports a red build."""
    assert 1 + 1 == 3
