# -----------------------------
# 📘 Définition du schéma FHIR minimal
# -----------------------------
FHIR_FIELDS = {
    "Patient": {
        "patient_uuid": "string",
        "source_patient_id": "string",
        "name": "string",
        "birth_date": "date",
        "gender": "string",
        "address": "string",
        "cin": "string",
        "birth_city": "string",
        "email": "string",
    },
    "Encounter": {
        "patient_uuid": "string",
        "encounter_id": "string",
        "admission_date": "date",
        "discharge_date": "date",
        "create_date": "date",
        "visit_type": "string"
    },
    "Condition": {
        "patient_uuid": "string",
        "diagnosis": "string",
        "diagnosis_code": "string",
        "category": "string",
        "code": "string",
        "info": "string",
        "name": "string"
    },
    "Observation": {
        "patient_uuid": "string",
        "mortality": "int",
        "parity": "int",
        "gravida": "int",
        "live_births": "int"
    }
}

## Patient
# patient_uuid : identifiant unique dans ton Data Lake
# source_patient_id : identifiant original dans la base source
# name : nom complet du patient
# birth_date : date de naissance
# gender : sexe
# address, cin, birth_city, email : infos de contact et d'identité
# cin : numéro de Carte Nationale d'Identité (présent ~75 % des patients)

## Encounter
# encounter_id : identifiant unique de la consultation ou hospitalisation
# admission_date / discharge_date : dates d’entrée et sortie
# create_date : date d’enregistrement dans la base
# visit_type : type de visite (hospitalisation, consultation, etc.)

## Condition
# diagnosis / diagnosis_code : nom et code CIM-10 du diagnostic
# category / code : type de condition (ex : maladie, symptôme)
# info / name : info supplémentaire ou nom détaillé

## Observation
# mortality : 0/1 pour décès (maternel ou infantile)
# parity : nombre de grossesses précédentes
# gravida : nombre de grossesses totales
# live_births : nombre d’enfants vivants
# value : mesure quelconque (poids, tension, etc.)

# Patient : représente l’individu auquel les données médicales sont rattachées. Chaque patient est identifié de manière unique par un patient_uuid.
# Encounter : correspond aux visites ou hospitalisations du patient. Elle est liée à la table Patient via la clé étrangère patient_uuid.
# Condition : décrit les diagnostics médicaux observés lors des consultations ou hospitalisations, tels que codés par la classification CIM-10.
# Observation : regroupe des indicateurs médicaux simples (parité, gravité, mortalité) permettant une première analyse statistique.