"""Tests for ``sensor._parse_programs`` against real sorrisi.com markup.

The fixtures under ``fixtures/`` are full pages saved from sorrisi.com. This
is the most fragile part of the integration: if sorrisi.com changes its
markup, these tests catch it before the sensors silently start returning
"Nessun dato" in production.
"""

from pathlib import Path

from coordinator import CHANNEL_ORDER, SKIP_CHANNELS, _parse_programs

FIXTURES = Path(__file__).parent / "fixtures"
ORA_IN_ONDA = (FIXTURES / "ora_in_onda.html").read_text(encoding="utf-8")
PRIMA_SERATA = (FIXTURES / "prima_serata.html").read_text(encoding="utf-8")


def test_parses_known_channel_from_ora_in_onda():
    result = _parse_programs(ORA_IN_ONDA)
    assert "Rai 1" in result
    assert result["Rai 1"]


def test_parses_multiple_channels():
    result = _parse_programs(ORA_IN_ONDA)
    assert len(result) >= 5


def test_titles_are_non_empty_strings():
    result = _parse_programs(ORA_IN_ONDA)
    for title in result.values():
        assert isinstance(title, str)
        assert title.strip()


def test_orders_known_channels_by_channel_order():
    result = _parse_programs(ORA_IN_ONDA)
    known = [channel for channel in result if channel in CHANNEL_ORDER]
    assert known == sorted(known, key=CHANNEL_ORDER.index)


def test_excludes_skip_channels():
    result = _parse_programs(ORA_IN_ONDA)
    normalized = {channel.upper().replace(" ", "") for channel in result}
    assert normalized.isdisjoint(SKIP_CHANNELS)


def test_parses_prima_serata_fixture():
    result = _parse_programs(PRIMA_SERATA)
    assert "Rai 1" in result
    assert result["Rai 1"]


def test_empty_html_returns_empty_mapping():
    assert _parse_programs("") == {}


def test_malformed_html_does_not_raise():
    assert _parse_programs("<div><not really html") == {}


def test_html_without_expected_markup_returns_empty_mapping():
    assert _parse_programs("<html><body>Pagina di errore</body></html>") == {}
