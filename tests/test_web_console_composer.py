from pathlib import Path

ROOT = Path(__file__).parents[1]


def _console_js() -> str:
    return (ROOT / "channel/web/static/js/console.js").read_text(encoding="utf-8")


def test_composer_draft_is_saved_per_agent_and_session():
    js = _console_js()
    assert "const DRAFT_KEY_PREFIX = 'cow_draft'" in js
    assert "function activeDraftStorageKey()" in js
    assert "function saveDraft()" in js
    assert "function restoreDraft()" in js
    # Persisted on every keystroke...
    assert "updateSteerBtnState();\n    saveDraft();" in js
    # ...and cleared whenever the composer text is consumed.
    assert "resetComposerHeight();\n    saveDraft();" in js
    # Restored on load and on every session switch / new chat.
    assert js.count("restoreDraft();") >= 3
    assert "localStorage.setItem(activeDraftStorageKey(), value)" in js
    assert "localStorage.getItem(activeDraftStorageKey())" in js


def test_user_messages_offer_a_copy_button():
    js = _console_js()
    user_bubble = js.split("function createUserMessageEl")[1].split(
        "function renderToolCallsHtml"
    )[0]
    assert "copy-msg-btn" in user_bubble
    # The shared copy handler reads back the raw text of a user bubble.
    assert "copyBtn.closest('.user-message-group')" in js
    assert "userRoot.dataset.rawContent" in js
