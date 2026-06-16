from app.core.verification import verify_changes


def test_rejects_unknown_device() -> None:
    decision = verify_changes({"coffee_machine": True})

    assert decision.allowed is False
    assert decision.safe_changes == {}
    assert "coffee_machine" in decision.reason


def test_rejects_non_boolean_value() -> None:
    decision = verify_changes({"hallway_light": "on"})

    assert decision.allowed is False
    assert decision.safe_changes == {}
    assert "hallway_light" in decision.reason


def test_accepts_valid_change() -> None:
    decision = verify_changes({"hallway_light": True})

    assert decision.allowed is True
    assert decision.safe_changes == {"hallway_light": True}
