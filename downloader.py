"""
Scarica gli allegati PDF (versione "non firmata", cioè PDF semplice — non il .p7m
firmato digitalmente) per ogni atto nuovo individuato dallo scraper.
"""
import base64
import re
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper import Atto, ARCHIVE_DIR, HEADERS

ATOB_RE = re.compile(r"atob\('([^']+)'\)")


def slugify(text: str, maxlen: int = 80) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")
    text = re.sub(r"_+", "_", text)
    return text[:maxlen] or "documento"


def extract_download_links(detail_html: str) -> list[dict]:
    """Ritorna una lista di allegati con titolo, descrizione e URL diretto del PDF non firmato."""
    soup = BeautifulSoup(detail_html, "html.parser")
    allegati = []

    for row in soup.select("table.allegati-table tr[data-chiave-allegato]"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        titolo = cells[0].get_text(strip=True)
        descrizione = cells[1].get_text(strip=True)

        pdf_url = None
        for a in cells[2].find_all("a"):
            if a.get("title", "").lower() != "download versione non firmata":
                continue
            onclick = a.get("onclick", "")
            match = ATOB_RE.search(onclick)
            if match:
                pdf_url = base64.b64decode(match.group(1)).decode("utf-8")
                break

        if pdf_url:
            allegati.append({"titolo": titolo, "descrizione": descrizione, "url": pdf_url})

    return allegati


def download_pdf(url: str, dest_path: Path) -> None:
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(resp.content)


def process_atto(atto: Atto) -> list[Path]:
    """Scarica tutti i PDF (non firmati) di un atto. Ritorna i path salvati."""
    resp = requests.get(atto.url_dettaglio, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    allegati = extract_download_links(resp.text)

    anno = atto.anno_numero.split("/")[0] if "/" in atto.anno_numero else "sconosciuto"
    subdir = ARCHIVE_DIR / atto.fonte / anno
    base_name = slugify(f"{atto.anno_numero}_{atto.oggetto}")

    saved = []
    for i, allegato in enumerate(allegati, start=1):
        suffix = f"_{i}" if len(allegati) > 1 else ""
        dest = subdir / f"{base_name}{suffix}.pdf"
        try:
            download_pdf(allegato["url"], dest)
            saved.append(dest)
        except requests.RequestException as e:
            print(f"  ! Errore scaricando allegato di {atto.anno_numero}: {e}")
        time.sleep(0.5)

    return saved


if __name__ == "__main__":
    from scraper import run

    nuovi = run()
    print(f"Trovati {len(nuovi)} nuovi atti da scaricare.")
    for atto in nuovi:
        print(f"[{atto.fonte}] {atto.anno_numero} - {atto.oggetto[:70]}")
        paths = process_atto(atto)
        for p in paths:
            print(f"  -> {p}")
