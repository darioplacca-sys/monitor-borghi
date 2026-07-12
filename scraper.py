"""
Monitor Amministrazione Trasparente - Comune di Borghi
Scarica delibere di Giunta/Consiglio e determine appena pubblicate.

Fonte dati: portale Liferay/Maggioli JCityGov (papca-p), tabella HTML statica,
già ordinata dal più recente al meno recente.
"""
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://borghi.trasparenza-valutazione-merito.it"

# Le due liste da monitorare: Delibere (organi politici) e Determine (dirigenti)
SOURCES = {
    "delibere": f"{BASE}/web/trasparenzaj/papca-p/-/papca/igrid/29248478",
    "determine": f"{BASE}/web/trasparenzaj/papca-p/-/papca/igrid/29248477",
}

STATE_FILE = Path(__file__).parent / "state.json"
ARCHIVE_DIR = Path(__file__).parent / "archivio"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BorghiMonitor/1.0; uso personale archiviazione atti pubblici)"
}


@dataclass
class Atto:
    id: str
    fonte: str  # "delibere" | "determine"
    tipo: str  # es. "DELIBERE DI GIUNTA"
    anno_numero: str
    oggetto: str
    data_inizio_pubblicazione: str
    data_fine_pubblicazione: str
    n_allegati: int
    url_dettaglio: str


def load_state() -> set[str]:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text())["visti"])
    return set()


def save_state(visti: set[str]) -> None:
    STATE_FILE.write_text(json.dumps({"visti": sorted(visti)}, ensure_ascii=False, indent=2))


def parse_lista(html: str, fonte: str) -> list[Atto]:
    soup = BeautifulSoup(html, "html.parser")
    atti = []
    for row in soup.select("tr.master-detail-list-line"):
        atto_id = row.get("data-id")
        if not atto_id:
            continue

        categoria = row.select_one("td.categoria")
        sottocategoria = categoria.select_one(".categoria_sottocategoria")
        tipo = sottocategoria.get_text(strip=True) if sottocategoria else categoria.get_text(strip=True)

        anno_numero = row.select_one("td.annonumeroregistrazione").get_text(strip=True)
        oggetto = row.select_one("td.oggetto").get_text(strip=True)

        periodo = row.select_one("td.periodo-pubblicazione")
        date_match = re.findall(r"\d{2}/\d{2}/\d{4}", periodo.get_text(" ", strip=True))
        data_inizio = date_match[0] if len(date_match) > 0 else ""
        data_fine = date_match[1] if len(date_match) > 1 else ""

        badge = row.select_one(".actions .badge")
        n_allegati = int(badge.get_text(strip=True)) if badge else 0

        link = row.select_one("a.master-detail-list-link-a")
        url_dettaglio = link["href"] if link else ""

        atti.append(
            Atto(
                id=atto_id,
                fonte=fonte,
                tipo=tipo,
                anno_numero=anno_numero,
                oggetto=oggetto,
                data_inizio_pubblicazione=data_inizio,
                data_fine_pubblicazione=data_fine,
                n_allegati=n_allegati,
                url_dettaglio=url_dettaglio,
            )
        )
    return atti


def fetch_prima_pagina(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def run() -> list[Atto]:
    """Ritorna la lista degli atti NUOVI trovati in questa esecuzione (non ancora scaricati)."""
    visti = load_state()
    nuovi: list[Atto] = []

    for fonte, url in SOURCES.items():
        html = fetch_prima_pagina(url)
        atti = parse_lista(html, fonte)
        for atto in atti:
            if atto.id not in visti:
                nuovi.append(atto)
        time.sleep(1)  # cortesia verso il server

    if nuovi:
        visti.update(a.id for a in nuovi)
        save_state(visti)

    return nuovi


if __name__ == "__main__":
    nuovi = run()
    print(f"Trovati {len(nuovi)} nuovi atti.")
    for a in nuovi:
        print(f"  [{a.fonte}] {a.tipo} {a.anno_numero} - {a.oggetto[:80]}")
