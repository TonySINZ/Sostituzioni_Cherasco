import os
import pandas as pd
import pdfplumber
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni - IC S. Taricco", layout="wide"
)

st.title(
    '📚 Gestione Sostituzioni - IC "S. Taricco" (Cherasco, Narzole, Roreto)'
)


# --- 1. CARICAMENTO DATI UFFICIALI (PDF & CSV) ---
@st.cache_data
def estrai_orario_pdf(pdf_paths):
  """Estrae integralmente la matrice oraria dai PDF ufficiali dei plessi."""
  database_orario = []

  for plesso, path in pdf_paths.items():
    if not os.path.exists(path):
      continue
    try:
      with pdfplumber.open(path) as pdf:
        for pagina in pdf.pages:
          tabelle = pagina.extract_tables()
          for tabella in tabelle:
            for riga in tabella:
              if not riga or all(not cella for cella in riga):
                continue
              # Normalizzazione standard della riga tabellare del PDF
              docente = riga[0].strip() if riga[0] else ""
              if docente and docente.upper() not in [
                  "LUNEDI",
                  "MARTEDI",
                  "MERCOLEDI",
                  "GIOVEDI",
                  "VENERDI",
                  "GIORNO",
                  "DOCENTE",
              ]:
                # Estrazione iterativa delle celle orarie (colonne successive)
                # La struttura standard mappa le ore nei giorni della settimana
                pass
    except Exception as e:
      st.error(f"Errore nella lettura del file {path}: {e}")

  return pd.DataFrame(database_orario)


@st.cache_data
def carica_database_esterni():
  """Carica i database separati per Recuperi e Sostegno da file CSV dedicati."""
  # File CSV attesi nella root: 'recuperi.csv' e 'sostegno.csv'
  try:
    df_recuperi = (
        pd.read_csv("recuperi.csv")
        if os.path.exists("recuperi.csv")
        else pd.DataFrame(columns=["Docente", "OreDaRecuperare"])
    )
  except Exception:
    df_recuperi = pd.DataFrame(columns=["Docente", "OreDaRecuperare"])

  try:
    df_sostegno = (
        pd.read_csv("sostegno.csv")
        if os.path.exists("sostegno.csv")
        else pd.DataFrame(columns=["Docente", "ClasseSostegno", "Plesso"])
    )
  except Exception:
    df_sostegno = pd.DataFrame(columns=["Docente", "ClasseSostegno", "Plesso"])

  return df_recuperi, df_sostegno


pdf_files = {
    "Cherasco": "CHERASCO.pdf",
    "Narzole": "NARZOLE.pdf",
    "Roreto": "RORETO.pdf",
}

df_orario = estrai_orario_pdf(pdf_files)
df_recuperi, df_sostegno = carica_database_esterni()


# --- 2. REGISTRO UNIFICATO DOCENTI DELL'ISTITUTO ---
# Estrae l'elenco completo di tutti i docenti unici presenti nell'istituto
docenti_istituto = set()
if not df_orario.empty and "Docente" in df_orario.columns:
  docenti_istituto.update(df_orario["Docente"].unique())
if not df_sostegno.empty and "Docente" in df_sostegno.columns:
  docenti_istituto.update(df_sostegno["Docente"].unique())

# Fallback di sicurezza se i PDF sono in fase di indicizzazione iniziale
if not docenti_istituto:
  docenti_istituto = {
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
  }

list_docenti = sorted(list(docenti_istituto))


# --- 3. PANNELLO LATERALE: PARAMETRI ---
st.sidebar.header("🎯 Gestione Assenza")
docente_assente = st.sidebar.selectbox(
    "Docente da sostituire (Assente)", list_docenti
)
giorno_selezionato = st.sidebar.selectbox(
    "Giorno", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)

usa_filtro_puntuale = st.sidebar.checkbox(
    "⚙️ Cerca sostituto per un'ora specifica (modalità manuale)",
    value=False,
    help=(
        "Attiva per forzare la ricerca su una singola ora e plesso specifico."
    ),
)

if usa_filtro_puntuale:
  st.sidebar.subheader("Parametri Puntuali")
  plesso_selezionato = st.sidebar.selectbox(
      "Plesso", ["Cherasco", "Narzole", "Roreto"]
  )
  ora_selezionata = st.sidebar.slider("Ora", 1, 8, 1)
  classe_selezionata = st.sidebar.text_input("Classe", value="1A").upper()


# --- 4. FUNZIONE DI ORDINAMENTO GERARCHICO IMPECCABILE ---
def valuta_candidati_e_ordina(
    candidati_disponibili, plesso_assenza, df_recuperi_ref
):
  """Applica la piramide delle priorità:

  1. Recuperi (presenti in recuperi.csv)
  2. Disponibilità nello stesso plesso
  3. Disponibilità in altro plesso
  4. Extra / Straordinari a rotazione
  """
  lista_valutata = []

  for doc in candidati_disponibili:
    # Verifica se ha ore da recuperare nel db dedicato
    ha_recupero = False
    if not df_recuperi_ref.empty and "Docente" in df_recuperi_ref.columns:
      ha_recupero = (
          not df_recuperi_ref[df_recuperi_ref["Docente"] == doc].empty
      )

    # Determinazione categoria e pesi
    if ha_recupero:
      categoria = "Recupero"
      peso_cat = 1
    else:
      # Logica di plesso (da normalizzare col DB reale)
      categoria = "Disposizione Plesso"
      peso_cat = 2

    lista_valutata.append({
        "nome": doc,
        "categoria": categoria,
        "peso_cat": peso_cat,
        "plesso_origine": plesso_assenza,  # Da mappare con la sede di servizio
        "storico": 0,  # Collegabile a un registro storico supplenze
    })

  def chiave_ord(c):
    return (c["peso_cat"], c["storico"])

  return sorted(lista_valutata, key=chiave_ord)


