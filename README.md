<img src="logo.png" width="96" alt="TV Guide Multi-Source" align="right">

# TV Guide Multi-Source

**Italian TV schedules inside Home Assistant, with a card that shows them as a real programme guide.**

[![Validate](https://github.com/iAlias/HomeAssistantTVGuide/actions/workflows/validate.yml/badge.svg)](https://github.com/iAlias/HomeAssistantTVGuide/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41bdf5)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-41bdf5)](https://www.home-assistant.io/)
[![Version](https://img.shields.io/badge/version-4.1.1-orange)](custom_components/tv_guide_multi/manifest.json)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

🇮🇹 [Leggi in italiano](README.it.md)

Two sensors — what's **on now** and what's **on tonight in prime time** — fed by the schedules
published by [TV Sorrisi e Canzoni](https://www.sorrisi.com), with channels pre-sorted according
to the official Italian digital terrestrial (DTT) numbering. A companion Lovelace card turns the
raw data into a proper TV guide grid.

---

## Contents

- [What it installs](#what-it-installs)
- [Installation](#installation)
- [Card configuration](#card-configuration)
- [Styling the card](#styling-the-card)
- [How it works](#how-it-works)
- [Things worth knowing](#things-worth-knowing)
- [Requirements](#requirements)
- [License](#license)

---

## What it installs

| Entity | State | Attributes |
|---|---|---|
| `<name> - Ora in onda` | the current programme on the first listed channel | `programmi_correnti`: a channel → programme mapping |
| `<name> - Prima serata` | the evening programme on the first listed channel | `prima_serata`: a channel → programme mapping |

The entity state is a convenience for automations; **the real content lives in the attributes**,
where every channel is available at once — that's what the card reads from to build the guide.

Dependencies (`aiohttp`, `beautifulsoup4`, `async_timeout`) are installed automatically by Home
Assistant; there is nothing to install by hand.

---

## Installation

### 1. The integration, via HACS

1. HACS → Integrations → top-right menu → **Custom repositories**
2. Add `https://github.com/iAlias/HomeAssistantTVGuide`, category **Integration**
3. Install, then restart Home Assistant

Then add the sensors to `configuration.yaml`:

```yaml
sensor:
  - platform: tv_guide_multi
    name: "Guida TV"      # optional, used as the prefix for both sensor names
```

Restart again and you'll find `sensor.guida_tv_ora_in_onda` and `sensor.guida_tv_prima_serata`.

### 2. The card

The card **is not copied by HACS**, because it lives outside the integration folder: it has to be
added by hand, once.

1. Copy `www/tv-guide-multi-card.js` into your `config/www/` folder
2. **Settings → Dashboards → top-right menu → Resources → Add resource**
   - URL: `/local/tv-guide-multi-card.js`
   - Type: **JavaScript module**
3. Reload the page with Ctrl+F5

## Card configuration

```yaml
type: custom:tv-guide-multi-card
title: Guida TV
now_entity: sensor.guida_tv_ora_in_onda
prime_entity: sensor.guida_tv_prima_serata
channels:
  - Rai 1
  - Rai 2
  - Rai 3
  - Rete 4
  - Canale 5
  - Italia 1
  - La7
```

`now_entity` and `prime_entity` are required; `channels` picks and orders which channels to
display (omit it and the card falls back to every channel present in the sensor data). The card
also ships a **graphical editor**, so it can be added and configured from the dashboard UI without
writing YAML.

---

## Styling the card

With [card_mod](https://github.com/thomasloven/lovelace-card-mod) you can change the card's look
without touching its code:

```yaml
style: |
  ha-card {
    border-radius: 16px;
    box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.3));
    padding: 12px;
    background: var(--card-background-color);
  }
```

---

## How it works

- A single `DataUpdateCoordinator` fetches both the "now" and "prime time" pages together, once
  every **10 minutes**, and shares the result between the two sensors — 2 downloads per refresh
  instead of 4.
- Each page is parsed with BeautifulSoup: for every channel header, the coordinator locates the
  matching programme block and reads the title.
- A handful of channels (`IRIS`, `CANALE20`, `20`, `20MEDIASET`, `RAI4`) are filtered out, and the
  rest are ordered to match the standard Italian DTT numbering (Rai 1, Rai 2, Rai 3, Rete 4,
  Canale 5, Italia 1, La7, TV8, NOVE); anything not in that list is appended afterwards.

## Things worth knowing

- **The data comes from scraping a page, not from an API.** There is no open public schedule feed
  for Italian TV, so the sorrisi.com pages are fetched and parsed. This works well, but if the
  site's markup changes, the parser needs updating; if the sensors ever show `Nessun dato`, this is
  almost always why — [open an issue](https://github.com/iAlias/HomeAssistantTVGuide/issues).
- **Italian channels only.** The ordering follows the national LCN (logical channel number)
  scheme.
- **Be polite to the source.** The integration caches the schedules instead of re-downloading them
  on every check; if you change how it works, avoid turning the site into a target of frequent
  requests.

## Requirements

- Home Assistant **2024.1.0** or newer
- Outbound internet access to `sorrisi.com`
- [HACS](https://hacs.xyz/) (optional, for one-click updates) or manual installation

## License

[MIT](LICENSE). The schedules themselves belong to their respective publishers; this integration
displays them for personal use within your own Home Assistant instance.
