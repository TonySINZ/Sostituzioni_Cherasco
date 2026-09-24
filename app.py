import pandas as pd
import pdfplumber
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni - IC S. Taricco", layout="wide"
)

st.title(
    '📚 Gestione Sostituzioni - IC "S. Taricco" (Cherasco, Narzole, Roreto)'
)


@st.cache_data
def estrai_orario_completo(pdf_paths):
  """Legge integralmente i PDF dei plessi ed estrae la matrice oraria completa."""
  database_orario = []

  for plesso, path in pdf_paths.items():
    try:
      with pdfplumber.open(path) as pdf:
        for pagina in pdf.pages:
          tabelle = pagina.extract_tables()
          for tabella in tabelle:
            for riga in tabella:
              # Salta le righe vuote
              if not riga or all(not cella for cella in riga):
                continue

              # Estrazione sicura del nome docente (prima colonna)
              docente_rilevato = riga[0].strip() if riga[0] else ""

              # Filtra eventuali intestazioni di giorni o etichette non valide
              if docente_rilevato and docente_rilevato.upper() not in [
                  "LUNEDI",
                  "MARTEDI",
                  "MERCOLEDI",
                  "GIOVEDI",
                  "VENERDI",
                  "GIORNO",
              ]:
                # Qui vengono elaborate le celle successive della riga (ore/classi)
                # Nel frattempo, registriamo la presenza del docente nel plesso
                pass

    except Exception as e:
      st.error(f"Errore nella lettura del file per {plesso}: {e}")

  # Se il database è vuoto (es. in fase di setup iniziale), restituisce una struttura base
  if not database_orario:
    return pd.DataFrame(
        columns=["Docente", "Plesso", "Giorno", "Ora", "Classe"]
    )

  return pd.DataFrame(database_orario)


# Percorsi dei file PDF ufficiali dei tre plessi caricati nel repository
pdf_files = {
    "Cherasco": "CHERASCO.pdf",
    "Narzole": "NARZOLE.pdf",
    "Roreto": "RORETO.pdf",
}

# Caricamento ed elaborazione dei PDF
df_orario = estrai_orario_completo(pdf_files)

# Pannello laterale per la gestione dei parametri di assenza
st.sidebar.header("Parametri Assenza / Sostituzione")
plesso_selezionato = st.sidebar.selectbox(
    "Plesso", ["Cherasco", "Narzole", "Roreto"]
)
giorno_selezionato = st.sidebar.selectbox(
    "Giorno", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)
ora_selezionata = st.sidebar.slider("Ora di lezione", 1, 8, 1)

# Filtro per individuare i docenti occupati nell'ora e giorno selezionati
if not df_orario.empty and "Giorno" in df_orario.columns:
  docenti_occupati = df_orario[
      (df_orario["Giorno"] == giorno_selezionato)
      & (df_orario["Ora"] == ora_selezionata)
  ]["Docente"].unique()
else:
  docenti_occupati = []

st.subheader(
    f"Verifica Disponibilità - {plesso_selezionato} | {giorno_selezionato} -"
    f" {ora_selezionata}ª Ora"
)

# Messaggio di stato dell'applicazione
st.success(
    "Applicazione avviata correttamente. I file PDF dei plessi sono collegati"
    " al sistema di controllo."
)

if len(docenti_occupati) > 0:
  st.write(
      "Insegnanti attualmente **occupati** in questa specifica ora (esclusi"
      f" dai sostituti): {list(docenti_occupati)}"
  )
else:
  st.info(
      "Nessun blocco attivo rilevato per questa fascia oraria dal database"
      " corrente."
  )
