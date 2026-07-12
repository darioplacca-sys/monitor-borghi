"""
Entry point: individua nuovi atti, scarica i PDF, invia notifica email.
Da eseguire schedulato (es. GitHub Actions, cron).
"""
from scraper import run
from downloader import process_atto
from notifier import send_notification


def main():
    nuovi = run()
    print(f"Trovati {len(nuovi)} nuovi atti.")

    salvati = {}
    for atto in nuovi:
        print(f"Scarico allegati per [{atto.fonte}] {atto.anno_numero} - {atto.oggetto[:70]}")
        paths = process_atto(atto)
        salvati[atto.id] = paths
        for p in paths:
            print(f"  -> {p}")

    send_notification(nuovi, salvati)


if __name__ == "__main__":
    main()
