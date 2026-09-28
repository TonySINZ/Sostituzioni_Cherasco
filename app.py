import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni - IC S. Taricco", layout="wide"
)

st.title(
    '📚 Gestione Sostituzioni - IC "S. Taricco" (Cherasco, Narzole, Roreto)'
)


# --- 1. MOTORE DI PARSING DA FILE EXCEL ---
@st.cache_data
def estrai_orario_excel(file_path):
  database_orario = []
  giorni_standard = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]

  if not os.path.exists(file_path):
    return pd.DataFrame(
        columns=["Docente", "Plesso", "Giorno", "Ora", "Classe"]
    )

  try:
    xls = pd.ExcelFile(file_path)
    for plesso in xls.sheet_names:
      df = pd.read_excel(xls, sheet_name=plesso, header=None)

      # Identifichiamo la riga delle classi (solitamente indice 3 o 2)
      # Cerchiamo la riga che contiene i nomi delle classi (es. 1A, 2A, 1C...)
      row_classi_idx = None
      for idx in range(min(5, len(df))):
        row_vals = [str(v) for v in df.iloc[idx].values if pd.notna(v)]
        if any(
            re.search(r"\d+[A-Z]", v.strip().upper()) for v in row_vals
        ):
          row_classi_idx = idx
          break

      if row_classi_idx is None:
        continue

      classi_map = {}
      for col_idx, val in enumerate(df.iloc[row_classi_idx]):
        if pd.notna(val):
          c_text = str(val).strip().upper()
          # Pulizia eventuale da descrizioni extra
          c_text = re.sub(
              r"^(SCUOLA.*)", "", c_text
          )  # Evita intestazioni lunghe
          if c_text and len(c_text) < 10:
            classi_map[col_idx] = c_text

      # Scansione delle righe successive per giorno e ora
      giorno_corrente = "Lunedì"
      giorno_idx_counter = 0

      for r_idx in range(row_classi_idx + 1, len(df)):
        riga = df.iloc[r_idx]
        cell_giorno = riga.iloc[0] if len(riga) > 0 and pd.notna(riga.iloc[0]) else None
        cell_ora = riga.iloc[1] if len(riga) > 1 and pd.notna(riga.iloc[1]) else None

        if cell_giorno:
          g_text = str(cell_giorno).strip().upper()
          for g in giorni_standard:
            if g.upper() in g_text:
              giorno_corrente = g
              break

        if cell_ora:
          ora_text = str(cell_ora).strip()
          # Estrazione numero ora (es. 1^, 1, ecc.)
          match_ora = re.search(r"(\d+)", ora_text)
          if match_ora:
            ora_num = int(match_ora.group(1))

            # Leggiamo le celle delle classi per questa ora
            for col_idx, classe_nome in classi_map.items():
              if col_idx < len(riga) and pd.notna(riga.iloc[col_idx]):
                cell_content = str(riga.iloc[col_idx]).strip()
                if cell_content and cell_content.upper() != "NAN":
                  # Estrazione pulita del nome docente (rimuovendo la materia es. "ROSSI ita" -> "ROSSI")
                  # Di solito il formato è "COGNOME materia" oppure "COGNOME/Altro"
                  docente_raw = cell_content.split("/")[
                      0
                  ]  # Prende il primo se c'è compresenza
                  docente_raw = re.sub(
                      r"\s+(ita|mat|geo|sto|arte|mus|moto|tec|rel|ing|fra|ted|tecno.*|sost.*)$",
                      "",
                      docente_raw,
                      flags=re.IGNORECASE,
                  )
                  docente_pulito = docente_raw.strip().upper()

                  if (
                      len(docente_pulito) > 1
                      and docente_pulito not in ["UNNAMED", "NAN"]
                  ):
                    database_orario.append({
                        "Docente": docente_pulito,
                        "Plesso": plesso.capitalize(),
                        "Giorno": giorno_corrente,
                        "Ora": ora_num,
                        "Classe": classe_nome,
                    })
  except Exception as e:
    st.error(f"Errore nella lettura del file Excel: {e}")

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


# Nome del file excel caricato
excel_file_path = "ORARIO con SOSTEGNO.xls"

df_orario = estrai_orario_excel(excel_file_path)
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
  st.sidebar.error("Nessun docente trovato nel file Excel.")
  docente_assente = st.sidebar.selectbox(
      "Seleziona il Docente Assente", ["FILE VUOTO"]
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
        f"Nessuna ora registrata per **{docente_assente}** nella giornata di"
        f" **{giorno_selezionato}**."
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
