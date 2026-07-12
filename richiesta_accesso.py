"""
Genera una bozza di richiesta di accesso agli atti per ogni atto nuovo trovato.

Il template è volutamente generico e con placeholder da compilare a mano,
perché il tipo di richiesta più adatto varia caso per caso:

- ACCESSO CIVICO GENERALIZZATO (art. 5, c.2, D.Lgs. 33/2013): chiunque può
  richiederlo, senza dover motivare, salvo i limiti di legge (art. 5-bis).
- ACCESSO DOCUMENTALE (L. 241/1990): richiede un interesse diretto,
  concreto e attuale, e va motivato.

Lo script produce SOLO una bozza: va sempre rivista, integrata con i propri
dati anagrafici/di contatto e la scelta del tipo di accesso più corretto
per quel caso specifico, prima dell'invio.
"""
from pathlib import Path
from datetime import date

from scraper import Atto, ARCHIVE_DIR

RICHIESTE_DIR = ARCHIVE_DIR.parent / "richieste"

TEMPLATE = """\
Alla c.a. Comune di Borghi (FC)
Ufficio Protocollo / Responsabile per la Trasparenza
Piazza Lombardini, 7 - 47030 Borghi (FC)
PEC: comune.borghi@cert.provincia.fc.it

Data: {oggi}

OGGETTO: Richiesta di accesso {tipo_accesso_placeholder} relativa a
{tipo} n. {anno_numero} del {data_atto} - "{oggetto_breve}"

Il/La sottoscritto/a [NOME COGNOME], nato/a a [LUOGO] il [DATA NASCITA],
residente in [INDIRIZZO], codice fiscale [CF], contattabile all'indirizzo
email [EMAIL] / PEC [PEC],

PREMESSO CHE

in data {data_pubblicazione} è stato pubblicato all'Albo Pretorio /
Amministrazione Trasparente del Comune di Borghi il seguente atto:

  Tipo:        {tipo}
  Numero/Anno: {anno_numero}
  Oggetto:     {oggetto}
  Link:        {url_dettaglio}

[[ SCEGLIERE UNA DELLE DUE OPZIONI SOTTO ED ELIMINARE L'ALTRA ]]

--- OPZIONE A: ACCESSO CIVICO GENERALIZZATO (art. 5, c. 2, D.Lgs. 33/2013) ---
CHIEDE

ai sensi e per gli effetti dell'art. 5, comma 2, del D.Lgs. 33/2013,
l'accesso civico generalizzato ai seguenti documenti/dati, ulteriori
rispetto a quanto già pubblicato, relativi all'atto sopra indicato:

  [SPECIFICARE: es. allegati tecnici, relazioni istruttorie, corrispondenza
  citata nell'atto, capitolati, computi metrici, ecc.]

Si precisa che la presente richiesta non necessita di motivazione, ai
sensi della normativa citata.

--- OPZIONE B: ACCESSO DOCUMENTALE (L. 241/1990) ---
CHIEDE

ai sensi degli artt. 22 e ss. della L. 241/1990, l'accesso ai seguenti
documenti amministrativi relativi all'atto sopra indicato:

  [SPECIFICARE i documenti richiesti]

per il seguente motivo, in quanto portatore di un interesse diretto,
concreto e attuale, corrispondente a una situazione giuridicamente
tutelata e collegata al documento:

  [SPECIFICARE LA MOTIVAZIONE - obbligatoria per questo tipo di accesso]

--- FINE OPZIONI ---

Si richiede che i documenti vengano messi a disposizione in formato
elettronico, se disponibili, all'indirizzo email/PEC sopra indicato.

Si resta in attesa di riscontro nei termini di legge (30 giorni per
l'accesso civico generalizzato; di norma 30 giorni anche per l'accesso
documentale, salvo diversi termini regolamentari dell'ente).

Distinti saluti.

[FIRMA]
[NOME COGNOME]
"""


def build_richiesta(atto: Atto) -> str:
    oggetto_breve = atto.oggetto[:80] + ("..." if len(atto.oggetto) > 80 else "")
    return TEMPLATE.format(
        oggi=date.today().strftime("%d/%m/%Y"),
        tipo_accesso_placeholder="[civico generalizzato / documentale - vedi sotto]",
        tipo=atto.tipo,
        anno_numero=atto.anno_numero,
        data_atto=atto.data_inizio_pubblicazione or "[data non disponibile]",
        data_pubblicazione=atto.data_inizio_pubblicazione or "[data non disponibile]",
        oggetto=atto.oggetto,
        oggetto_breve=oggetto_breve,
        url_dettaglio=atto.url_dettaglio,
    )


def save_richiesta(atto: Atto) -> Path:
    anno = atto.anno_numero.split("/")[0] if "/" in atto.anno_numero else "sconosciuto"
    subdir = RICHIESTE_DIR / atto.fonte / anno
    subdir.mkdir(parents=True, exist_ok=True)

    numero = atto.anno_numero.split("/")[-1] if "/" in atto.anno_numero else atto.anno_numero
    dest = subdir / f"richiesta_accesso_{anno}_{numero}_{atto.id}.txt"
    dest.write_text(build_richiesta(atto), encoding="utf-8")
    return dest


if __name__ == "__main__":
    from scraper import run

    nuovi = run()
    for atto in nuovi:
        path = save_richiesta(atto)
        print(f"Bozza richiesta creata: {path}")
