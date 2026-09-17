from pathlib import Path

ROOT = Path(__file__).parents[1]


def _console_js() -> str:
    composer = (ROOT / "channel/web/static/js/chat/composer-input.js").read_text(encoding="utf-8")
    send = (ROOT / "channel/web/static/js/chat/send.js").read_text(encoding="utf-8")
    state = (ROOT / "channel/web/static/js/chat/state.js").read_text(encoding="utf-8")
    new_chat = (ROOT / "channel/web/static/js/chat/new-chat.js").read_text(encoding="utf-8")
    sessions = (ROOT / "channel/web/static/js/views/sessions.js").read_text(encoding="utf-8")
    render = (ROOT / "channel/web/static/js/chat/render.js").read_text(encoding="utf-8")
    return composer + "\n" + send + "\n" + state + "\n" + new_chat + "\n" + sessions + "\n" + render


def test_composer_draft_is_saved_per_agent_and_session():
    js = _console_js()
    assert "const DRAFT_KEY_PREFIX = 'cow_draft'" in js
    assert "function activeDraftStorageKey()" in js
    assert "function saveDraft()" in js
    assert "function restoreDraft()" in js
    # Persisted on every keystroke (input handler in composer-input.js).
    assert js.count("saveDraft();") >= 3
    # ...and cleared whenever the composer text is consumed (sendMessage /
    # steerActiveTask each clear chatInput.value; saveDraft follows).
    assert js.count("resetComposerHeight();\n    saveDraft();") >= 1
    # Restored on load and on every session switch / new chat.
    assert js.count("restoreDraft();") >= 3
    assert "localStorage.setItem(activeDraftStorageKey(), value)" in js
    assert "localStorage.getItem(activeDraftStorageKey())" in js


def test_user_messages_offer_a_copy_button():
    js = _console_js()
    assert "copy-msg-btn" in js
    # The shared copy handler reads back the raw text of a user bubble.
    assert "copyBtn.closest('.user-message-group')" in js
    assert "userRoot.dataset.rawContent" in js