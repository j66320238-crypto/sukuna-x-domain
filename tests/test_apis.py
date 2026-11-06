#!/usr/bin/env python3
"""APIs plugin tests — pure helpers offline (no network needed).

Usage:  python3 tests/test_apis.py   (ya  pytest tests/test_apis.py)
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from plugins.apis import _horo_resolve, _rss_parse, _dns_rows  # noqa: E402

_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test Feed</title>
<item><title><![CDATA[India wins the match &amp; trophy]]></title>
<link>https://example.com/1</link></item>
<item><title>Plain title without CDATA</title>
<link>https://example.com/2</link></item>
<item><title><![CDATA[Third &#8212; story]]></title></item>
</channel></rss>
"""


def test_horo_resolve():
    # western names
    assert _horo_resolve("leo") == "leo"
    assert _horo_resolve("Leo") == "leo"
    assert _horo_resolve("LEO") == "leo"
    # desi names (user demand ke hisaab se)
    assert _horo_resolve("singh") == "leo"
    assert _horo_resolve("mesh") == "aries"
    assert _horo_resolve("makar") == "capricorn"
    assert _horo_resolve("kumbh") == "aquarius"
    assert _horo_resolve("vrishchik") == "scorpio"
    # cleanup: spaces/emoji hata ke bhi
    assert _horo_resolve(" singh! ") == "leo"
    # invalid
    assert _horo_resolve("kumbhkaran") is None
    assert _horo_resolve("") is None
    print("  ✓ horo resolve: western + desi + cleanup + invalid")


def test_rss_parse():
    items = _rss_parse(_SAMPLE_RSS, 10)
    assert len(items) == 3, items
    # CDATA unwrap + html unescape
    assert items[0][0] == "India wins the match & trophy"
    assert items[0][1] == "https://example.com/1"
    # plain title bhi
    assert items[1][0] == "Plain title without CDATA"
    # missing link → empty string, no crash
    assert items[2][1] == ""
    assert items[2][0] == "Third — story"
    # limit
    assert len(_rss_parse(_SAMPLE_RSS, 2)) == 2
    # empty feed
    assert _rss_parse("<rss></rss>") == []
    print("  ✓ rss parse: CDATA + entities + missing link + limit")


def test_dns_rows():
    answers = [
        {"type": 1, "TTL": 300, "data": "142.250.183.206"},
        {"type": 28, "TTL": 60, "data": "2404:6800:4009::"},
        {"type": 5, "TTL": 120, "data": "ghs.googlehosted.com."},
    ]
    rows = _dns_rows(answers)
    assert rows[0] == ("A", "300", "142.250.183.206")
    assert rows[1][0] == "AAAA"
    assert rows[2][0] == "CNAME"
    assert _dns_rows([]) == []
    assert _dns_rows(None) == []
    print("  ✓ dns rows: A/AAAA/CNAME mapping + empty safe")


def main():
    print("── APIs helpers ──")
    test_horo_resolve()
    test_rss_parse()
    test_dns_rows()
    print("\nALL APIS TESTS PASSED ✅")


if __name__ == "__main__":
    main()
