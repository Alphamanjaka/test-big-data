import hashlib

import pandas as pd
import streamlit as st
from psycopg.rows import dict_row

from patient_platform.load.database import connection_factory


st.set_page_config(page_title="Patient Data Platform",
                   page_icon="+", layout="wide")


def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def _validate_user(api_key: str) -> dict | None:
    key_hash = _hash_api_key(api_key)
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT user_id, username, role FROM api_user WHERE api_key_hash = %s AND active = TRUE",
                (key_hash,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


with st.sidebar:
    st.header("Authentification")
    api_key = st.text_input("Clé API", type="password", placeholder="Entrez votre clé API")

    if api_key:
        user = _validate_user(api_key)
        if user:
            st.success(f"Connecté: {user['username']} ({user['role']})")
            st.session_state.user = user
        else:
            st.error("Clé API invalide")
            st.session_state.user = None
    else:
        st.session_state.user = None

if not st.session_state.get("user"):
    st.info("Veuillez vous connecter via la barre latérale.")
    st.stop()

user = st.session_state.user


@st.cache_data(ttl=30)
def query_all(query: str, parameters: tuple = ()) -> list[dict]:
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return list(cursor.fetchall())
    finally:
        connection.close()


@st.cache_data(ttl=30)
def query_one(query: str, parameters: tuple = ()) -> dict:
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()
    finally:
        connection.close()


st.title("Patient Data Platform")
st.caption(f"Vue de gouvernance - Connecté en tant que {user['username']} ({user['role']})")

metrics = query_one(
    """
    SELECT
        (SELECT COUNT(*) FROM raw_patient_record) AS raw_records,
        (SELECT COUNT(*) FROM master_patient) AS master_patients,
        (SELECT COUNT(*) FROM patient_identity_map) AS identity_links,
        (SELECT COUNT(*) FROM medicine_purchase) AS purchases,
        (SELECT COUNT(*) FROM patient_consultation) AS consultations,
        (SELECT COUNT(*) FROM imaging_exam) AS exams
    """
)

metric_columns = st.columns(6)
for column, (label, key) in zip(
    metric_columns,
    (
        ("RAW", "raw_records"),
        ("Patients master", "master_patients"),
        ("Liens identité", "identity_links"),
        ("Achats", "purchases"),
        ("Consultations", "consultations"),
        ("Examens", "exams"),
    ),
):
    column.metric(label, int(metrics[key]))

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Repartition des donnees metier")
    st.bar_chart(pd.DataFrame({"enregistrements": {
        "Achats": metrics["purchases"],
        "Consultations": metrics["consultations"],
        "Examens": metrics["exams"],
    }}))

with right:
    st.subheader("Patients master")
    patients = query_all(
        """
        SELECT master_patient_id, full_name, birth_date
        FROM master_patient
        ORDER BY master_patient_id
        """
    )
    st.dataframe(pd.DataFrame(patients), hide_index=True, width="stretch")

if patients:
    selected_id = st.selectbox(
        "Patient",
        options=[patient["master_patient_id"] for patient in patients],
        format_func=lambda value: next(
            patient["full_name"] for patient in patients
            if patient["master_patient_id"] == value
        ),
    )
    links = query_all(
        """
        SELECT source_system, source_patient_id, match_method, match_score, explanation
        FROM patient_identity_map
        WHERE master_patient_id = %s
        ORDER BY source_system, source_patient_id
        """,
        (selected_id,),
    )
    st.subheader(f"Identity map - {selected_id}")
    st.dataframe(pd.DataFrame(links), hide_index=True, width="stretch")

if user["role"] == "admin":
    st.divider()
    st.subheader("Administration")

    tab1, tab2 = st.tabs(["Utilisateurs", "Journal d'audit"])

    with tab1:
        st.write("### Utilisateurs enregistres")
        users = query_all(
            "SELECT user_id, username, role, active, created_at FROM api_user ORDER BY user_id"
        )
        st.dataframe(pd.DataFrame(users), hide_index=True, width="stretch")

    with tab2:
        st.write("### Derniers acces")
        audit = query_all(
            "SELECT username, endpoint, method, response_status, ip_address, accessed_at FROM access_audit ORDER BY accessed_at DESC LIMIT 50"
        )
        st.dataframe(pd.DataFrame(audit), hide_index=True, width="stretch")

if user["role"] in ("admin", "analyst"):
    st.divider()
    st.subheader("Consentements")
    consents = query_all(
        """
        SELECT c.master_patient_id, m.full_name, c.purpose, c.granted, c.recorded_at
        FROM consent c
        JOIN master_patient m ON c.master_patient_id = m.master_patient_id
        ORDER BY c.recorded_at DESC
        """
    )
    st.dataframe(pd.DataFrame(consents), hide_index=True, width="stretch")
