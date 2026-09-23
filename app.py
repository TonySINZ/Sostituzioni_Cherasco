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

st.divider()

# Selezione Plesso e Giorno
plesso_scelto = st.selectbox(
    "📍 Seleziona il Plesso:", ["Cherasco", "Narzole", "Roreto"]
)
giorno_scelto = st.selectbox(
    "📅 Giorno:", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
)

# Anagrafica docenti per plesso
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
    "Seleziona i docenti assenti oggi:", docenti_disponibili_plesso
)

if assenti_selezionati:
    st.warning(f"⚠️ Assenti oggi: {', '.join(assenti_selezionati)}")

    st.markdown("### 2️⃣ Proposte di Sostituzione (con rotazione e priorità)")

    if st.button("🔍 Genera Sostituzioni", type="primary"):
        # Teniamo traccia dei docenti già assegnati in questa elaborazione per evitare doppioni consecutivi
        gia_assegnati_oggi = set()

        # Simuliamo le ore da coprire (es. 1ª, 2ª e 3ª ora)
        ore_da_coprire = [1, 2, 3]

        for docente in assenti_selezionati:
            st.info(f"📋 **Copertura per assenza di: {docente}**")

            for ora in ore_da_coprire:
                st.markdown(f"**⏰ {ora}° Ora di lezione:**")

                pool_colleghi = [
                    d
                    for d in docenti_disponibili_plesso
                    if d != docente and d not in gia_assegnati_oggi
                ]

                # Se per caso finiamo i docenti puliti, ripeschiamo dall'intero plesso tranne l'assente
                if not pool_colleghi:
                    pool_colleghi = [
                        d for d in docenti_disponibili_plesso if d != docente
                    ]

                proposte = []
                for collega in pool_colleghi:
                    debito_recupero = st.session_state.recuperi.get(collega, 0)
                    ore_ecc = st.session_state.eccedenti.get(collega, 0)

                    # Scala di priorità:
                    # 1. Chi ha debito di recupero (priorità massima)
                    # 2. Chi ha meno ore eccedenti (rotazione equa)
                    if debito_recupero > 0:
                        priorita_score = -20 - debito_recupero
                        motivo = f"🔴 **Recupero permesso ({debito_recupero}h)**"
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

                # Ordinamento per priorità
                proposte_ordinate = sorted(proposte, key=lambda x: x["score"])

                # Prendiamo le prime 2 alternative diverse
                opzioni_top = proposte_ordinate[:2]

                for i, opzione in enumerate(opzioni_top, 1):
                    st.write(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;*{i}*️⃣ **{opzione['docente']}** — {opzione['motivo']}"
                    )
                    # Registriamo il docente scelto per penalizzarlo nelle ore successive della stessa giornata
                    gia_assegnati_oggi.add(opzione["docente"])

                st.markdown("---")
