import os
import io
import json
import sqlite3
import logging
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Naplózás beállítása
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==============================================================================
# BIZTONSÁGI FIGYELMEZTETÉS:
# A Google API JSON kulcsot NE tedd be ide a kódba! 
# A kód a 'GDRIVE_SERVICE_ACCOUNT_JSON' nevű környezeti változóból olvassa be, 
# amit a GitHub Secrets-ben kell beállítanod.
# ==============================================================================

# CÉLMAPPA ID (Ahova a kész ceges_adatok.db fájl mentésre kerül)
TARGET_DB_FOLDER_ID = "1qqL-xyNBbWVFgFLxBeTX3EKjd7vjiRbR"

# CÉL ADATBÁZIS FÁJLNEVE
LOCAL_DB_NAME = "ceges_adatok.db"

# MAPPA MAPPING (SQL Táblanév -> Google Drive Mappa ID)
SQL_MAPPING = {
    "payment_report": "1KGd5i9yH9UxJw6yTSveZBpbwwaS3Hj6_",
    "payout_report": "11HFdIpgeEIPKR2hAguigkhCVa7aYOOYe",
    "resrev_report": "1Kabe1R7ADsqtoVyRb-sgGead7k9lZWJs",
    "felhomatrac_2026": "19bo5GiU6lrPEgfrSbJrO74e7pWD9Ng7U",
    "szamlazz_hu_2026": "16KYmZhM-F08ZNHj-3VQf1TZXszHki1Cf"
}

# ==============================================================================
# OKOS FÜL MAPPING (SQL Táblanév -> Excel Fül Név vagy Index)
# Ha egy táblanév nem szerepel itt, automatikusan az 1. fület (index: 0) olvassa be.
# ==============================================================================
SHEET_MAPPING = {
    "payment_report": "Card payments",  # Pontos szöveges fül név
    "payout_report": "Payouts",          # Pontos szöveges fül név
    "resrev_report": 2                   # 3. fül (0-s indexeléssel: 0, 1, 2)
}

def get_drive_service():
    """Autentikáció a GitHub Secrets-be beállított JSON kulccsal."""
    gdrive_json_str = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
    if not gdrive_json_str:
        raise ValueError("HIBA: A 'GDRIVE_SERVICE_ACCOUNT_JSON' környezeti változó hiányzik!")
    
    creds_dict = json.loads(gdrive_json_str)
    creds = Credentials.from_service_account_info(
        creds_dict, 
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def get_latest_excel_file(service, folder_id):
    """Megkeresi a legfrissebb Excel fájlt az adott Drive mappában."""
    query = f"'{folder_id}' in parents and (mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel') and trashed=false"
    results = service.files().list(
        q=query, 
        orderBy="modifiedTime desc", 
        pageSize=1, 
        fields="files(id, name, modifiedTime)"
    ).execute()
    
    files = results.get('files', [])
    if not files:
        return None, None
    return files[0]['id'], files[0]['name']

def upload_or_update_db(service, local_file_path, target_folder_id):
    """Megkeresi a célmappában a ceges_adatok.db fájlt: ha van, frissíti, ha nincs, feltölti."""
    query = f"'{target_folder_id}' in parents and name='{LOCAL_DB_NAME}' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    existing_files = results.get('files', [])

    media = MediaFileUpload(local_file_path, mimetype='application/x-sqlite3', resumable=True)

    if existing_files:
        file_id = existing_files[0]['id']
        logging.info(f"Drive-on lévő adatbázisfájl frissítése (ID: {file_id})...")
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        logging.info("Új adatbázisfájl feltöltése a célmappába...")
        file_metadata = {'name': LOCAL_DB_NAME, 'parents': [target_folder_id]}
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def main():
    logging.info("=== DRIVESYNCBOT INDÍTÁSA ===")
    
    try:
        service = get_drive_service()
    except Exception as e:
        logging.error(f"Autentikációs hiba: {e}")
        return

    # Ideiglenes helyi SQLite adatbázis törlése/létrehozása a konténerben
    if os.path.exists(LOCAL_DB_NAME):
        os.remove(LOCAL_DB_NAME)
        
    conn = sqlite3.connect(LOCAL_DB_NAME)

    # Végigmegyünk a Drive mappákon
    for table_name, folder_id in SQL_MAPPING.items():
        try:
            file_id, file_name = get_latest_excel_file(service, folder_id)
            if not file_id:
                logging.warning(f"Nem található Excel fájl ebben a mappában: [{table_name}] ({folder_id})")
                continue

            # Meghatározzuk, hogy melyik fület kell beolvasni (alapértelmezett: 0, azaz az 1. fül)
            sheet_to_load = SHEET_MAPPING.get(table_name, 0)

            logging.info(f"Feldolgozás: [{table_name}] <-- Fájl: '{file_name}' | Kijelölt fül: '{sheet_to_load}'")
            
            # Excel letöltése a RAM memóriába
            request = service.files().get_media(fileId=file_id)
            excel_bytes = io.BytesIO(request.execute())
            
            # Pandas beolvasás a SPECIFIKUS FÜLRŐL és az üres oszlopok eldobása
            df = pd.read_excel(excel_bytes, sheet_name=sheet_to_load)
            df = df.dropna(how='all', axis=1)

            # Beírás az SQLite táblába
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            logging.info(f"   -> Tábla sikeresen frissítve: '{table_name}' ({len(df)} sor, {len(df.columns)} oszlop)")

        except Exception as e:
            logging.error(f"Hiba a(z) [{table_name}] feldolgozásakor: {e}")

    conn.close()

    # Kész .db fájl feltöltése/frissítése a Drive célmappában
    logging.info("=== SQLITE FÁJL FELTÖLTÉSE A GOOGLE DRIVE CÉLMAP PÁBA ===")
    try:
        upload_or_update_db(service, LOCAL_DB_NAME, TARGET_DB_FOLDER_ID)
        logging.info("=== FOLYAMAT SIKERESEN BEFEJEZŐDÖTT ===")
    except Exception as e:
        logging.error(f"Hiba a feltöltés során: {e}")

if __name__ == "__main__":
    main()
