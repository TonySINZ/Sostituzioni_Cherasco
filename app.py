import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni IC S. Taricco",
    page_icon="🏫",
    layout="centered",
)

st.title("🏫 Gestione Sostituzioni - IC S. Taricco")
st.markdown("*Filtro automatico per Plesso • Ordinamento Alfabetico*")

# Inizializzazione dello stato (Recuperi e Storico Eccedenti)
if "recuperi" not in st.session_state:
    st.session_state.recuperi = {
        "BELLANOVA": 2,
        "RACCA": 0,
        "CORRADINO": 1,
        "CECCARELLI": 0,
        "DISDERI": 3,
        "PERENO": 1,
        "PIUMATTI": 1,
    }

if "eccedenti" not in st.session_state:
    st.session_state.eccedenti = {
        "BELLANOVA": 1,
        "RACCA": 3,
        "CORRADINO": 0,
        "CECCARELLI": 2,
        "DISDERI": 1,
        "PERENO": 0,
        "PIUMATTI": 2,
    }

st.divider()

# 1. SELEZIONE GIORNO
giorno_scelto = st.selectbox(
    "📅 Giorno della settimana:",
    ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"],
)

# ANAGRAFICA SUDDIVISA PER PLESSO (Estratta dai documenti ufficiali)
docenti_per_plesso = {
    "Cherasco": sorted([
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
    ]),
    "Narzole": sorted([
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
    ]),
    "Roreto": sorted([
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
    ]),
}


# Funzione per trovare il plesso di un docente
def trova_plesso(docente):
    for plesso, lista in docenti_per_plesso.items():
        if docente in lista:
            return plesso
    return "Cherasco"  # Default di sicurezza


# Uniamo tutti i docenti in un unico elenco generale alfabetico per la selezione iniziale dell'assente
tutti_i_docenti = sorted(
    list(
        set(
            docenti_per_plesso["Cherasco"]
            + docenti_per_plesso["Narzole"]
            + docenti_per_plesso["Roreto"]
        )
    )
)

# SIMULAZIONE DATABASE ORARI GIORNALIERI PER DOCENTE
orario_mappato_esempio = {
    "Martedì": {
        "BELLANOVA": [1, 2, 4, 5],
        "RACCA": [3, 4, 5],
        "CORRADINO": [2, 3, 4],
        "CECCARELLI": [1, 3, 7, 8],
        "DISDERI": [3, 4, 6],
        "PERENO": [1, 2, 3, 4],
    },
    "Giovedì": {
        "BELLANOVA": [1, 2, 3],
        "RACCA": [1, 2, 3, 4],
        "CORRADINO": [1, 2, 5],
        "CECCARELLI": [2, 4, 5],
        "DISDERI": [1, 2, 5, 6],
        "PERENO": [2, 3, 6, 8],
    },
    "Lunedì": {},
    "Mercoledì": {},
    "Venerdì": {},
}

st.markdown("### 1️⃣ Inserisci i Docenti Assenti")
assenti_selezionati = st.multiselect(
    "Seleziona i docenti assenti oggi:", tutti_i_docenti
)

if assenti_selezionati:
    st.warning(f"⚠️ Assenti oggi: {', '.join(assenti_selezionati)}")

    st.markdown("### 2️⃣ Ore da Coprire e Sostituti per Plesso")
    st.markdown(
        "*I sostituti vengono pescati **solo** dallo stesso plesso del docente assente e ordinati alfabeticamente per categoria.*"
    )

    for docente in assenti_selezionati:
        plesso_del_docente = trova_plesso(docente)
        ore_reali_docente = orario_mappato_esempio.get(giorno_scelto, {}).get(
            docente, [3, 5, 6]
        )

        st.info(
            f"📋 **{docente}** (Plesso: **{plesso_del_docente}** | {giorno_scelto}) — Ore di lezione: **{', '.join([str(h) + '°' for h in ore_reali_docente])}**"
        )

        for ora in ore_reali_docente:
            st.subheader(
                f"⏰ Copertura per la {ora}° Ora (Assenza: {docente} - {plesso_del_docente})"
            )

            # POOL DI COLLEGHI RIGOROSAMENTE DELLO STESSO PLESSO
            colleghi_stesso_plesso = docenti_per_plesso[plesso_del_docente]
            pool_colleghi = [d for d in colleghi_stesso_plesso if d != docente]

            proposte = []
            for collega in pool_colleghi:
                debito_recupero = st.session_state.recuperi.get(collega, 0)
                ore_ecc = st.session_state.eccedenti.get(collega, 0)

                if debito_recupero > 0:
                    categoria = 1
                    # Usiamo il nome del collega come chiave secondaria per l'ordine alfabetico perfetto a parità di categoria
                    motivo = f"🔴 **Recupero permesso ({debito_recupero}h di debito)**"
                else:
                    categoria = 3
                    motivo = (
                        f"🟢 Ore eccedenti (Storico attuale: {ore_ecc}h fatte)"
                    )

                proposte.append({
                    "docente": collega,
                    "categoria": categoria,
                    "ore_ecc": ore_ecc,
                    "motivo": motivo,
                })

            # Ordinamento rigoroso: prima per categoria (recuperi vs eccedenti) e poi alfabetico per nome del docente
            proposte_ordinate = sorted(
                proposte, key=lambda x: (x["categoria"], x["ore_ecc"], x["docente"])
            )

            st.markdown(
                f"Seleziona il sostituto dal plesso di **{plesso_del_docente}**:"
            )

            key_base = f"sost_plesso_{giorno_scelto}_{docente}_{ora}"

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
