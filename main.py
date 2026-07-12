"""
Entry point: individua nuovi atti, scarica i PDF, invia notifica email.
Da eseguire schedulato (es. GitHub Actions, cron).
"""
from scraper import run
from downloader import process_atto
from richiesta_accesso import save_richiesta
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

        richiesta_path = save_richiesta(atto)
        print(f"  -> bozza richiesta accesso: {richiesta_path}")

    try:
        send_notification(nuovi, salvati)
    except Exception as e:
        # Un problema con l'email non deve mai far perdere i PDF già scaricati:
        # lo step di commit su GitHub Actions deve poter girare comunque.
        print(f"Attenzione: invio email fallito ({e}), ma i download sono comunque salvati.")


if __name__ == "__main__":
    main()
