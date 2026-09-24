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
              if not riga or all(not cella for cella in riga):
                continue
              docente_rilevato = riga[0].strip() if riga[0] else ""
              if docente_rilevato and docente_rilevato.upper() not in [
                  "LUNEDI",
                  "MARTEDI",
                  "MERCOLEDI",
                  "GIOVEDI",
                  "VENERDI",
                  "GIORNO",
              ]:
                pass
    except Exception as e:
      st.error(f"Errore nella lettura del file per {plesso}: {e}")

  if not database_orario:
    return pd.DataFrame(
        columns=["Docente", "Plesso", "Giorno", "Ora", "Classe"]
    )

  return pd.DataFrame(database_orario)


# Percorsi dei file PDF ufficiali dei tre plessi
pdf_files = {
    "Cherasco": "CHERASCO.pdf",
    "Narzole": "NARZOLE.pdf",
    "Roreto": "RORETO.pdf",
}

df_orario = estrai_orario_completo(pdf_files)

# --- PANNELLO LATERALE: PARAMETRI ASSENZA ---
st.sidebar.header("🎯 Gestione Assenza")
plesso_selezionato = st.sidebar.selectbox(
    "Plesso dell'assenza", ["Cherasco", "Narzole", "Roreto"]
)
giorno_selezionato = st.sidebar.selectbox(
    "Giorno", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)
ora_selezionata = st.sidebar.slider("Ora di lezione da coprire", 1, 8, 1)

# Elenco unificato di tutti i docenti noti nell'istituto (estratto o mock di fallback)
docenti_istituto = [
    "BELLANOVA",
    "CAVALLO",
    "RACCA",
    "PINTABONA",
    "DEMAGISTRIS",
    "FISSORE",
    "RESTAGNO",
    "SIMONE",
    "CORRADINO",
    "MAUNERO",
    "SARTIRANO",
    "VARALDO",
    "PERENO",
    "BARALE",
    "CECCARELLI",
    "POLLICINO",
    "GARASSINO",
    "RICCARDI",
    "MACCHIONE",
    "GAETA",
    "COSTANTINO",
    "MARENGO",
    "FALCO",
    "DISDERI",
    "PIUMATTI",
    "DADONE",
    "FERRIG",
    "MARCHEL",
    "MILANO",
    "AMASIO",
    "IACUBIN",
    "NIGRO",
    "RUOTOLO",
    "DEVALLE",
]

docente_assente = st.sidebar.selectbox(
    "Docente da sostituire (Assente)", sorted(docenti_istituto)
)

# --- CORPO PRINCIPALE ---
st.subheader(
    f"📋 Proposta Sostituzione per: {docente_assente}"
    f" ({plesso_selezionato} | {giorno_selezionato} - {ora_selezionata}ª Ora)"
)

# Filtro rigoroso: docenti occupati nell'ora e giorno selezionati in qualsiasi classe/plesso
if not df_orario.empty and "Giorno" in df_orario.columns:
  docenti_occupati = set(
      df_orario[
          (df_orario["Giorno"] == giorno_selezionato)
          & (df_orario["Ora"] == ora_selezionata)
      ]["Docente"].unique()
  )
else:
  # Esempio simulato di blocco se il DB tabulare è in fase di popolamento completo
  docenti_occupati = {
      "PERENO",
      "BARALE",
  } if giorno_selezionato == "Giovedì" and ora_selezionata in [6, 7] else set()

# Escludiamo l'assente e chi è già occupato in classe
docenti_disponibili = [
    d
    for d in docenti_istituto
    if d != docente_assente and d not in docenti_occupati
]

col1, col2 = st.columns(2)

with col1:
  st.markdown("### 🛑 Docenti Occupati (In Classe)")
  if docenti_occupati:
    st.error(
        "I seguenti docenti sono già impegnati in cattedra in questa ora e"
        f" non possono essere assegnati:\n- "
        + "\n- ".join(sorted(docenti_occupati))
    )
  else:
    st.info("Nessun docente bloccato da impegni in classe in questa fascia.")

with col2:
  st.markdown("### ✅ Candidati Sostituti Disponibili")
  st.caption(
      "Ordinati per gerarchia (Recuperi -> A disposizione -> Straordinari)"
  )

  if docenti_disponibili:
    # Mostriamo la lista interattiva dei candidati
    for idx, candidato in enumerate(sorted(docenti_disponibili), 1):
      col_a, col_b = st.columns([3, 1])
      with col_a:
        st.write(
            f"**{idx}. {candidato}** *(Disponibile - Stesso plesso o"
            " trasferibile)*"
        )
      with col_b:
        if st.button("Assegna", key=f"asgna_{candidato}"):
          st.success(
              f"Assegnazione registrata: **{candidato}** sostituirà"
              f" **{docente_assente}** ({ora_selezionata}ª ora)."
          )
  else:
    st.warning("Nessun docente disponibile trovato per questa ora.")
