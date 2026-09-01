import pandas as pd
import streamlit as st
from psycopg.rows import dict_row

from patient_platform.load.database import connection_factory


st.set_page_config(page_title="Patient Data Platform",
                   page_icon="+", layout="wide")


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
st.caption("Vue de gouvernance des donnees patients synthetiques")

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
    st.subheader("Répartition des données métier")
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
