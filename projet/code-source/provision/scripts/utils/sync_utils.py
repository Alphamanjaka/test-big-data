import json
import os
import pytz
from datetime import datetime

SYNC_METADATA_PATH = "/home/vagrant/datalake-final/provision/metadata/sync_metadata.json"

# Assurer que le dossier existe
os.makedirs(os.path.dirname(SYNC_METADATA_PATH), exist_ok=True)

# Fuseau UTC+3
TZ = pytz.timezone("Indian/Antananarivo")

def load_sync_metadata():
    """Charge le fichier JSON s'il existe, sinon retourne dict vide"""
    if os.path.exists(SYNC_METADATA_PATH):
        with open(SYNC_METADATA_PATH, encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def save_sync_metadata(metadata):
    """Sauvegarde le dictionnaire dans le JSON"""
    with open(SYNC_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

def update_sync_metadata(zone, status="ok"):
    """
    Met à jour la synchro globale d'une zone (RAW, Silver, Gold).
    
    :param zone: "RAW", "Silver" ou "Gold"
    :param status: "ok" ou "error"
    """
    metadata = load_sync_metadata()
    # Utiliser le fuseau UTC+3
    now = datetime.now(TZ).isoformat()

    # Initialiser si absent
    if zone not in metadata:
        metadata[zone] = {"last_sync": None, "status": "pending"}

    # Mettre à jour
    metadata[zone] = {
        "last_sync": now,
        "status": status
    }

    save_sync_metadata(metadata)
    print(f"[SYNC] Zone {zone} mise à jour (status={status}, last_sync={now})")
