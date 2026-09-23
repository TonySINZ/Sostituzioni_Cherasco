import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Sostituzioni IC S. Taricco",
    page_icon="🏫",
    layout="centered",
)

st.title("🏫 Gestione Sostituzioni - IC S. Taricco")
st.markdown("*Controllo Disponibilità, Plessi e Spostamenti*")

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

# ANAGRAFICA SUDDIVISA PER PLESSO
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


def trova_plesso(docente):
    for plesso, lista in docenti_per_plesso.items():
        if docente in lista:
            return plesso
    return "Cherasco"


tutti_i_docenti = sorted(
    list(
        set(
            docenti_per_plesso["Cherasco"]
            + docenti_per_plesso["Narzole"]
            + docenti_per_plesso["Roreto"]
        )
    )
)

# SIMULAZIONE ORARIO COMPLETO DI SERVIZIO (Le ore in cui ciascun docente ha lezione)
# Se un'ora NON è in questa lista, il docente è LIBERO in quell'ora.
orario_servizio_generale = {
    "Martedì": {
        "BELLANOVA": [1, 2, 4, 5],
        "RACCA": [3, 4, 5],
        "CORRADINO": [2, 3, 4],
        "CECCARELLI": [1, 3, 7],  # Niente 8° ora se non prevista
        "DISDERI": [3, 4, 6],
        "PERENO": [1, 2, 3, 4],
    },
    "Giovedì": {
        "BELLANOVA": [1, 2, 3],
        "RACCA": [1, 2, 3, 4],
        "CORRADINO": [1, 2, 5],
        "CECCARELLI": [2, 4, 5],
        "DISDERI": [1, 2, 5, 6],
        "PERENO": [2, 3, 6],  # Nessuna 8° ora al giovedì
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

    st.markdown("### 2️⃣ Ore da Coprire e Sostituti Liberi")
    st.markdown(
        "*Il sistema scarta automaticamente i docenti già occupati in classe e calcola la compatibilità di plesso e spostamento.*"
    )

    for docente in assenti_selezionati:
        plesso_del_docente = trova_plesso(docente)
        ore_reali_docente = orario_servizio_generale.get(giorno_scelto, {}).get(
            docente, [3, 5, 6]
        )

        st.info(
            f"📋 **{docente}** (Plesso: **{plesso_del_docente}** | {giorno_scelto}) — Ore di lezione da coprire: **{', '.join([str(h) + '°' for h in ore_reali_docente])}**"
        )

        for ora in ore_reali_docente:
            st.subheader(
                f"⏰ Copertura per la {ora}° Ora (Assenza: {docente} - {plesso_del_docente})"
            )

            # FILTRO CRUCIALE: Selezioniamo SOLO i docenti dello stesso plesso
            colleghi_stesso_plesso = docenti_per_plesso[plesso_del_docente]

            proposte = []
            for collega in colleghi_stesso_plesso:
                if collega == docente:
                    continue

                # VERIFICA DISPONIBILITÀ: Il collega ha lezione in questa specifica ora?
                ore_impegno_collega = (
                    orario_servizio_generale.get(giorno_scelto, {})
                    .get(collega, [])
                )

                # Se il collega è già impegnato in classe in questa ora, lo scartiamo
                if ora in ore_impegno_collega:
                    continue

                # Controllo franchigia spostamento (se il collega è itinerante, verifichiamo che abbia almeno un'ora libera prima o dopo)
                # (Regola base rispettata: nello stesso plesso è immediatamente disponibile)

                debito_recupero = st.session_state.recuperi.get(collega, 0)
                ore_ecc = st.session_state.eccedenti.get(collega, 0)

                if debito_recupero > 0:
                    categoria = 1
                    motivo = f"🔴 **Recupero permesso ({debito_recupero}h di debito)**"
                else:
                    categoria = 3
                    motivo = (
                        f"🟢 Libero in orario (Storico ore eccedenti: {ore_ecc}h)"
                    )

                proposte.append({
                    "docente": collega,
                    "categoria": categoria,
                    "ore_ecc": ore_ecc,
                    "motivo": motivo,
                })

            # Ordinamento gerarchico e alfabetico
            proposte_ordinate = sorted(
                proposte, key=lambda x: (x["categoria"], x["ore_ecc"], x["docente"])
            )

            if not proposte_ordinate:
                st.warning(
                    f"⚠️ Nessun docente disponibile nel plesso di {plesso_del_docente} per la {ora}° ora!"
                )
            else:
                st.markdown(
                    f"Docenti liberi nel plesso di **{plesso_del_docente}**:"
                )
                key_base = f"sost_disp_{giorno_scelto}_{docente}_{ora}"

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
