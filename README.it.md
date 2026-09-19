<img src="logo.png" width="96" alt="TV Guide Multi-Source" align="right">

# TV Guide Multi-Source

**Il palinsesto della TV italiana dentro Home Assistant, con una card che lo mostra come una guida vera.**

[![Validate](https://github.com/iAlias/HomeAssistantTVGuide/actions/workflows/validate.yml/badge.svg)](https://github.com/iAlias/HomeAssistantTVGuide/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41bdf5)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-41bdf5)](https://www.home-assistant.io/)
[![Versione](https://img.shields.io/badge/versione-5.1.0-orange)](custom_components/tv_guide_multi/manifest.json)
[![Licenza](https://img.shields.io/badge/licenza-MIT-green)](LICENSE)

🇬🇧 [Read in English](README.md)

Due sensori — cosa c'è **ora in onda** e cosa c'è **stasera in prima serata** — alimentati dai
palinsesti pubblicati da [TV Sorrisi e Canzoni](https://www.sorrisi.com), con i canali già ordinati
secondo la numerazione italiana del digitale terrestre, e arricchiti con orario di inizio/fine,
genere, locandina e descrizione quando disponibili. Una card Lovelace dedicata trasforma i dati
grezzi in una vera griglia da guida TV, e sensori opzionali sui programmi preferiti possono
attivare automazioni.

---

## Indice

- [Cosa installa](#cosa-installa)
- [Installazione](#installazione)
- [Configurazione della card](#configurazione-della-card)
- [Programmi preferiti](#programmi-preferiti)
- [Personalizzare l'aspetto della card](#personalizzare-laspetto-della-card)
- [Come funziona](#come-funziona)
- [Cose da sapere](#cose-da-sapere)
- [Sviluppo](#sviluppo)
- [Requisiti](#requisiti)
- [Licenza](#licenza)

---

## Cosa installa

| Entità | Stato | Attributi |
|---|---|---|
| `<nome> - Ora in onda` | il programma del primo canale in elenco | `programmi_correnti`: dizionario canale → dati del programma |
| `<nome> - Prima serata` | il programma serale del primo canale | `prima_serata`: dizionario canale → dati del programma |
| `In onda: <preferito>` (binary_sensor, uno per ogni preferito configurato) | acceso quando un programma che corrisponde a quel titolo è in onda ora, su un qualsiasi canale | `canali`: dizionario canale → titolo |

Il valore dello stato è una comodità per le automazioni; **il contenuto vero sta negli attributi**,
dove trovi tutti i canali in una volta, ciascuno con titolo, orario di inizio/fine, genere,
locandina e descrizione (quando sorrisi.com li pubblica). È da lì che la card costruisce la guida.

Le dipendenze (`aiohttp`, `beautifulsoup4`, `async_timeout`) le installa Home Assistant da solo:
non devi toccare niente.

---

## Installazione

### 1. L'integrazione, con HACS

1. HACS → Integrazioni → menù in alto a destra → **Repository personalizzati**
2. Incolla `https://github.com/iAlias/HomeAssistantTVGuide`, categoria **Integration**
3. Installa e riavvia Home Assistant
4. **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** → cerca **TV Guide Multi-Source**
5. Conferma il nome (o personalizzalo): è il prefisso dei due sensori

Si può installare una sola istanza dell'integrazione: interroga un'unica fonte pubblica condivisa.

> **Aggiornamento da una versione precedente alla 5.0.0?** L'integrazione non si configura più via
> `configuration.yaml`. Rimuovi il blocco `sensor: - platform: tv_guide_multi` e aggiungi
> l'integrazione dalla UI come sopra; le entità mantengono lo stesso `unique_id`, quindi cronologia
> e automazioni restano intatte.

### 2. La card

La card **non viene copiata da HACS**, perché sta fuori dalla cartella dell'integrazione: va messa a
mano una volta sola.

1. Copia `www/tv-guide-multi-card.js` dentro la tua cartella `config/www/`
2. **Impostazioni → Dashboard → menù in alto a destra → Risorse → Aggiungi risorsa**
   - URL: `/local/tv-guide-multi-card.js`
   - Tipo: **Modulo JavaScript**
3. Ricarica la pagina con Ctrl+F5

## Configurazione della card

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

`now_entity` e `prime_entity` sono obbligatori; `channels` sceglie e ordina i canali da mostrare
(omettilo e la card userà tutti i canali presenti nei dati dei sensori). La card ha anche un
**editor grafico**: puoi aggiungerla dall'interfaccia e configurarla senza scrivere YAML.

---

## Programmi preferiti

Da **Impostazioni → Dispositivi e servizi → TV Guide Multi-Source → Configura** puoi indicare uno
o più titoli (anche parziali, separati da virgola: es. `Report, Propaganda Live`). Per ciascuno
viene creato un `binary_sensor` che si accende quando quel programma è in onda ora su un
qualsiasi canale — comodo per un'automazione che ti avvisa quando inizia una serie che segui.

---

## Personalizzare l'aspetto della card

Con [card_mod](https://github.com/thomasloven/lovelace-card-mod) puoi cambiare l'aspetto senza
toccare il codice della card:

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

## Come funziona

- Fetch e parsing passano da una piccola interfaccia `ScheduleSource` (`sources.py`); oggi l'unica
  implementazione è `SorrisiSource`, che legge sorrisi.com. Questo lascia la porta aperta a una
  seconda fonte in futuro senza toccare il coordinator o le entità.
- Un unico `DataUpdateCoordinator` scarica insieme le pagine "ora in onda" e "prima serata", ogni
  **10 minuti**, e condivide il risultato tra tutti i sensori.
- Se un aggiornamento torna vuoto — il sintomo reale di un cambio di markup su sorrisi.com — il
  coordinator continua a servire l'ultimo palinsesto letto con successo, invece di far collassare
  subito i sensori su `Nessun dato`.
- Ogni pagina viene analizzata con BeautifulSoup: per ogni intestazione di canale, il coordinator
  individua il blocco del programma corrispondente e ne legge titolo, orario di inizio/fine,
  genere, locandina e descrizione (ciascuno opzionale, a seconda di cosa pubblica sorrisi.com per
  quel programma).
- Alcuni canali (`IRIS`, `CANALE20`, `20`, `20MEDIASET`, `RAI4`) vengono esclusi, e i restanti
  vengono ordinati secondo la numerazione LCN italiana standard (Rai 1, Rai 2, Rai 3, Rete 4,
  Canale 5, Italia 1, La7, TV8, NOVE); tutto ciò che non è in questa lista viene aggiunto in coda.

## Cose da sapere

- **I dati arrivano leggendo un sito, non un'API.** Non esiste un palinsesto pubblico aperto per la
  TV italiana, quindi le pagine di sorrisi.com vengono lette e interpretate. Se i sensori mostrano
  a lungo un programma chiaramente non aggiornato rispetto al vero palinsesto —
  [apri una segnalazione](https://github.com/iAlias/HomeAssistantTVGuide/issues): quasi certamente
  sorrisi.com ha cambiato l'impaginazione e il parser va aggiornato.
- **Una sola fonte oggi, pronta per una seconda.** È stata cercata una vera seconda fonte EPG
  pubblica italiana da usare come fallback, ma i candidati trovati non erano abbastanza affidabili
  (un mirror di terze parti che non rispondeva, un altro servizio limitato a 20 richieste/giorno
  con copertura Italia non confermata) — aggiungerne una in futuro richiede solo
  un'implementazione di `ScheduleSource`.
- **Solo canali italiani.** L'ordinamento segue la numerazione LCN nazionale.
- **Rispetta la fonte.** L'integrazione tiene in memoria i palinsesti invece di riscaricarli a ogni
  controllo: se ne modifichi il funzionamento, evita di trasformare il sito in un bersaglio.

## Sviluppo

```bash
pip install -r requirements_test.txt
pytest -q
```

I test in `tests/` coprono la logica di parsing e di matching contro fixture HTML reali
(`tests/fixtures/`) e una `ScheduleSource` finta — nessuna installazione di Home Assistant
richiesta. Il parsing è il punto più fragile dell'integrazione, perché sorrisi.com può cambiare il
markup in qualsiasi momento.

## Requisiti

- Home Assistant **2024.1.0** o successivo
- Accesso internet in uscita verso `sorrisi.com`
- [HACS](https://hacs.xyz/) (opzionale, per gli aggiornamenti con un clic) oppure installazione manuale

## Licenza

[MIT](LICENSE). I palinsesti appartengono ai rispettivi editori; questa integrazione li mostra per
uso personale dentro la propria istanza di Home Assistant.
