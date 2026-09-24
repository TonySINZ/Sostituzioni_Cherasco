import os
import re
import pandas as pd
import pdfplumber
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni - IC S. Taricco", layout="wide"
)

st.title(
    '📚 Gestione Sostituzioni - IC "S. Taricco" (Cherasco, Narzole, Roreto)'
)


# --- 1. MOTORE DI PARSING RIGOROSO (PULIZIA TOTALE FRAMMENTI) ---
@st.cache_data
def estrai_orario_pdf(pdf_paths):
  database_orario = []
  giorni_standard = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]

  # Termini di sistema o frammenti di layout da scartare tassativamente
  blacklist_termini = {
      "LUNEDI",
      "MARTEDI",
      "MERCOLEDI",
      "GIOVEDI",
      "VENERDI",
      "GIORNO",
      "DOCENTE",
      "ORARIO",
      "ID",
      "IDE",
      "COD",
      "PLESSO",
      "CLASSE",
      "LOC",
      "REM",
  }

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

              # Uniamo le prime due celle per evitare che il cognome sia spezzato (es. 'ROS' + 'SI')
              pezzo1 = riga[0].strip() if riga[0] else ""
              pezzo2 = riga[1].strip() if len(riga) > 1 and riga[1] else ""

              # Se la prima cella è un frammento corto (es. ID, E, LO), proviamo a vedere se è parte di un’intestazione o scartiamla
              docente_candidato = f"{pezzo1} {pezzo2}".strip().upper()

              # Pulizia da spazi multipli
              docente_candidato = re.sub(r"\s+", " ", docente_candidato)

              # Criteri ferrei di validità per un cognome di un docente:
              # - Almeno 4 caratteri
              # - Non deve essere nella blacklist
              # - Non deve contenere solo cifre o caratteri strani
              if (
                  len(docente_candidato) < 4
                  or docente_candidato in blacklist_termini
                  or re.match(r"^[\d\W_]+$", docente_candidato)
                  or len(pezzo1)
                  <= 2  # Se il primo blocco è di 1-2 lettere è un troncone
              ):
                continue

              docente = docente_candidato

              # Scansione delle ore/colonne successive (partendo da riga[1] o riga[2])
              colonne_orario = riga[2:] if len(riga) > 2 else riga[1:]
              for idx_col, cella in enumerate(colonne_orario, start=1):
                if cella and cella.strip():
                  classe_estratta = cella.strip().upper()
                  giorno_idx = (idx_col - 1) // 8
                  ora_num = ((idx_col - 1) % 8) + 1
                  giorno = (
                      giorni_standard[giorno_idx]
                      if giorno_idx < len(giorni_standard)
                      else "Lunedì"
                  )

                  database_orario.append({
                      "Docente": docente,
                      "Plesso": plesso,
                      "Giorno": giorno,
                      "Ora": ora_num,
                      "Classe": classe_estratta,
                  })
    except Exception as e:
      st.error(f"Errore nella lettura del file {path}: {e}")

  return pd.DataFrame(
      database_orario, columns=["Docente", "Plesso", "Giorno", "Ora", "Classe"]
  )


@st.cache_data
def carica_database_esterni():
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


# --- 2. ELENCO DOCENTI DELL'ISTITUTO ---
docenti_istituto = set()
if not df_orario.empty and "Docente" in df_orario.columns:
  docenti_istituto.update(df_orario["Docente"].unique())
if not df_sostegno.empty and "Docente" in df_sostegno.columns:
  docenti_istituto.update(df_sostegno["Docente"].unique())

list_docenti = sorted(list(docenti_istituto))


# --- 3. PANNELLO LATERALE ---
st.sidebar.header("🎯 Gestione Assenza Docente")

if not list_docenti:
  st.sidebar.error(
      "Nessun docente valido estratto dai PDF. Verifica la struttura delle"
      " tabelle."
  )
  docente_assente = st.selectbox(
      "Seleziona il Docente Assente", ["INSERISCI FILE VALIDI"]
  )
else:
  docente_assente = st.sidebar.selectbox(
      "Seleziona il Docente Assente", list_docenti
  )

giorno_selezionato = st.sidebar.selectbox(
    "Giorno dell'assenza", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)

usa_filtro_puntuale = st.sidebar.checkbox(
    "⚙️ Forza ora specifica (Modalità manuale)", value=False
)

if usa_filtro_puntuale:
  st.sidebar.subheader("Parametri Puntuali")
  plesso_selezionato = st.sidebar.selectbox(
      "Plesso", ["Cherasco", "Narzole", "Roreto"]
  )
  ora_selezionata = st.sidebar.slider("Ora", 1, 8, 1)
  classe_selezionata = st.sidebar.text_input(
      "Classe da coprire", value="1A"
  ).upper()


