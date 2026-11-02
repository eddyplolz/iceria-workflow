"""The kit's wiki client: it reads, it never writes, and a page that is not JSON counts as down."""

import http.client
import io
import json
import urllib.error

import iceria_wiki
import pytest

BOT_CHECK = (
    "<!DOCTYPE html><html><head><title>Just a moment...</title></head>"
    "<body>Checking your browser before accessing iceria.org.</body></html>"
)


class FakeResponse(io.BytesIO):
    def __init__(self, body: str, content_type="application/json"):
        super().__init__(body.encode("utf-8"))
        self.headers = {"Content-Type": content_type}


class FakeOpener:
    """The network boundary: answers each request from a list, and keeps the requests made."""

    def __init__(self, *answers):
        self.answers, self.requests = list(answers), []

    def open(self, req, timeout=None):
        self.requests.append(req)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def _json(data) -> FakeResponse:
    return FakeResponse(json.dumps(data))


def test_a_write_action_is_refused_before_any_request():
    opener = FakeOpener()
    wiki = iceria_wiki.Wiki(opener=opener)
    write = "ed" + "it"
    with pytest.raises(ValueError, match="read-only"):
        wiki._call("POST", action=write, title="Somewhere", text="x")
    assert opener.requests == []
    assert write not in iceria_wiki.READ_ACTIONS


def test_the_allowlist_holds_only_reads_and_the_login_handshake():
    assert iceria_wiki.READ_ACTIONS == {"query", "expandtemplates", "parse", "login"}


def test_a_bot_check_page_counts_as_unreachable():
    wiki = iceria_wiki.Wiki(opener=FakeOpener(FakeResponse(BOT_CHECK, "text/html")))
    with pytest.raises(iceria_wiki.WikiUnavailable, match="bot check"):
        wiki.get_page("World Standards")


def test_a_network_error_counts_as_unreachable():
    wiki = iceria_wiki.Wiki(opener=FakeOpener(urllib.error.URLError("no route")))
    with pytest.raises(iceria_wiki.WikiUnavailable, match="no route"):
        wiki.get_page("World Standards")


@pytest.mark.parametrize(
    "answer",
    [
        ConnectionResetError(10054, "connection reset by the server"),
        http.client.RemoteDisconnected("closed without a response"),
        http.client.IncompleteRead(b'{"query":'),
        FakeResponse('{"query": {"pages": ['),  # a body cut off part way, labeled JSON
    ],
)
def test_a_dropped_or_cut_off_answer_counts_as_unreachable(answer):
    wiki = iceria_wiki.Wiki(opener=FakeOpener(answer))
    with pytest.raises(iceria_wiki.WikiUnavailable):
        wiki.get_page("World Standards")


def test_get_page_returns_text_and_revision_or_none():
    page = {"title": "Mantua", "revisions": [{"revid": 42, "slots": {"main": {"content": "Hi"}}}]}
    wiki = iceria_wiki.Wiki(
        opener=FakeOpener(
            _json({"query": {"pages": [page]}}),
            _json({"query": {"pages": [{"title": "Nowhere", "missing": True}]}}),
        )
    )
    assert wiki.get_page("Mantua") == {"title": "Mantua", "revid": 42, "text": "Hi"}
    assert wiki.get_page("Nowhere") is None


def test_login_sends_the_token_and_reports_a_refusal():
    opener = FakeOpener(
        _json({"query": {"tokens": {"logintoken": "tok+\\"}}}),
        _json({"login": {"result": "Failed", "reason": "Incorrect username or password"}}),
    )
    pw = "w" * 8  # a stand-in; never the 32-character shape the leak gate looks for
    with pytest.raises(iceria_wiki.LoginFailed, match="Incorrect username") as refused:
        iceria_wiki.Wiki(opener=opener).login("Member@kit", pw)
    assert pw not in str(refused.value)
    body = opener.requests[1].data.decode("ascii")
    assert "lgname=Member%40kit" in body and "lgtoken=tok%2B%5C" in body


def test_a_mac_python_without_certificates_is_told_the_fix():
    # python.org's macOS Python ships without root certificates until its installer step runs;
    # urllib wraps the failure in a URLError.
    import ssl

    refused = urllib.error.URLError(ssl.SSLCertVerificationError(1, "certificate verify failed"))
    wiki = iceria_wiki.Wiki(opener=FakeOpener(refused))
    with pytest.raises(iceria_wiki.WikiUnavailable, match="Install Certificates.command"):
        wiki.get_page("World Standards")


def test_latest_revids_asks_once_for_up_to_50_titles_and_maps_each_back():
    answer = {
        "query": {
            "normalized": [{"from": "world standards", "to": "World Standards"}],
            "pages": [
                {"title": "World Standards", "revisions": [{"revid": 7}]},
                {"title": "Nowhere", "missing": True},
            ],
        }
    }
    opener = FakeOpener(_json(answer))
    wiki = iceria_wiki.Wiki(opener=opener)
    assert wiki.latest_revids(["world standards", "Nowhere"]) == {
        "world standards": 7,
        "Nowhere": None,
    }
    assert len(opener.requests) == 1


def test_latest_revids_splits_more_than_50_titles_into_batches():
    titles = [f"Page {i}" for i in range(51)]

    def pages(batch):
        rows = [{"title": t, "revisions": [{"revid": 1}]} for t in batch]
        return _json({"query": {"pages": rows}})

    opener = FakeOpener(pages(titles[:50]), pages(titles[50:]))
    revids = iceria_wiki.Wiki(opener=opener).latest_revids(titles)
    assert len(opener.requests) == 2 and len(revids) == 51 and set(revids.values()) == {1}


def test_the_default_client_resolves_ipv4_only(monkeypatch):
    # Cloudflare challenges the IPv6 route some VPNs use, so the kit never asks for it
    # (tools/wiki/client.py does the same for the workspace's own client).
    import socket

    families = []

    def fake_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        families.append(family)
        raise socket.gaierror("stop here")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    wiki = iceria_wiki.Wiki("https://www.iceria.org/w/api.php")
    with pytest.raises(iceria_wiki.WikiUnavailable):
        wiki.whoami()
    assert families == [socket.AF_INET]
