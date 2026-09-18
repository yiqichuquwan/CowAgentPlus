/* Small shared helpers: escaping, time formatting, scrolling.
   Split out of console.js. These are classic scripts sharing one global
   scope; see channel/web/README.md before changing the load order. */

// =====================================================================
// Utilities
// =====================================================================
function formatTime(date) {
    const now = new Date();
    const sameDay = date.getFullYear() === now.getFullYear()
        && date.getMonth() === now.getMonth()
        && date.getDate() === now.getDate();
    const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (sameDay) return time;
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    if (date.getFullYear() === now.getFullYear()) return `${m}-${d} ${time}`;
    return `${date.getFullYear()}-${m}-${d} ${time}`;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function ChannelsHandler_maskSecret(val) {
    if (!val || val.length <= 8) return val;
    return val.slice(0, 4) + '*'.repeat(val.length - 8) + val.slice(-4);
}

function formatToolArgs(args) {
    if (!args || Object.keys(args).length === 0) return '(none)';
    try {
        return escapeHtml(JSON.stringify(args, null, 2));
    } catch (_) {
        return escapeHtml(String(args));
    }
}

const SUBSTEP_ARGS_CHARS = 90;

/** Tool arguments on one line, for a step in a list of dozens. */
function summarizeToolArgs(args) {
    if (!args || typeof args !== 'object') return '';
    const parts = [];
    for (const [key, value] of Object.entries(args)) {
        const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
        parts.push(`${key}=${text}`);
    }
    const joined = parts.join(', ');
    return joined.length > SUBSTEP_ARGS_CHARS
        ? joined.slice(0, SUBSTEP_ARGS_CHARS) + '…'
        : joined;
}

/**
 * Add or settle one step inside a sub agent's card.
 *
 * Silent when the card is gone: a sub agent cancelled on timeout keeps working
 * until its next checkpoint, and steps that arrive after its card closed
 * describe work nobody is waiting on any more.
 */
function renderSubagentStep(toolEl, item) {
    if (!toolEl || !item.step_id) return;
    const section = toolEl.querySelector('.tool-substeps-section');
    const list = toolEl.querySelector('.tool-substeps');
    if (!section || !list) return;

    let stepEl = list.querySelector(`[data-step-id="${CSS.escape(item.step_id)}"]`);
    if (!stepEl) {
        if (item.phase !== 'start') return;
        stepEl = document.createElement('div');
        stepEl.className = 'tool-substep';
        stepEl.dataset.stepId = item.step_id;
        stepEl.innerHTML = `
            <i class="fas fa-circle-notch fa-spin tool-substep-icon"></i>
            <span class="tool-substep-name">${escapeHtml(item.tool || 'tool')}</span>
            <span class="tool-substep-args">${escapeHtml(summarizeToolArgs(item.arguments))}</span>
            <span class="tool-substep-time"></span>`;
        list.appendChild(stepEl);
        section.classList.remove('hidden');
        // The first step is also the first sign of life from a sub agent that
        // runs for minutes, so it opens the card it belongs to.
        toolEl.classList.add('expanded');
        updateSubstepCount(toolEl, list.children.length);
        return;
    }

    if (item.phase !== 'end') return;
    const isError = item.status && item.status !== 'success';
    const icon = stepEl.querySelector('.tool-substep-icon');
    if (icon) {
        icon.className = isError
            ? 'fas fa-times tool-substep-icon tool-substep-failed'
            : 'fas fa-check tool-substep-icon';
    }
    const timeEl = stepEl.querySelector('.tool-substep-time');
    if (timeEl && item.execution_time) timeEl.textContent = `${item.execution_time}s`;
    if (item.error) {
        // A step that failed says so where it happened; the sub agent's report
        // covers what the successful ones found.
        const argsEl = stepEl.querySelector('.tool-substep-args');
        if (argsEl) {
            argsEl.textContent = String(item.error);
            argsEl.classList.add('tool-substep-failed');
        }
        stepEl.title = String(item.error);
    }
}

function updateSubstepCount(toolEl, count) {
    const countEl = toolEl.querySelector('.tool-substep-count');
    if (countEl) countEl.textContent = count === 1 ? '1 step' : `${count} steps`;
}

function scrollChatToBottom(force) {
    if (force || _autoScrollEnabled) {
        if (force) _autoScrollEnabled = true;
        const target = messagesDiv.scrollHeight;
        // Only flag a programmatic scroll when scrollTop will actually change
        // (i.e. a scroll event will fire). Otherwise the flag would go stale
        // and swallow the user's next real scroll-up gesture.
        if (Math.abs(messagesDiv.scrollTop - target) > 1) {
            _programmaticScroll = true;
        }
        messagesDiv.scrollTop = target;
        _lastScrollTop = messagesDiv.scrollTop;
    }
}

function _updateScrollToBottomBtn() {
    const btn = document.getElementById('scroll-to-bottom-btn');
    if (!btn) return;
    const distFromBottom = messagesDiv.scrollHeight - messagesDiv.scrollTop - messagesDiv.clientHeight;
    btn.classList.toggle('hidden', distFromBottom <= _SCROLL_THRESHOLD);
}

function applyHighlighting(container) {
    const root = container || document;
    setTimeout(() => {
        const hljsLib = getHljs();
        root.querySelectorAll('pre code').forEach(block => {
            if (!block.classList.contains('hljs')) {
                hljsLib.highlightElement(block);
            }
        });
        // Add language labels and copy buttons to code blocks
        _addCodeBlockHeaders(root);
    }, 0);
}

// POST /message with a bounded timeout and retries. The backend answers
// /message immediately (it spawns the run and returns a request_id), so a
// request that does not settle quickly is a rejected or hung connection, not a
// slow answer — the exact case that used to surface as an unexplained
// "发送失败" toast. A timeout is reported as 请求超时, and the real status /
// error is logged so the browser console tells the two apart.
const MESSAGE_POST_TIMEOUT_MS = 15000;
const MESSAGE_POST_MAX_RETRIES = 2;
const MESSAGE_POST_RETRY_DELAY_MS = 1000;

function postMessage(body, { tag, onSuccess, onFailure }) {
    function attempt(n) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), MESSAGE_POST_TIMEOUT_MS);
        fetch('/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: controller.signal,
        })
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            clearTimeout(timer);
            if (data && data.status === 'success') {
                onSuccess(data);
            } else {
                console.error(`[${tag}] server rejected the message:`, (data && data.message) || data);
                onFailure('error_send');
            }
        })
        .catch(err => {
            clearTimeout(timer);
            if (err.name === 'AbortError') {
                console.warn(`[${tag}] request timed out after ${MESSAGE_POST_TIMEOUT_MS}ms`);
                onFailure('error_timeout');
                return;
            }
            if (n < MESSAGE_POST_MAX_RETRIES) {
                console.warn(`[${tag}] attempt ${n + 1} failed, retrying...`, err);
                setTimeout(() => attempt(n + 1), MESSAGE_POST_RETRY_DELAY_MS * (n + 1));
                return;
            }
            console.error(`[${tag}] giving up after ${n + 1} attempts:`, err);
            onFailure('error_send');
        });
    }
    attempt(0);
}

