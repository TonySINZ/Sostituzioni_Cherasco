import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni IC S. Taricco",
    page_icon="🏫",
    layout="centered",
)

# Titolo dell'applicazione ottimizzato per smartphone
st.title("🏫 Gestione Sostituzioni")
st.markdown(
    "*Istituto Comprensivo 'S. Taricco' - Cherasco, Narzole, Roreto*"
)

# ---------------------------------------------------------
# 1. SIMULAZIONE DATABASE ORARI E DOCENTI (I 3 PLESSI)
# ---------------------------------------------------------
# Nelle versioni successive questo potrà essere collegato a un foglio Google Sheets o Excel.
# Per adesso strutturiamo la base dati logica per testare il sistema.


# Inizializziamo lo "Storico" delle ore eccedenti e dei recuperi permessi in memoria di sessione
if "recuperi" not in st.session_state:
    # Esempio: Docente -> Ore di permesso da recuperare (debito)
    st.session_state.recuperi = {
        "BELLANOVA": 2,
        "RACCA": 0,
        "CORRADINO": 1,
        "CECCARELLI": 0,
        "DISDERI": 3,
    }

if "eccedenti" not in st.session_state:
    # Esempio: Docente -> Ore eccedenti già svolte (per la rotazione equa)
    st.session_state.eccedenti = {
        "BELLANOVA": 1,
        "RACCA": 3,
        "CORRADINO": 0,
        "CECCARELLI": 2,
        "DISDERI": 1,
    }


# ---------------------------------------------------------
# 2. SELEZIONE DEL PLESSO E GIORNO
# ---------------------------------------------------------
st.divider()
plesso_scelto = st.selectbox(
    "📍 Seleziona il Plesso:", ["Cherasco", "Narzole", "Roreto"]
)
giorno_scelto = st.selectbox(
    "📅 Giorno della settimana:",
    ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
)

st.subheader(f"Gestione Giornaliera - Plesso di {plesso_scelto}")

# ---------------------------------------------------------
# 3. ARCHIVIO SIMULATO DOCENTI PRESENTI NEL PLESSO
# ---------------------------------------------------------
# Elenco di esempio basato sui plessi analizzati (da estendere liberamente)
docenti_per_plesso = {
    "Cherasco": [
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
        "BARICALLA",
        "SARTIRANO",
        "FERRIGNO",
        "VARALDO",
        "MORRA",
        "DADONE",
        "MARCHELLO",
        "MARKU",
        "MANZONE",
        "PERENO",
        "BARALE",
    ],
    "Narzole": [
        "CECCARELLI",
        "BARALE",
        "POLLICINO",
        "GARASSINO",
        "RICCARDI",
        "MACCHIONE",
        "COSTANTINO",
        "CONTERNO",
        "SCALAS",
        "GAETA",
        "FALCO",
        "MARENGO",
    ],
    "Roreto": [
        "DISDERI",
        "TRUNFIO",
        "RUOTOLO",
        "NIGRO",
        "DEVALLE",
        "DADONE",
        "TEALDI",
        "PIUMATTI",
        "MODICA",
        "IACUBIN",
        "MARCHEL",
        "MILANO",
        "AMASIO",
        "BENEDET",
        "MANZON",
        "CAVAGL",
        "RUSSO",
        "CAPRIOL",
    ],
}

docenti_disponibili_plesso = docenti_per_plesso.get(plesso_scelto, [])

# ---------------------------------------------------------
# 4. INSERIMENTO ASSENZE DA SMARTPHONE
# ---------------------------------------------------------
st.markdown("### 1️⃣ Inserisci i Docenti Assenti")
assenti_selezionati = st.multiselect(
    "Seleziona i docenti assenti oggi in questo plesso:",
    docenti_disponibili_plesso,
)

# Simulazione orario giornaliero delle classi da coprire per i docenti assenti
# (In una versione avanzata il sistema leggerà l'ora esatta dal PDF/Excel dell'orario)
if assenti_selezionati:
    st.warning(f"⚠️ Docenti assenti oggi: {', '.join(assenti_selezionati)}")

    st.markdown("### 2️⃣ Generazione Proposte di Sostituzione")
    st.markdown(
        "*Il sistema calcola automaticamente la scala di priorità:* **1. Recuperi permessi** ➡️ **2. Ore a disposizione** ➡️ **3. Ore eccedenti (minore storico)**"
    )

    if st.button("🔍 Trova Sostituzioni Ottimali", type="primary"):
        for docente in assenti_selezionati:
            st.info(f"📋 **Copertura per assenza di: {docente}**")

            # Simuliamo le ore da coprire (es. 1ª e 2ª ora)
            ore_da_coprire = [1, 2]

            for ora in ore_da_coprire:
                st.markdown(f"**⏰ {ora}° Ora di lezione:**")

                # FILTRAGGIO E ORDINAMENTO DELLA SCALA DI PRIORITÀ NEL PLESSO:
                # Escludiamo il docente assente dal pool dei soccorritori
                pool_colleghi = [
                    d for d in docenti_disponibili_plesso if d != docente
                ]

                # Creazione di una classifica fittizia ma coerente con le regole stabilite:
                proposte = []
                for collega in pool_colleghi:
                    debito_recupero = st.session_state.recuperi.get(collega, 0)
                    ore_ecc = st.session_state.eccedenti.get(collega, 0)

                    # Assegnazione del punteggio di priorità (più basso è prioritario)
                    # Se ha debito di recupero -> priorità altissima (punteggio -10 o -20)
                    # Se non ha recupero -> conta quante ore eccedenti ha fatto (meno ne ha, prima viene scelto)
                    if debito_recupero > 0:
                        priorita_score = -10 - debito_recupero
                        motivo = f"🔴 **Da recuperare ({debito_recupero}h di permesso)**"
                    else:
                        priorita_score = ore_ecc
                        motivo = (
                            f"🟢 Ore eccedenti (Storico: {ore_ecc}h fatte)"
                        )

                    proposte.append({
                        "docente": collega,
                        "score": priorita_score,
                        "motivo": motivo,
                    })

                # Ordiniamo per priorità
                proposte_ordinate = sorted(proposte, key=lambda x: x["score"])

                # Mostriamo almeno le prime 2 opzioni prioritarie richieste
                opzioni_top = proposte_ordinate[:2]

                for i, opzione in enumerate(opzioni_top, 1leukin):
                    st.write(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;*{i}*️⃣ **{opzione['docente']}** — {opzione['motivo']}"
                    )

                st.markdown("---")

# ---------------------------------------------------------
# 5. SEZIONE DI CONTROLLO RAPIDO (STATO DEBITI/CREDITI)
# ---------------------------------------------------------
with st.expander("📊 Visualizza stato Recuperi e Ore Eccedenti del Plesso"):
    st.markdown("### Situazione Debiti di Recupero Permessi")
    df_rec = pd.DataFrame(
        list(st.session_state.recuperi.items()), columns=["Docente", "Ore Debito"]
    )
    st.dataframe(df_rec, hide_index=True)

    st.markdown("### Storico Ore Eccedenti")
    df_ecc = pd.DataFrame(
        list(st.session_state.eccedenti.items()),
        columns=["Docente", "Ore Eccedenti Fatte"],
    )
    st.dataframe(df_ecc, hide_index=True)
