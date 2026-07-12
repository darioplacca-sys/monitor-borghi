"""
Invia una email riassuntiva quando vengono trovati e scaricati nuovi atti.
Usa SMTP standard (funziona con Gmail con "password per le app", o altri provider).

Variabili d'ambiente richieste:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
  EMAIL_FROM, EMAIL_TO
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scraper import Atto


def build_email_body(nuovi: list[Atto], salvati: dict) -> str:
    righe = []
    for atto in nuovi:
        n_file = len(salvati.get(atto.id, []))
        righe.append(
            f"[{atto.fonte.upper()}] {atto.tipo} {atto.anno_numero}\n"
            f"  Oggetto: {atto.oggetto}\n"
            f"  Pubblicato dal {atto.data_inizio_pubblicazione} al {atto.data_fine_pubblicazione}\n"
            f"  File scaricati: {n_file}\n"
            f"  Dettaglio: {atto.url_dettaglio}\n"
        )
    return (
        f"Trovati {len(nuovi)} nuovi atti sull'Amministrazione Trasparente del Comune di Borghi:\n\n"
        + "\n".join(righe)
    )


def send_notification(nuovi: list[Atto], salvati: dict) -> None:
    if not nuovi:
        return

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    email_from = os.environ.get("EMAIL_FROM", user)
    email_to = os.environ["EMAIL_TO"]

    msg = MIMEMultipart()
    msg["Subject"] = f"[Borghi Monitor] {len(nuovi)} nuovi atti pubblicati"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.attach(MIMEText(build_email_body(nuovi, salvati), "plain", "utf-8"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

    print(f"Email di notifica inviata a {email_to}")
