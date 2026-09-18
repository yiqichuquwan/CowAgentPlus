"""The pages the browser loads directly, and the assets they pull in.

RootHandler and ChatHandler both serve the console shell -- every in-app
path renders the same page and the frontend router takes it from there.
AssetsHandler serves everything under static/, and decides what may be
cached immutably. PwaFileHandler re-serves two of those files -- the manifest
and the service worker -- from the console root, where the browser requires
them to live.
"""

import json
import mimetypes
import os

import web

from channel.web.core import template
from common import i18n
from common.log import logger


class RootHandler:
    """Where /chat used to live. The console is at / now, so that the address
    bar reads as paths into one app rather than as a page with state after it.
    Kept as a redirect because /chat is what older bookmarks, and the startup
    banner of any running instance, still point at. The query string travels
    with it so a PWA shortcut opened on /chat?view=... does not lose its view."""

    def GET(self):
        query = web.ctx.get('query', '')
        target = '/' + query if query else '/'
        # Relative Location, deliberately: web.py's redirect helpers prepend
        # web.ctx.home, an absolute http:// URL built from HTTP_HOST that
        # downgrades the client when this console is reached through a
        # TLS-terminating reverse proxy. A relative target is resolved by
        # the browser against whatever scheme/host it actually used.
        raise web.HTTPError("303 See Other", {"Location": target}, "")


class HealthHandler:
    # Unauthenticated liveness probe. The desktop shell polls this to know the
    # backend is up; it must never require auth (a set web_password would
    # otherwise make startup hang). Returns no sensitive data.
    def GET(self):
        web.header('Content-Type', 'application/json; charset=utf-8')
        web.header('Cache-Control', 'no-store')
        return json.dumps({"status": "ok"})


class ChatHandler:
    def GET(self):
        # Content-Type must be explicit: behind a reverse proxy that sends
        # X-Content-Type-Options: nosniff, a missing type makes browsers
        # refuse to sniff and render the page as plain text source.
        web.header('Content-Type', 'text/html; charset=utf-8')
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        # The shell pulls its layout, views and modals in from templates/;
        # render() assembles them and stamps every first-party asset with its
        # own mtime, so an upgraded console never runs against cached old
        # scripts while unchanged ones stay cacheable.
        html = template.render('chat.html')
        # Inject the backend-resolved default language for first-load fallback.
        html = html.replace("{{COW_DEFAULT_LANG}}", i18n.get_language())
        return html


class AssetsHandler:
    def GET(self, file_path):  # 修改默认参数
        try:
            # 如果请求是/static/，需要处理
            if file_path == '':
                # 返回目录列表...
                pass

            # This module lives in channel/web/api/, one level below the web
            # root that static/ sits in.
            web_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            static_dir = os.path.join(web_dir, 'static')

            full_path = os.path.normpath(os.path.join(static_dir, file_path))

            # 安全检查：确保请求的文件在static目录内
            if not os.path.abspath(full_path).startswith(os.path.abspath(static_dir)):
                logger.error(f"Security check failed for path: {full_path}")
                raise web.notfound()

            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                # Browsers routinely probe optional asset variants (e.g. a
                # .ttf fallback declared alongside .woff2 in @font-face);
                # logging these as errors floods the console with harmless
                # noise. Keep it at debug level — real misconfigurations
                # will still surface via the network panel.
                logger.debug(f"Static file not found: {full_path}")
                raise web.notfound()

            # 设置正确的Content-Type
            content_type = mimetypes.guess_type(full_path)[0]
            if content_type:
                web.header('Content-Type', content_type)
            else:
                # 默认为二进制流
                web.header('Content-Type', 'application/octet-stream')

            # Without a validator a browser has nothing to cache on, so the
            # console re-downloaded every script, stylesheet, font and logo on
            # every reload. The ETag lets it ask instead, and a hit costs one
            # header rather than the file.
            info = os.stat(full_path)
            etag = '"%x-%x"' % (info.st_mtime_ns, info.st_size)
            web.header('ETag', etag)
            # ctx fields are read defensively: this handler is also driven
            # directly, outside a live request, where ctx is empty.
            if template.is_versioned(file_path) and 'v=' in web.ctx.get('query', ''):
                # render() stamps these with the file's own mtime, so the URL
                # cannot outlive the bytes it names: a changed file is a
                # changed URL. That is what makes it safe to promise the copy
                # never goes stale -- the promise is about this URL, not about
                # this path.
                web.header('Cache-Control', 'public, max-age=31536000, immutable')
            else:
                # Everything else (vendor bundles, fonts, logos) is served off
                # an unstamped URL, so it has to be revalidated. no-cache means
                # "keep it, but ask" -- not "do not keep it".
                web.header('Cache-Control', 'no-cache')
            if web.ctx.get('env', {}).get('HTTP_IF_NONE_MATCH') == etag:
                raise web.notmodified()

            # 读取并返回文件内容
            with open(full_path, 'rb') as f:
                return f.read()

        except web.HTTPError:
            # A 304 or the 404 above, both already handled; re-raise as-is so
            # web.py returns the original status to the client.
            raise
        except Exception as e:
            logger.error(f"Error serving static file: {e}", exc_info=True)
            raise web.notfound()


class PwaFileHandler:
    """Serve the PWA entry files from the console root.

    The service worker has to live at the root (or use a Service-Worker-Allowed
    header) to control /chat; a worker under /assets/ could only ever control
    /assets/. The manifest is kept next to it so it can be fetched without
    touching the auth-guarded API surface. Both files physically live in
    static/ -- this handler is the root-level alias AssetsHandler cannot give.
    """

    _FILES = {
        'manifest.webmanifest': ('manifest.webmanifest', 'application/manifest+json; charset=utf-8'),
        'manifest.en.webmanifest': ('manifest.en.webmanifest', 'application/manifest+json; charset=utf-8'),
        'sw.js': ('sw.js', 'application/javascript; charset=utf-8'),
    }

    def GET(self, filename):
        entry = self._FILES.get(filename)
        if not entry:
            raise web.notfound()
        rel_path, content_type = entry
        # This module lives in channel/web/api/, one level below the web root
        # that static/ sits in.
        web_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_dir = os.path.join(web_dir, 'static')
        full_path = os.path.normpath(os.path.join(static_dir, rel_path))
        if not os.path.abspath(full_path).startswith(os.path.abspath(static_dir)):
            raise web.notfound()
        if not os.path.isfile(full_path):
            raise web.notfound()
        # Always revalidate: an upgraded console must not stay pinned to a
        # stale manifest / service worker from the browser cache.
        web.header('Content-Type', content_type)
        web.header('Cache-Control', 'no-cache')
        with open(full_path, 'rb') as f:
            return f.read()
