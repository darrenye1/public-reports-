# Automated Equity Research Reports

Institutional-style **English PDF** reports for **Top 20 US mega-caps** (+ optional **BX** extra), plus **Top 20 summary** (PDF + CSV).

**Data source:** [Yahoo Finance](https://finance.yahoo.com/) via `yfinance` (not Google Finance). State is tracked in `reports/.data_state.json`.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Full batch (replace all PDFs + rebuild summary)

```bash
python equity_research.py --batch-top20 --force --replace-old
```

### Smart refresh (recommended for automation)

Only regenerates a ticker when:

- **New financial period** appears in statements (e.g. new quarter), or  
- Last run is older than **7 days** (configurable), or  
- **`--force`** is used  

Does **not** delete existing PDFs for unchanged names.

```bash
python equity_research.py --batch-top20 --refresh-stale --force
```

Options:

```bash
python equity_research.py --batch-top20 --refresh-stale --stale-days 7 --force
```

### Windows Task Scheduler

| Script | Purpose |
|--------|---------|
| `run_daily_refresh.bat` | Daily `--refresh-stale` (checks new earnings period) |
| `run_weekly.bat` | Mondays only; same stale logic |

Full Monday rebuild (optional):

```bash
python equity_research.py --batch-top20 --weekly --force --replace-old
```

### Single company

```bash
python equity_research.py MSFT
```

## Report layout (sell-side inspired)

- **Page header/footer:** Ticker, rating, target, **Data as of**, **Latest financial period**, page X of 2  
- **Investment Highlights:** 3 bullets (rating/target, fundamentals, DCF/risks)  
- Investment thesis, key data, financial table, valuation cross-check, peers  

## Outputs

- `reports/{TICKER}_research.pdf`
- `reports/Top20_Summary.pdf` / `.csv`
- `reports/.data_state.json` — last run, fiscal period, cached summary rows  

## Valuation

Blended **DCF (Simon FCFE) + Comps + Analyst**; outliers excluded. DCF often **0% weight** for growth tech (low FCFE yield).

## Disclaimer

Educational / research only. Not investment advice.
