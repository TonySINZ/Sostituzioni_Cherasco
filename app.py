import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni IC S. Taricco",
    page_icon="🏫",
    layout="centered",
)

st.title("🏫 Gestione Sostituzioni - IC S. Taricco")
st.markdown("*Elenco Generale Unificato (Ordine Alfabetico)*")

# Inizializzazione dello stato (Recuperi e Storico Eccedenti)
if "recuperi" not in st.session_state:
    st.session_state.recuperi = {
        "BELLANOVA": 2,
        "RACCA": 0,
        "CORRADINO": 1,
        "CECCARELLI": 0,
        "DISDERI": 3,
        "PIUMATTI": 1,
        "TRUNFIO": 0,
    }

if "eccedenti" not in st.session_state:
    st.session_state.eccedenti = {
        "BELLANOVA": 1,
        "RACCA": 3,
        "CORRADINO": 0,
        "CECCARELLI": 2,
        "DISDERI": 1,
        "PIUMATTI": 2,
        "TRUNFIO": 0,
    }

st.divider()

# 1. SELEZIONE GIORNO
giorno_scelto = st.selectbox(
    "📅 Giorno della settimana:",
    ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
)

# ANAGRAFICA GENERALE UNIFICATA DI TUTTI I DOCENTI (Ordinata alfabeticamente)
docenti_generali = [
    "AMASIO",
    "BARALE",
    "BARICALLA",
    "BELLANOVA",
    "BENEDET",
    "CAPRIOL",
    "CAVAGL",
    "CAVALLO",
    "CECCARELLI",
    "CONTERNO",
    "CORRADINO",
    "DADONE",
    "DEMAGISTRIS",
    "DEVALLE",
    "DISDERI",
    "FALCO",
    "FERRIGNO",
    "FISSORE",
    "GAETA",
    "GARASSINO",
    "IACUBIN",
    "MACCHIONE",
    "MARENGO",
    "MARCHEL",
    "MARCHELLO",
    "MARKU",
    "MANZONE",
    "MILANO",
    "MODICA",
    "MORRA",
    "NIGRO",
    "PERENO",
    "PIUMATTI",
    "PINTABONA",
    "POLLICINO",
    "RACCA",
    "RESTAGNO",
    "RICCARDI",
    "RUOTOLO",
    "RUSSO",
    "SARTIRANO",
    "SIMONE",
    "TEALDI",
    "TRUNFIO",
    "VARALDO",
]

# Assicuriamoci che l'elenco sia rigorosamente in ordine alfabetico
docenti_generali = sorted(list(set(docenti_generali)))

# SIMULAZIONE DATABASE ORARI GIORNALIERI PER DOCENTE
orario_mappato_esempio = {
    "Martedì": {
        "BELLANOVA": [1, 2, 4, 5],
        "RACCA": [3, 4, 5],
        "CORRADINO": [2, 3, 4],
        "CECCARELLI": [1, 3, 7, 8],
        "DISDERI": [3, 4, 6],
    },
    "Giovedì": {
        "BELLANOVA": [1, 2, 3],
        "RACCA": [1, 2, 3, 4],
        "CORRADINO": [1, 2, 5],
        "CECCARELLI": [2, 4, 5],
        "DISDERI": [1, 2, 5, 6],
    },
    "Lunedì": {},
    "Mercoledì": {},
    "Venerdì": {},
}

st.markdown("### 1️⃣ Inserisci i Docenti Assenti")
assenti_selezionati = st.multiselect(
    "Seleziona i docenti assenti oggi (elenco generale alfabetico):",
    docenti_generali,
)

if assenti_selezionati:
    st.warning(f"⚠️ Assenti oggi: {', '.join(assenti_selezionati)}")

    st.markdown("### 2️⃣ Ore da Coprire e Gestione Sostituzioni")
    st.markdown(
        "*Il sistema mostra le ore reali in cui ciascun docente assente ha lezione.*"
    )

    for docente in assenti_selezionati:
        ore_reali_docente = orario_mappato_esempio.get(giorno_scelto, {}).get(
            docente, [3, 5, 6]
        )

        st.info(
            f"📋 **Assenza di {docente}** ({giorno_scelto}) — Ore di lezione previste: **{', '.join([str(h) + '°' for h in ore_reali_docente])}**"
        )

        for ora in ore_reali_docente:
            st.subheader(
                f"⏰ Copertura per la {ora}° Ora (Assenza: {docente})"
            )

            # Pool di colleghi disponibili escludendo l'assente
            pool_colleghi = [d for d in docenti_generali if d != docente]

            proposte = []
            for collega in pool_colleghi:
                debito_recupero = st.session_state.recuperi.get(collega, 0)
                ore_ecc = st.session_state.eccedenti.get(collega, 0)

                if debito_recupero > 0:
                    categoria = 1
                    priorita_score = -50 - debito_recupero
                    motivo = f"🔴 **Recupero permesso ({debito_recupero}h di debito)**"
                else:
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

            proposte_ordinate = sorted(
                proposte, key=lambda x: (x["categoria"], x["score"])
            )

            st.markdown("Seleziona il docente sostituto:")

            key_base = f"sost_gen_{giorno_scelto}_{docente}_{ora}"

            for idx, op in enumerate(proposte_ordinate):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
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
                        f"✔️ Sostituzione confermata: **{op['docente']}** coprirà la {ora}° ora."
                    )

            st.markdown("---")
