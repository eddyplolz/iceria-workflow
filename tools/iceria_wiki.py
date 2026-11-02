"""Read pages from the Iceria wiki. Read-only by construction: every call goes through _call, and
_call refuses any API action outside READ_ACTIONS, so the kit cannot post for a member."""

import http.client
import http.cookiejar
import json
import socket
import ssl
import urllib.parse
import urllib.request

API = "https://www.iceria.org/w/api.php"
USER_AGENT = "IceriaContributorKit/0.1 (https://www.iceria.org/wiki/; read-only)"
# login is here only for the handshake that lets a member's own bot password read.
READ_ACTIONS = frozenset({"query", "expandtemplates", "parse", "login"})


def _ipv4_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """socket.create_connection limited to IPv4: Cloudflare challenges the IPv6 route some VPNs
    use (tools/wiki/client.py forces IPv4 for the same reason)."""
    host, port = address
    error = None
    for family, kind, proto, _, addr in socket.getaddrinfo(
        host, port, socket.AF_INET, socket.SOCK_STREAM
    ):
        sock = socket.socket(family, kind, proto)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(addr)
            return sock
        except OSError as e:
            sock.close()
            error = e
    raise error or OSError(f"no IPv4 address for {host}")


class _IPv4Connection(http.client.HTTPConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = _ipv4_connection


class _IPv4SConnection(http.client.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = _ipv4_connection


class _IPv4HTTP(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_IPv4Connection, req)


class _IPv4HTTPS(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_IPv4SConnection, req, context=self._context)


class WikiUnavailable(Exception):
    """The wiki could not answer: network down, an HTTP error, an API error or a bot check."""


class LoginFailed(Exception):
    """The wiki answered and refused the bot password."""


class Wiki:
    source = "live"

    def __init__(self, api: str = API, opener=None):
        self.api = api
        self.opener = opener or urllib.request.build_opener(
            _IPv4HTTP,
            _IPv4HTTPS,
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )

    def _call(self, method: str, **params) -> dict:
        action = params.get("action")
        if action not in READ_ACTIONS:
            raise ValueError(f"the kit is read-only; it never sends action={action}")
        params.update(format="json", formatversion="2")
        data = urllib.parse.urlencode(params)
        if method == "GET":
            req = urllib.request.Request(f"{self.api}?{data}")
        else:
            req = urllib.request.Request(self.api, data=data.encode("ascii"))
        req.add_header("User-Agent", USER_AGENT)
        try:
            with self.opener.open(req, timeout=60) as resp:
                kind = resp.headers.get("Content-Type", "")
                body = resp.read()
        # OSError covers URLError, timeouts and a reset connection; HTTPException a reply cut off
        # mid-read.
        except (OSError, http.client.HTTPException) as e:
            if isinstance(getattr(e, "reason", e), ssl.SSLCertVerificationError):
                # python.org's macOS Python has no root certificates until its installer step runs.
                raise WikiUnavailable(
                    f"{self.api}: this Python cannot check the wiki's certificate. On a Mac, open "
                    "Applications > Python 3.x and double-click Install Certificates.command, "
                    "then run the command again. Elsewhere, a network that inspects secure "
                    "traffic (a school or office proxy) can cause this; try another network."
                ) from e
            raise WikiUnavailable(f"{self.api}: {e!r}") from e
        if "json" not in kind:
            raise WikiUnavailable(
                f"{self.api} answered with {kind or 'no type'}, not JSON: a bot check or an error "
                "page. Try again later, or open the wiki in a browser once."
            )
        try:
            out = json.loads(body)
        except ValueError as e:  # JSONDecodeError, and a body that is not UTF-8
            raise WikiUnavailable(f"{self.api} sent a cut-off or broken answer: {e}") from e
        if "error" in out:
            raise WikiUnavailable(f"{action}: {out['error'].get('info', out['error'])}")
        return out

    def login(self, user: str, password: str):
        token = self._call("GET", action="query", meta="tokens", type="login")
        token = token["query"]["tokens"]["logintoken"]
        out = self._call("POST", action="login", lgname=user, lgpassword=password, lgtoken=token)
        if out["login"]["result"] != "Success":
            raise LoginFailed(out["login"].get("reason", out["login"]["result"]))

    def whoami(self) -> dict:
        q = self._call("GET", action="query", meta="userinfo", uiprop="groups|rights")
        return q["query"]["userinfo"]

    def get_page(self, title: str) -> dict | None:
        """{title, revid, text} of the page's current revision, or None when there is no page."""
        q = self._call(
            "GET",
            action="query",
            prop="revisions",
            titles=title,
            rvslots="main",
            rvprop="ids|content",
        )
        page = q["query"]["pages"][0]
        if page.get("missing") or "revisions" not in page:
            return None
        rev = page["revisions"][0]
        return {
            "title": page["title"],
            "revid": rev["revid"],
            "text": rev["slots"]["main"]["content"],
        }

    def latest_revids(self, titles: list[str]) -> dict[str, int | None]:
        """{title: current revid, or None when there is no page} for each title as given, in
        batches of 50 (the API's limit for a visitor). A redirect is not followed: its own
        revision is the one a copy records."""
        out = {}
        for i in range(0, len(titles), 50):
            batch = titles[i : i + 50]
            q = self._call(
                "GET", action="query", prop="revisions", titles="|".join(batch), rvprop="ids"
            )["query"]
            to = {n["from"]: n["to"] for n in q.get("normalized", [])}
            live = {
                p["title"]: p["revisions"][0]["revid"] if "revisions" in p else None
                for p in q["pages"]
            }
            out.update({t: live.get(to.get(t, t)) for t in batch})
        return out

    def categories_exist(self, names: list[str]) -> dict[str, bool]:
        """{name: True when the category exists} for each name without "Category:", in batches
        of 50. A category with members but no page of its own still exists."""
        out = {}
        for i in range(0, len(names), 50):
            batch = names[i : i + 50]
            q = self._call(
                "GET",
                action="query",
                prop="categoryinfo",
                titles="|".join(f"Category:{n}" for n in batch),
            )["query"]
            to = {n["from"]: n["to"] for n in q.get("normalized", [])}
            live = {p["title"]: "categoryinfo" in p or not p.get("missing") for p in q["pages"]}
            out.update(
                {n: live.get(to.get(f"Category:{n}", f"Category:{n}"), False) for n in batch}
            )
        return out

    def expand(self, text: str) -> str:
        q = self._call("GET", action="expandtemplates", text=text, prop="wikitext")
        return q["expandtemplates"]["wikitext"]
