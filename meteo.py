"""Aggiorna il blocco meteo in index.html (Open-Meteo, gratuito, senza chiave).

Gira ogni mattina da GitHub Actions (.github/workflows/meteo.yml), che poi fa commit e push.
Stessa logica di aggiorna_meteo.py sul PC, ma tocca solo index.html.
Uso:  python meteo.py
"""
import json, re, statistics, sys, urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HTML = Path(__file__).resolve().parent / "index.html"
LAT, LON = 40.7149, -73.9922  # Hotel Richland LES, 5 Allen St
TZ = "America/New_York"
TRIP = [date(2026, 10, 28) + timedelta(days=i) for i in range(8)]
DOW = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
WET_MM = 1.0


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def q(base, **p):
    return base + "?" + "&".join(f"{k}={v}" for k, v in p.items())


def climatology():
    d = get(q("https://archive-api.open-meteo.com/v1/archive", latitude=LAT, longitude=LON,
              start_date="2006-10-20", end_date="2025-11-12", timezone=TZ,
              daily="temperature_2m_max,temperature_2m_min,precipitation_sum"))["daily"]
    rows = list(zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"], d["precipitation_sum"]))
    out = {}
    for day in TRIP:
        win = []
        for t, hi, lo, mm in rows:
            dt = date.fromisoformat(t)
            ref = day.replace(year=dt.year)
            if abs((dt - ref).days) <= 3 and None not in (hi, lo, mm):
                win.append((hi, lo, mm))
        out[day.isoformat()] = {
            "tmax": round(statistics.mean(w[0] for w in win)),
            "tmin": round(statistics.mean(w[1] for w in win)),
            "pp": round(100 * sum(w[2] >= WET_MM for w in win) / len(win)),
        }
    return out


def forecast():
    d = get(q("https://api.open-meteo.com/v1/forecast", latitude=LAT, longitude=LON, timezone=TZ,
              forecast_days=16,
              daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max",
              hourly="precipitation_probability"))
    dl, hr = d["daily"], d["hourly"]
    hours = dict(zip(hr["time"], hr["precipitation_probability"]))
    out = {}
    for i, t in enumerate(dl["time"]):
        vals = [dl[k][i] for k in ("weather_code", "temperature_2m_max", "temperature_2m_min",
                                   "precipitation_probability_max", "precipitation_sum")]
        if None in vals:
            continue
        parts = []
        for a, b in ((8, 13), (13, 18), (18, 23)):
            ps = [hours.get(f"{t}T{h:02d}:00") for h in range(a, b)]
            ps = [p for p in ps if p is not None]
            parts.append(max(ps) if ps else None)
        out[t] = {"src": "prev", "code": vals[0], "tmax": round(vals[1]), "tmin": round(vals[2]),
                  "pp": vals[3], "mm": round(vals[4], 1), "wind": round(dl["wind_speed_10m_max"][i] or 0),
                  "parts": parts}
    return out


def ensemble():
    d = get(q("https://ensemble-api.open-meteo.com/v1/ensemble", latitude=LAT, longitude=LON, timezone=TZ,
              models="gfs05", forecast_days=35,
              daily="temperature_2m_max,temperature_2m_min,precipitation_sum"))["daily"]
    out = {}
    for i, t in enumerate(d["time"]):
        def members(var):
            return [d[k][i] for k in d if k.startswith(var) and d[k][i] is not None]
        hi, lo, mm = members("temperature_2m_max"), members("temperature_2m_min"), members("precipitation_sum")
        if len(hi) < 10 or len(mm) < 10:
            continue
        hi.sort()
        out[t] = {"src": "tend", "tmax": round(statistics.median(hi)), "tmin": round(statistics.median(lo)),
                  "range": [round(hi[len(hi) // 10]), round(hi[-1 - len(hi) // 10])],
                  "pp": round(100 * sum(m >= WET_MM for m in mm) / len(mm)),
                  "mm": round(statistics.median(mm), 1)}
    return out


def build():
    clim, fc = climatology(), forecast()
    try:
        ens = ensemble()
    except Exception as e:  # la tendenza è un di più: se manca si mostra la media storica
        print("Ensemble non disponibile:", e)
        ens = {}
    days = []
    for day in TRIP:
        k = day.isoformat()
        w = fc.get(k) or ens.get(k) or {"src": "clim", **clim[k]}
        if w["src"] == "prev" and (day - datetime.now(ZoneInfo(TZ)).date()).days > 7:
            w = {**w, "far": True}
        days.append({"date": k, **w, "clim": clim[k]})
    now = datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%dT%H:%M")
    return {"upd": now, "days": days}


ICON = {0: "☀️", 1: "🌤", 2: "⛅", 3: "☁️", 45: "🌫", 48: "🌫"}


def icon(w):
    c = w.get("code")
    if c is not None:
        if c in ICON: return ICON[c]
        if c >= 95: return "⛈"
        if c >= 71 and c < 80 or c in (85, 86): return "🌨"
        if c >= 80: return "🌦"
        return "🌧"
    return "🌧" if w["pp"] >= 60 else "🌦" if w["pp"] >= 35 else "⛅"


SRC = {"prev": "previsione", "tend": "tendenza, poco affidabile", "clim": "media storica"}


def main():
    m = build()
    js = "const METEO = " + json.dumps(m, ensure_ascii=False, separators=(",", ":")) + ";"
    html = HTML.read_text(encoding="utf-8")
    html, n = re.subn(r"/\*METEO:START\*/.*?/\*METEO:END\*/", lambda _: f"/*METEO:START*/{js}/*METEO:END*/", html, flags=re.S)
    if n != 1: sys.exit("Marcatori METEO non trovati nell'HTML")
    HTML.write_text(html, encoding="utf-8", newline="\n")
    for w in m["days"]:
        print(w["date"], w["src"], f"{w['tmax']}/{w['tmin']}", f"{w['pp']}%")


if __name__ == "__main__":
    main()
