import json

from channel.feishu.feishu_static_card import (
    build_card_delivery,
    build_text_delivery,
    contains_markdown,
)


def test_plain_text_keeps_native_feishu_text_message():
    msg_type, content = build_text_delivery("hello from CowAgent")

    assert msg_type == "text"
    assert json.loads(content) == {"text": "hello from CowAgent"}


def test_markdown_reply_uses_card_2_markdown_element():
    msg_type, content = build_text_delivery("**Build complete**\n\n- tests passed")

    card = json.loads(content)
    assert msg_type == "interactive"
    assert card["schema"] == "2.0"
    assert card["body"]["elements"] == [
        {"tag": "markdown", "content": "**Build complete**\n\n- tests passed"}
    ]


def test_force_card_renders_plain_text_as_card():
    msg_type, content = build_text_delivery("hello from CowAgent", force_card=True)

    card = json.loads(content)
    assert msg_type == "interactive"
    assert card["body"]["elements"] == [
        {"tag": "markdown", "content": "hello from CowAgent"}
    ]


def test_build_card_delivery_wraps_any_text():
    msg_type, content = build_card_delivery("- [ ] ship the release")

    card = json.loads(content)
    assert msg_type == "interactive"
    assert card["schema"] == "2.0"
    assert card["body"]["elements"] == [
        {"tag": "markdown", "content": "- [ ] ship the release"}
    ]


def test_markdown_detection_avoids_common_plain_text_punctuation():
    assert contains_markdown("release 1.2.0 - all checks passed") is False
    assert contains_markdown("Use `cow --help` for details") is True
    assert contains_markdown("| Item | State |\n| --- | --- |\n| API | ready |") is True
