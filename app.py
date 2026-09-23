import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni IC S. Taricco",
    page_icon="🏫",
    layout="centered",
)

st.title("🏫 Gestione Sostituzioni - IC S. Taricco")
st.markdown("*Cherasco • Narzole • Roreto*")

# Inizializzazione dello stato (Recuperi e Storico Eccedenti)
if "recuperi" not in st.session_state:
    st.session_state.recuperi = {
        "BELLANOVA": 2,
        "RACCA": 0,
        "CORRADINO": 1,
        "CECCARELLI": 0,
        "DISDERI": 3,
    }

if "eccedenti" not in st.session_state:
    st.session_state.eccedenti = {
        "BELLANOVA": 1,
        "RACCA": 3,
        "CORRADINO": 0,
        "CECCARELLI": 2,
        "DISDERI": 1,
    }

# Storico delle sostituzioni effettuate oggi
if "sostituzioni_oggi" not in st.session_state:
    st.session_state.sostituzioni_oggi = {}

st.divider()

# Selezione Plesso e Giorno
plesso_scelto = st.selectbox(
    "📍 Seleziona il Plesso:", ["Cherasco", "Narzole", "Roreto"]
)
giorno_scelto = st.selectbox(
    "📅 Giorno:", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)

# Anagrafica docenti per plesso (campione di test basato sui PDF)
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

st.markdown("### 1️⃣ Inserisci i Docenti Assenti")
assenti_selezionati = st.multiselect(
    "Seleziona i docenti assenti oggi in questo plesso:",
    docenti_disponibili_plesso,
)

if assenti_selezionati:
    st.warning(f"⚠️ Assenti oggi: {', '.join(assenti_selezionati)}")

    st.markdown("### 2️⃣ Elenco Proposte Gerarchiche e Assegnazione")
    st.markdown(
        "*Scala di priorità:* 🔴 **Recuperi permessi** ➡️ 🟡 **Ore a disposizione** ➡️ 🟢 **Ore eccedenti (rotazione)**"
    )

    # Simuliamo le ore da coprire (es. 1ª e 2ª ora)
    ore_da_coprire = [1, 2]

    for docente in assenti_selezionati:
        st.info(f"📋 **Copertura per l'assenza di: {docente}**")

        for ora in ore_da_coprire:
            st.subheader(f"⏰ {ora}° Ora di lezione")

            # Escludiamo il docente assente dal pool dei soccorritori
            pool_colleghi = [
                d for d in docenti_disponibili_plesso if d != docente
            ]

            proposte = []
            for collega in pool_colleghi:
                debito_recupero = st.session_state.recuperi.get(collega, 0)
                ore_ecc = st.session_state.eccedenti.get(collega, 0)

                # Definizione gerarchica del punteggio e della categoria
                # Livello 1: Recupero permesso (priorità massima, score negativo)
                # Livello 2: Ore a disposizione / Contemporaneità (score medio)
                # Livello 3: Ore eccedenti (score basato sullo storico ore fatte)
                if debito_recupero > 0:
                    categoria = 1
                    priorita_score = -50 - debito_recupero
                    motivo = (
                        f"🔴 **Recupero permesso da effettuare ({debito_recupero}h di debito)**"
                    )
                else:
                    # Per ora consideriamo le eccedenti basate sullo storico
                    categoria = 3
                    priorita_score = ore_ecc
                    motivo = (
                        f"🟢 Ore eccedenti (Storico attuale: {ore_ecc}h fatte)"
                    )

                proposte.append({
                    "docente": collega,
                    "categoria": categoria,
                    "score": priorita_score,
                    "motivo": motivo,
                })

            # Ordinamento rigoroso per livello gerarchico e score
            proposte_ordinate = sorted(
                proposte, key=lambda x: (x["categoria"], x["score"])
            )

            # Mostriamo TUTTE le opzioni possibili con le spunte interattive
            st.markdown(
                "Seleziona il docente che effettuerà la sostituzione per questa ora:"
            )

            key_base = f"sost_{plesso_scelto}_{docente}_{ora}"

            for idx, op in enumerate(proposte_ordinate):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    # Checkbox per confermare la scelta del sostituto
                    scelto = st.checkbox(
                        "",
                        key=f"{key_base}_{op['docente']}",
                        label_visibility="collapsed",
                    )
                with col2:
                    st.markdown(
                        f"**{op['docente']}** — {op['motivo']}"
                    )

                if scelto:
                    st.success(
                        f"✔️ Assegnato a **{op['docente']}** per la {ora}° ora."
                    )

            st.markdown("---")
