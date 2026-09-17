"""Web channel HTTP visibility: access lines and worker-pool snapshots.

A web-console "发送失败" toast used to leave no server-side trace at all: the
stock access log was silenced and handler logs only fire once a request reaches
the app. When the cheroot worker pool is saturated, connections are refused
before any handler runs, so the only way to tell a client/connection failure
apart from a rejected request is the access line (absent = never arrived) plus
the pool snapshot. These tests pin that behavior.
"""

import logging
import threading
from pathlib import Path
from types import SimpleNamespace

from channel.web import web_channel
from channel.web.core._common import _web_access_log

WebChannel = web_channel.WebChannel.__wrapped__


def _messages(caplog):
    return [record.getMessage() for record in caplog.records]


def test_critical_endpoints_log_at_info(caplog):
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="log"):
        for path in ("/message", "/stream", "/upload", "/cancel", "/steer"):
            _web_access_log(None, "200 OK", {
                "PATH_INFO": path,
                "REQUEST_METHOD": "POST",
                "REMOTE_ADDR": "127.0.0.1",
            })
    lines = _messages(caplog)
    assert len(lines) == 5
    for path in ("/message", "/stream", "/upload", "/cancel", "/steer"):
        assert any(f"POST {path} -> 200 OK" in line for line in lines)


def test_non_critical_endpoints_stay_at_debug(caplog):
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="log"):
        _web_access_log(None, "200 OK", {
            "PATH_INFO": "/assets/app.js",
            "REQUEST_METHOD": "GET",
            "REMOTE_ADDR": "127.0.0.1",
        })
    # INFO capture must not contain the static request.
    assert _messages(caplog) == []

    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="log"):
        _web_access_log(None, "200 OK", {
            "PATH_INFO": "/assets/app.js",
            "REQUEST_METHOD": "GET",
            "REMOTE_ADDR": "127.0.0.1",
        })
    assert any("GET /assets/app.js -> 200 OK" in line for line in _messages(caplog))


class _FakePool:
    def __init__(self, idle, queued, max_workers):
        self.idle = SimpleNamespace(qsize=lambda: idle)
        self._queued = queued
        self.max = max_workers

    def qsize(self):
        return self._queued


def _channel(idle, queued, streams=0):
    return SimpleNamespace(
        sse_streams={f"r{i}": object() for i in range(streams)},
        _sse_streams_lock=threading.RLock(),
        _http_server=SimpleNamespace(requests=_FakePool(idle, queued, 120)),
    )


def test_pool_stats_warn_when_no_idle_worker_and_requests_queued(caplog):
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="log"):
        WebChannel._log_pool_stats(_channel(idle=0, queued=3, streams=2))
    lines = _messages(caplog)
    assert len(lines) == 1
    assert "idle=0" in lines[0] and "queued=3" in lines[0]
    assert "sse_streams=2" in lines[0]


def test_pool_stats_stay_quiet_when_healthy(caplog):
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="log"):
        WebChannel._log_pool_stats(_channel(idle=5, queued=0, streams=3))
    assert _messages(caplog) == []


def test_pool_stats_survive_missing_server(caplog):
    # Before startup() runs there is no HTTP server; stats must not raise.
    channel = SimpleNamespace(
        sse_streams={}, _sse_streams_lock=threading.RLock(), _http_server=None
    )
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="log"):
        WebChannel._log_pool_stats(channel)
    assert any("pool stats" in line for line in _messages(caplog))