# --- 4. LOGICA DI ORDINAMENTO GERARCHICO ---
def valuta_candidati_e_ordina(
    candidati_disponibili, plesso_assenza, df_recuperi_ref
):
  lista_valutata = []
  for doc in candidati_disponibili:
    ha_recupero = False
    if not df_recuperi_ref.empty and "Docente" in df_recuperi_ref.columns:
      ha_recupero = (
          not df_recuperi_ref[df_recuperi_ref["Docente"] == doc].empty
      )

    categoria = "Recupero" if ha_recupero else "Disposizione Plesso"
    peso_cat = 1 if ha_recupero else 2

    lista_valutata.append({
        "nome": doc,
        "categoria": categoria,
        "peso_cat": peso_cat,
        "plesso_origine": plesso_assenza,
        "storico": 0,
    })
  return sorted(lista_valutata, key=lambda c: (c["peso_cat"], c["storico"]))


# --- 5. CORPO PRINCIPALE ---
if not usa_filtro_puntuale:
  st.subheader(
      f"📋 Piano Sostituzioni per il docente: **{docente_assente}** — Giorno:"
      f" **{giorno_selezionato}**"
  )

  ore_docente_df = (
      df_orario[
          (df_orario["Docente"] == docente_assente)
          & (df_orario["Giorno"] == giorno_selezionato)
      ]
      if not df_orario.empty
      else pd.DataFrame()
  )

  if ore_docente_df.empty:
    st.warning(
        f"Nessuna ora registrata nei PDF per **{docente_assente}** nella"
        f" giornata di **{giorno_selezionato}**."
    )
  else:
    ore_docente_df = ore_docente_df.sort_values(by="Ora")
    for _, row in ore_docente_df.iterrows():
      ora_i = row["Ora"]
      classe_i = row["Classe"]
      plesso_i = row["Plesso"]

      with st.expander(
          f"⏰ {ora_i}ª Ora — Classe: {classe_i} (Plesso: {plesso_i})",
          expanded=True,
      ):
        docenti_occupati = set()
        if not df_orario.empty:
          occ_df = df_orario[
              (df_orario["Giorno"] == giorno_selezionato)
              & (df_orario["Ora"] == ora_i)
          ]
          docenti_occupati = set(occ_df["Docente"].unique())

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
          st.markdown("**🛑 Docenti Occupati in classe:**")
          st.write(
              ", ".join(sorted(docenti_occupati))
              if docenti_occupati
              else "Nessun blocco."
          )

        with cols[1]:
          st.markdown(
              "**✅ Sostituto proposto (1° ottimale / Apri per il"
              " successivo):**"
          )
          if candidati_ordinati:
            opzioni_menu = [
                f"{c['nome']} ({c['categoria']} | Plesso: {c['plesso_origine']})"
                for c in candidati_ordinati
            ]
            scelta_tendina = st.selectbox(
                "Seleziona sostituto:",
                opzioni_menu,
                key=f"sel_{docente_assente}_{giorno_selezionato}_{ora_i}_{classe_i}",
            )

            if st.button(
                "Conferma Assegnazione",
                key=f"btn_{docente_assente}_{giorno_selezionato}_{ora_i}_{classe_i}",
            ):
              assegnato = scelta_tendina.split(" (")[0]
              st.success(
                  f"Assegnazione confermata: **{assegnato}** coprirà la"
                  f" **{ora_i}ª ora** in **{classe_i}** ({plesso_i})"
                  f" sostituendo **{docente_assente}**."
              )
          else:
            st.warning("Nessun docente disponibile in questa ora.")
else:
  st.subheader(
      f"📋 Gestione Supplenza Manuale: {docente_assente} | Classe:"
      f" {classe_selezionata} ({plesso_selezionato} | {giorno_selezionato} -"
      f" {ora_selezionata}ª Ora)"
  )
  docenti_occupati = (
      set(
          df_orario[
              (df_orario["Giorno"] == giorno_selezionato)
              & (df_orario["Ora"] == ora_selezionata)
          ]["Docente"].unique()
      )
      if not df_orario.empty
      else set()
  )
  candidati_liberi = [
      d
      for d in list_docenti
      if d != docente_assente and d not in docenti_occupati
  ]
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
        key="sel_punt_manuale",
    )
    if st.button("Conferma Assegnazione Manuale", key="btn_punt_manuale"):
      assegnato_p = scelta_p.split(" (")[0]
      st.success(
          f"Assegnato **{assegnato_p}** alla classe **{classe_selezionata}**"
          f" ({ora_selezionata}ª ora) in sostituzione di **{docente_assente}**."
      )
  else:
    st.warning("Nessun docente disponibile.")
