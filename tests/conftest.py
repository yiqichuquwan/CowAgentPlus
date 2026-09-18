# encoding:utf-8
"""Keep the suite out of the developer's real workspace.

Whatever a test loads config for, ``agent_workspace`` ends up pointing at the
directory the person running the suite actually uses, and anything that resolves
a path without pinning one down writes there: the memory files, the scheduler
store and the tmp directory are all reachable that way.

Only that one key is redirected, and only for the session. Loading the config
outright would be worse than the problem: tests would inherit the developer's
model, language and channel settings, and start passing or failing on them.
"""

import os
import re
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the real `requests` before any test module is collected. Several
# security tests guard their own import with ``if "requests" not in
# sys.modules`` and, when it is missing, install a *partial* stub (only `get`,
# or a few exception types). Collection reaches those modules before anything
# else imports requests, so the stub landed in sys.modules first and stayed
# there for the whole session -- and a tool that later annotates with
# ``requests.Response`` fails to import, taking its tests down with it.
# requests is a hard dependency (requirements.txt), so the real module is
# always importable; loading it here keeps the stub branches from firing.
import requests  # noqa: F401

_WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "channel", "web")


def console_js():
    """Every script the console loads, concatenated in load order.

    console.js was split into a core/ and views/ tree, so a test that wants to
    assert on "the console's code" has to look at all of it. The list comes
    from the page's own script tags rather than a copy here, so it cannot fall
    behind a file being added or reordered.
    """
    from channel.web.core import template

    page = template.render("chat.html")
    parts = []
    # Asset URLs are absolute so they resolve the same from every routed path,
    # and each carries a ?v= stamp, so the name sits between /assets/ and the
    # query rather than between /assets/ and the closing quote.
    for src in re.findall(r'<script defer src="/assets/(js/[^"?]+)(?:\?[^"]*)?"', page):
        with open(os.path.join(_WEB_DIR, "static", src), encoding="utf-8") as f:
            parts.append(f.read())
    return "\n".join(parts)


def web_backend_py():
    """Every Python file behind the web console, concatenated.

    The counterpart of ``console_js()`` for the backend: a test that wants to
    assert on "the console's server code" should not have to know which file a
    handler or helper currently sits in, or the split of web_channel.py would
    break tests that have nothing to do with it. The list is read off the
    directory, so it cannot fall behind a file being added.

    Use this for "is this still wired up" assertions. A test that parses a
    specific structure -- the URL table, a class body -- should keep reading
    the one file it means, so that it fails loudly when that structure moves.
    """
    parts = []
    for dirpath, dirnames, filenames in os.walk(_WEB_DIR):
        dirnames[:] = [d for d in dirnames if d not in ("static", "templates", "tools", "__pycache__")]
        for name in sorted(filenames):
            if name.endswith(".py"):
                with open(os.path.join(dirpath, name), encoding="utf-8") as f:
                    parts.append(f.read())
    return "\n".join(parts)


@pytest.fixture(autouse=True)
def web_stub_carries_a_request_context():
    """Give the fake ``web`` module a ``ctx``, as the real one has.

    Nine test modules install a stub under ``sys.modules["web"]`` when web.py
    has not been imported yet, and which of them gets there first depends on
    the order the run collected. Handlers driven straight from a test read
    ``web.ctx`` for the query string and the request headers -- absent from the
    stubs, so whether a test sees an empty context or an AttributeError came
    down to that order. An empty context is the case the handlers are written
    for; this makes it the case they get.
    """
    web = sys.modules.get("web")
    if web is not None and not hasattr(web, "ctx"):
        web.ctx = {}
        try:
            yield
        finally:
            del web.ctx
    else:
        yield


@pytest.fixture(autouse=True)
def console_template_cache_not_poisoned():
    """Keep one test's mocked ``open`` out of the console's fragment cache.

    ``template`` caches each fragment under its mtime, which nothing in a test
    run disturbs, so a read that happened while ``builtins.open`` was patched
    is held for the rest of the session -- and every later ``render()`` returns
    that test's stand-in markup instead of the page. The cache is an
    optimisation, so dropping it around each test costs a few file reads and
    makes the suite independent of the order it ran in.
    """
    from channel.web.core import template

    template._cache.clear()
    yield
    template._cache.clear()


@pytest.fixture(autouse=True, scope="session")
def workspace_out_of_the_way():
    import config as config_module
    from common import i18n

    with tempfile.TemporaryDirectory(prefix="cow-tests-") as tmp:
        workspace = os.path.join(tmp, "cow")
        real_load = config_module.load_config
        real_lang = i18n.get_language()

        def load_then_redirect():
            real_load()
            config_module.conf()["agent_workspace"] = workspace
            # `load_config` resolves the host's `cow_lang` through i18n and
            # caches it globally (config.py calls i18n.resolve_language). A
            # developer whose config.json says "zh" would therefore flip the
            # language for every test after the first load_config, and modules
            # that pin English (test_feishu_progress_card) start asserting on
            # Chinese. Neutralise it: pin the language that was active when the
            # session started, undoing whatever the host config would set.
            i18n.set_language(real_lang)

        # Applied now for tests that never load, and re-applied after any that
        # do, since loading replaces the value with the real one.
        config_module.conf()["agent_workspace"] = workspace
        config_module.load_config = load_then_redirect

        # Collection imports every test module before this runs, and a module
        # that loads config on import can leave a registry or a store already
        # resolved against the real path. Drop those.
        _forget_resolved_paths()
        try:
            yield workspace
        finally:
            config_module.load_config = real_load
            i18n.set_language(real_lang)


def _forget_resolved_paths():
    from agent.memory import clear_conversation_store_cache
    from agent.memory.config import reset_memory_configs
    from agent.registry import set_agent_registry

    set_agent_registry(None)
    reset_memory_configs()
    clear_conversation_store_cache()