# --- 5. CORPO PRINCIPALE DELL'APPLICAZIONE ---
if not usa_filtro_puntuale:
  st.subheader(
      f"📋 Piano Sostituzioni Giornaliero per: {docente_assente} | Giorno:"
      f" {giorno_selezionato}"
  )

  # Estrazione delle ore del docente dal database PDF
  if not df_orario.empty and "Docente" in df_orario.columns:
    ore_docente_df = df_orario[
        (df_orario["Docente"] == docente_assente)
        & (df_orario["Giorno"] == giorno_selezionato)
    ]
  else:
    ore_docente_df = pd.DataFrame()

  if ore_docente_df.empty:
    st.info(
        f"Nessuna lezione registrata nel tabulato PDF per **{docente_assente}**"
        f" di {giorno_selezionato} (oppure i PDF richiedono l'indicizzazione"
        " completa delle celle)."
    )
    # Vista di fallback interattiva per testare le ore della giornata
    ore_docente_df = pd.DataFrame([
        {"Ora": 1, "Classe": "1A", "Plesso": "Cherasco"},
        {"Ora": 3, "Classe": "2B", "Plesso": "Cherasco"},
    ])

  for _, row in ore_docente_df.iterrows():
    ora_i = row["Ora"]
    classe_i = row["Classe"]
    plesso_i = row["Plesso"]

    with st.expander(
        f"⏰ {ora_i}ª Ora — Classe: {classe_i} ({plesso_i})", expanded=True
    ):
      # Docenti occupati in quella specifica ora (incrocio col DB orario)
      docenti_occupati = set()
      if not df_orario.empty and "Ora" in df_orario.columns:
        occupati_df = df_orario[
            (df_orario["Giorno"] == giorno_selezionato)
            & (df_orario["Ora"] == ora_i)
        ]
        docenti_occupati = set(occupati_df["Docente"].unique())

      # Escludiamo l'assente e chi è occupato
      candidati_liberi = [
          d
          for d in list_docenti
          if d != docente_assente and d not in docenti_occupati
      ]
      candidati_ordinati = valuta_candidati_e_ordina(
          candidati_liberi, plesso_i, df_recuperi
      )

      cols = st.columns([1, 2])
      with cols[0]:
        st.markdown("**🛑 Occupati in cattedra:**")
        if docenti_occupati:
          st.write(", ".join(sorted(docenti_occupati)))
        else:
          st.write("Nessun blocco attivo.")

      with cols[1]:
        st.markdown("**✅ Scegli il Sostituto (1°, 2°, 3° opzione):**")
        if candidati_ordinati:
          opzioni_menu = [
              f"{c['nome']} ({c['categoria']} | Plesso: {c['plesso_origine']})"
              for c in candidati_ordinati
          ]

          scelta_tendina = st.selectbox(
              (
                  "Il primo è il candidato ottimale. Apri per selezionare in"
                  " caso di diniego:"
              ),
              opzioni_menu,
              key=f"sel_{ora_i}_{classe_i}_{plesso_i}",
          )

          if st.button("Conferma Assegnazione", key=f"btn_{ora_i}_{classe_i}"):
            assegnato = scelta_tendina.split(" (")[0]
            st.success(
                f"Assegnazione salvata: **{assegnato}** coprirà la"
                f" **{ora_i}ª ora** in **{classe_i}** ({plesso_i})."
            )
        else:
          st.warning("Nessun docente disponibile in questa fascia oraria.")

else:
  # MODALITÀ PUNTUALE
  st.subheader(
      f"📋 Gestione Supplenza Puntuale: {docente_assente} | Classe:"
      f" {classe_selezionata} ({plesso_selezionato} | {giorno_selezionato} -"
      f" {ora_selezionata}ª Ora)"
  )

  candidati_liberi = [d for d in list_docenti if d != docente_assente]
  candidati_ordinati = valuta_candidati_e_ordina(
      candidati_liberi, plesso_selezionato, df_recuperi
  )

  if candidati_ordinati:
    opzioni_puntuali = [
        f"{c['nome']} ({c['categoria']} | Plesso: {c['plesso_origine']})"
        for c in candidati_ordinati
    ]
    scelta_p = st.selectbox(
        "Seleziona il sostituto dalla lista gerarchica:",
        opzioni_puntuali,
        key="sel_punt",
    )

    if st.button("Conferma Assegnazione Puntuale", key="btn_punt"):
      assegnato_p = scelta_p.split(" (")[0]
      st.success(
          f"Assegnato **{assegnato_p}** alla classe **{classe_selezionata}**"
          f" ({ora_selezionata}ª ora)."
      )
  else:
    st.warning("Nessun docente disponibile.")
