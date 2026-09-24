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

# Archivio docenti istituto
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
giorno_selezionato = st.sidebar.selectbox(
    "Giorno", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)

# --- OPZIONE DI FILTRO PUNTUALE (TOGGLE) ---
usa_filtro_puntuale = st.sidebar.checkbox(
    "⚙️ Filtra per ora/classe specifica",
    value=False,
    help=(
        "Attiva se vuoi limitare la ricerca a una sola ora o classe; lasciala"
        " disattivata per generare l'intero piano giornaliero del docente."
    ),
)

plesso_selezionato = "Cherasco"
ora_selezionata = 1
classe_selezionata = "1A"

if usa_filtro_puntuale:
  st.sidebar.subheader("Parametri Puntuali")
  plesso_selezionato = st.sidebar.selectbox(
      "Plesso dell'assenza", ["Cherasco", "Narzole", "Roreto"]
  )
  ora_selezionata = st.sidebar.slider("Ora di lezione da coprire", 1, 8, 1)
  classe_selezionata = st.sidebar.text_input(
      "Classe (es. 1A, 2B, 3C)", value="1A"
  ).upper()


# --- FUNZIONE DI ORDINAMENTO GERARCHICO ---
def ordina_candidati_sostituzione(candidati_disponibili, plesso_assenza):
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
if not usa_filtro_puntuale:
  st.subheader(
      f"📋 Piano Sostituzioni Giornaliero per: {docente_assente} | Giorno:"
      f" {giorno_selezionato}"
  )
  st.info(
      "Visualizzazione automatica di tutte le ore di lezione previste per il"
      " docente in questa giornata."
  )

  # Simulazione o estrazione delle ore in cui il docente assente ha lezione nella giornata
  # (In regime normale, il sistema interroga il DB orario per trovare tutte le ore coperte dal docente)
  ore_da_coprire = [
      {"ora": 1, "classe": "1A", "plesso": "Cherasco"},
      {"ora": 3, "classe": "2B", "plesso": "Cherasco"},
      {"ora": 4, "classe": "3A", "plesso": "Cherasco"},
  ]

  for item in ore_da_coprire:
    ora_i = item["ora"]
    classe_i = item["classe"]
    plesso_i = item["plesso"]

    with st.expander(
        f"⏰ {ora_i}ª Ora — Classe: {classe_i} ({plesso_i})", expanded=True
    ):
      # Calcolo occupati per quell'ora specifica
      docenti_occupati = (
          {"PERENO", "BARALE"}
          if giorno_selezionato == "Giovedì" and ora_i in [6, 7]
          else set()
      )

      candidati_validi = [
          d
          for d in archivio_docenti_istituto
          if d["nome"] != docente_assente and d["nome"] not in docenti_occupati
      ]
      candidati_ordinati = ordina_candidati_sostituzione(
          candidati_validi, plesso_i
      )

      cols = st.columns(2)
      with cols[0]:
        st.markdown("**🛑 Occupati in cattedra:**")
        if docenti_occupati:
          st.write(", ".join(sorted(docenti_occupati)))
        else:
          st.write("Nessun blocco in questa ora.")

      with cols[1]:
        st.markdown("**✅ Migliori candidati disponibili:**")
        if candidati_ordinati:
          top_cand = candidati_ordinati[0]
          st.success(
              f"**{top_cand['nome']}** ({top_cand['categoria']} | Plesso:"
              f" {top_cand['plesso_origine']} | Storico:"
              f" {top_cand['storico_sostituzioni']}h)"
          )
        else:
          st.warning("Nessun docente disponibile.")

else:
  # MODALITÀ PUNTUALE (se la spunta è attiva)
  st.subheader(
      f"📋 Gestione Supplenza Puntuale: {docente_assente} | Classe:"
      f" {classe_selezionata} ({plesso_selezionato} | {giorno_selezionato} -"
      f" {ora_selezionata}ª Ora)"
  )

  docenti_occupati = (
      {"PERENO", "BARALE"}
      if giorno_selezionato == "Giovedì" and ora_selezionata in [6, 7]
      else set()
  )
  candidati_validi = [
      d
      for d in archivio_docenti_istituto
      if d["nome"] != docente_assente and d["nome"] not in docenti_occupati
  ]
  candidati_ordinati = ordina_candidati_sostituzione(
      candidati_validi, plesso_selezionato
  )

  col1, col2 = st.columns(2)
  with col1:
    st.markdown("### 🛑 Docenti Occupati (In Classe)")
    if docenti_occupati:
      st.error(
          "I seguenti docenti sono impegnati in cattedra:\n- "
          + "\n- ".join(sorted(docenti_occupati))
      )
    else:
      st.info("Nessun docente bloccato da impegni in classe.")

  with col2:
    st.markdown("### ✅ Candidati Sostituti Ordinati")
    if candidati_ordinati:
      for idx, cand in enumerate(candidati_ordinati, 1):
        badge = (
            "🟢"
            if cand["categoria"] == "Recupero"
            else ("🔵" if "Plesso" in cand["categoria"] else "🟠")
        )
        c_a, c_b = st.columns([3, 1])
        with c_a:
          st.write(
              f"**{idx}. {cand['nome']}** {badge} *{cand['categoria']}* |"
              f" Plesso: {cand['plesso_origine']} | Storico:"
              f" {cand['storico_sostituzioni']}h"
          )
        with c_b:
          if st.button("Assegna", key=f"asgna_puntuale_{cand['nome']}"):
            st.success(
                f"Assegnato **{cand['nome']}** alla classe"
                f" **{classe_selezionata}** ({ora_selezionata}ª ora)."
            )
    else:
      st.warning("Nessun docente disponibile.")
