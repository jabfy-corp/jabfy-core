from app.core.prompt_builder import build_state_context, build_user_message


def test_builds_device_state_context() -> None:
    context = build_state_context(
        {"hallway_light": False, "garage_door": True}
    )

    assert context == (
        "Current device state:\n"
        "  hallway_light: OFF\n"
        "  garage_door: ON"
    )


def test_builds_empty_device_state_context() -> None:
    assert build_state_context({}) == "Current device state: all devices are off."


def test_builds_user_message() -> None:
    message = build_user_message("User enters the house", {"hallway_light": False})

    assert "hallway_light: OFF" in message
    assert message.endswith("Situation: User enters the house")
