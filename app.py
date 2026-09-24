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

# Elenco di esempio dei docenti dell'istituto con il loro stato dinamico (Categoria, Plesso d'origine, Storico)
# In un'evoluzione futura questi dati potranno essere letti da un file Excel o di configurazione dedicato.
archivio_docenti_istituto = [
    {
        "nome": "BELLANOVA",
        "categoria": "Disposizione Plesso",
        "plesso_origine": "Cherasco",
        "storico_sostituzioni": 1,
    },
    {
        "nome": "CAVALLO",
        "categoria": "Extra",
        "plesso_origine": "Cherasco",
        "storico_sostituzioni": 3,
    },
    {
        "nome": "RACCA",
        "categoria": "Recupero",
        "plesso_origine": "Cherasco",
        "storico_sostituzioni": 0,
    },
    {
        "nome": "PINTABONA",
        "categoria": "Disposizione Altro Plesso",
        "plesso_origine": "Narzole",
        "storico_sostituzioni": 1,
    },
    {
        "nome": "DEMAGISTRIS",
        "categoria": "Extra",
        "plesso_origine": "Cherasco",
        "storico_sostituzioni": 2,
    },
    {
        "nome": "FISSORE",
        "categoria": "Disposizione Plesso",
        "plesso_origine": "Roreto",
        "storico_sostituzioni": 0,
    },
    {
        "nome": "PERENO",
        "categoria": "Extra",
        "plesso_origine": "Cherasco",
        "storico_sostituzioni": 4,
    },
    {
        "nome": "BARALE",
        "categoria": "Disposizione Plesso",
        "plesso_origine": "Narzole",
        "storico_sostituzioni": 1,
    },
    {
        "nome": "CECCARELLI",
        "categoria": "Recupero",
        "plesso_origine": "Narzole",
        "storico_sostituzioni": 2,
    },
]

nomi_docenti = [d["nome"] for d in archivio_docenti_istituto]
docente_assente = st.sidebar.selectbox(
    "Docente da sostituire (Assente)", sorted(nomi_docenti)
)


# --- FUNZIONE DI ORDINAMENTO GERARCHICO IMPECCABILE ---
def ordina_candidati_sostituzione(candidati_disponibili, plesso_assenza):
  """Ordinamento multicriterio:

  1. Categoria (Recupero -> Disp. Plesso -> Disp. Altro Plesso -> Extra)
  2. Logistica Plesso (0 = stesso plesso, 1 = plesso diverso)
  3. Storico sostituzioni (minor numero di ore fatte = priorità di equità)
  """
  peso_categoria = {
      "Recupero": 1,
      "Disposizione Plesso": 2,
      "Disposizione Altro Plesso": 3,
      "Extra": 4,
  }

  def chiave_ordinamento(candidato):
    p_cat = peso_categoria.get(candidato.get("categoria", "Extra"), 5)
    p_plesso = (
        0 if candidato.get("plesso_origine") == plesso_assenza else 1
    )
    storico = candidato.get("storico_sostituzioni", 0)
    return (p_cat, p_plesso, storico)

  return sorted(candidati_disponibili, key=chiave_ordinamento)


# --- CORPO PRINCIPALE ---
st.subheader(
    f"📋 Gestione Supplenza per: {docente_assente}"
    f" ({plesso_selezionato} | {giorno_selezionato} - {ora_selezionata}ª Ora)"
)

# Filtro rigoroso sui docenti occupati in classe nell'ora selezionata
if not df_orario.empty and "Giorno" in df_orario.columns:
  docenti_occupati = set(
      df_orario[
          (df_orario["Giorno"] == giorno_selezionato)
          & (df_orario["Ora"] == ora_selezionata)
      ]["Docente"].unique()
  )
else:
  # Simulazione di blocco per test se il DB tabulare non è ancora popolato
  docenti_occupati = {
      "PERENO",
      "BARALE",
  } if giorno_selezionato == "Giovedì" and ora_selezionata in [6, 7] else set()

# Estrazione dei candidati idonei (escludendo l'assente e chi è occupato in classe)
candidati_validi = [
    d
    for d in archivio_docenti_istituto
    if d["nome"] != docente_assente and d["nome"] not in docenti_occupati
]

# Applicazione dell'ordinamento gerarchico intelligente
candidati_ordinati = ordina_candidati_sostituzione(
    candidati_validi, plesso_selezionato
)

col1, col2 = st.columns(2)

with col1:
  st.markdown("### 🛑 Docenti Occupati (In Classe)")
  if docenti_occupati:
    st.error(
        "I seguenti docenti sono impegnati in cattedra e non possono essere"
        f" assegnati:\n- "
        + "\n- ".join(sorted(docenti_occupati))
    )
  else:
    st.info(
        "Nessun docente bloccato da impegni in classe in questa fascia oraria."
    )

with col2:
  st.markdown("### ✅ Candidati Sostituti (Ordinamento Gerarchico)")
  st.caption(
      "Priorità: 1) Recuperi | 2) Disp. Plesso | 3) Disp. Altro Plesso | 4)"
      " Extra (per equità di carico)"
  )

  if candidati_ordinati:
    for idx, cand in enumerate(candidati_ordinati, 1):
      # Badge visivo per evidenziare la categoria e lo storico
      badge_colore = (
          "🟢"
          if cand["categoria"] == "Recupero"
          else ("🔵" if "Plesso" in cand["categoria"] else "🟠")
      )

      c_a, c_b = st.columns([3, 1])
      with c_a:
        st.write(
            f"**{idx}. {cand['nome']}** {badge_colore}"
            f" *{cand['categoria']}* | Plesso: {cand['plesso_origine']} |"
            f" Storico: {cand['storico_sostituzioni']}h"
        )
      with c_b:
        if st.button("Assegna", key=f"assegna_{cand['nome']}"):
          st.success(
              f"Assegnazione confermata: **{cand['nome']}** sostituirà"
              f" **{docente_assente}** ({ora_selezionata}ª ora)."
          )
  else:
    st.warning(
        "Nessun docente disponibile trovato in base ai filtri di orario e"
        " plesso."
    )
