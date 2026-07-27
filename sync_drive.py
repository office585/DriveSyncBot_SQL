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

# CÉL ADATBÁZIS ÚTVONAL (Ha létezik az Asztal, oda menti közvetlenül)
DESKTOP_DB_PATH = r"C:\Users\User\Desktop\ceges_adatok.db"
LOCAL_DB_NAME = DESKTOP_DB_PATH if os.path.exists(r"C:\Users\User\Desktop") else "ceges_adatok.db"

# CÉLMAPPA ID a Google Drive-on
TARGET_DB_FOLDER_ID = "1qqL-xyNBbWVFgFLxBeTX3EKjd7vjiRbR"

# ==============================================================================
# MULTITENANT MAPPA MAPPING (35 PONTOS DRIVE MAPPA ID)
# ==============================================================================
HOUSES_MAPPING = {
    "athenaeum": {
        "szamlazz_hu_2026": "16KYmZhM-F08ZNHj-3VQf1TZXszHki1Cf",
        "felhomatrac_2026": "19bo5GiU6lrPEgfrSbJrO74e7pWD9Ng7U",
        "payout_report": "11HFdIpgeEIPKR2hAguigkhCVa7aYOOYe",
        "payment_report": "1KGd5i9yH9UxJw6yTSveZBpbwwaS3Hj6_",
        "resrev_report": "1Kabe1R7ADsqtoVyRb-sgGead7k9lZWJs"
    },
    "buda_castle": {
        "szamlazz_hu_2026": "1Se15CyfmRcECnOxCjOCLDK_EsEcikmBL",
        "felhomatrac_2026": "1xk3SOqhKWNPbRMkgZM1JleGwgYHN8p2K",
        "payout_report": "1YW3v3__H92zsHrT1zQZrev9q9FsYYe23",
        "payment_report": "1SaF84GEvQlr8xN2R6KF1uOnhFayPVc_D",
        "resrev_report": "1XkgOWmQYlXFPp0saa6RJDnAOQIFE3TUA"
    },
    "soho": {
        "szamlazz_hu_2026": "1Se15CyfmRcECnOxCjOCLDK_EsEcikmBL",
        "felhomatrac_2026": "1fz1PwvGgmam-vZpg9SF3chn7s4ujTUYf",
        "payout_report": "1avEyXVFme4VXLLsopnmyLIcAwFkH6g0L",
        "payment_report": "1QD0ngN0Fa5vzmk7NrkszNsk3LjzV0DS3",
        "resrev_report": "1JL8FmlUR_NLwTN4PLwaNfxomnqqO3Chy"
    },
    "central": {
        "szamlazz_hu_2026": "1Se15CyfmRcECnOxCjOCLDK_EsEcikmBL",
        "felhomatrac_2026": "1OlJCdki0z-TC1lrewUrL4f0nPzGAbpwO", # 🟢 PONTOS CENTRAL ID
        "payout_report": "1u0lE84uJkrMNlswgHNXxtB7hFxhPlH2I",
        "payment_report": "1TRgDr2i_JrE36GQAqQ6xsTG_k4q6V0QL",
        "resrev_report": "105N_EKgndLbD-5IcHnbTLj0tVSTNzqO2"
    },
    "downtown": {
        "szamlazz_hu_2026": "1Se15CyfmRcECnOxCjOCLDK_EsEcikmBL",
        "felhomatrac_2026": "1HjE1CMPEIYHqG6HA7aPc5OqG0GAfHdXU",
        "payout_report": "1aFa3J4vAYAenmM2y9OwHrLfoM4eTM6E4",
        "payment_report": "1VVu8IXHmx9kFuo82Z-h7mvdvrrYfAiYQ",
        "resrev_report": "1A3n-svd06K3ML0SW59fnGlgpvFaOWH-m"
    },
    "vintage": {
        "szamlazz_hu_2026": "1Se15CyfmRcECnOxCjOCLDK_EsEcikmBL",
        "felhomatrac_2026": "1WWJ3dhu1yw2Lfw3ZxqTqaRtLsjLmg1ac",
        "payout_report": "1hwWmPVt7aUiwHuOwTX0To8rF6fz2LzBb",
        "payment_report": "1IgjazIli9Kxn807Nyl4N_5xOfFObaXfI",
        "resrev_report": "15nEFtJGFDVNuhRzYMa_H1L5dj8o2ROZG"
    },
    "amberlyn": {
        "szamlazz_hu_2026": "1jU3BiAy-iRgz3xvv0uFDu5WTeWqFFtj3",
        "felhomatrac_2026": "102qpagWkmb8j9NO7IU93D6qTVVYdBGKt",
        "payout_report": "1QSxQSYv6vKByO4zp8-MswpSfkT5em7_",
        "payment_report": "1K0SeRyibeikLr9giUWgOQr5YlxncEvr4",
        "resrev_report": "1byLJxJlTywGIjisMscG3FpO76ZCjo53q"
    }
}

SHEET_MAPPING = {
    "payment_report": "Card payments",
    "payout_report": "Payouts",
    "resrev_report": 2
}

def get_drive_service():
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
    query = f"'{target_folder_id}' in parents and name='ceges_adatok.db' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    existing_files = results.get('files', [])

    media = MediaFileUpload(local_file_path, mimetype='application/x-sqlite3', resumable=True)

    if existing_files:
        file_id = existing_files[0]['id']
        logging.info(f"Drive-on lévő adatbázisfájl frissítése (ID: {file_id})...")
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        logging.info("Új adatbázisfájl feltöltése a célmappába...")
        file_metadata = {'name': 'ceges_adatok.db', 'parents': [target_folder_id]}
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def main():
    logging.info("=== MULTITENANT DRIVESYNCBOT INDÍTÁSA ===")
    
    try:
        service = get_drive_service()
    except Exception as e:
        logging.error(f"Autentikációs hiba: {e}")
        return

    if os.path.exists(LOCAL_DB_NAME):
        try: os.remove(LOCAL_DB_NAME)
        except Exception: pass
        
    conn = sqlite3.connect(LOCAL_DB_NAME)
    total_tables_created = 0
    missing_folders = []

    for house_key, reports in HOUSES_MAPPING.items():
        logging.info(f"\n--- 🏠 HÁZ FELDOLGOZÁSA: [{house_key.upper()}] ---")
        
        for report_type, folder_id in reports.items():
            table_name = f"{house_key}_{report_type}"
            
            try:
                file_id, file_name = get_latest_excel_file(service, folder_id)
                if not file_id:
                    logging.warning(f"  ⚠️ Nem található Excel fájl ebben a mappában: [{table_name}] (Folder ID: {folder_id})")
                    missing_folders.append(table_name)
                    continue

                sheet_to_load = SHEET_MAPPING.get(report_type, 0)

                logging.info(f"  ➜ Feldolgozás: [{table_name}] <-- Fájl: '{file_name}' | Fül: '{sheet_to_load}'")
                
                request = service.files().get_media(fileId=file_id)
                excel_bytes = io.BytesIO(request.execute())
                
                try:
                    df = pd.read_excel(excel_bytes, sheet_name=sheet_to_load)
                except Exception:
                    df = pd.read_excel(excel_bytes, sheet_name=0)

                df = df.dropna(how='all', axis=1)

                df.to_sql(table_name, conn, if_exists="replace", index=False)
                total_tables_created += 1
                logging.info(f"     ✔ Tábla sikeresen frissítve: '{table_name}' ({len(df)} sor, {len(df.columns)} oszlop)")

            except Exception as e:
                logging.error(f"  ❌ Hiba a(z) [{table_name}] feldolgozásakor: {e}")

    conn.close()

    logging.info(f"\n=== MŰVELET ÖSSZEGZÉSE: {total_tables_created} / 35 TÁBLA SIKERESEN LÉTREHOZVA ===")
    if missing_folders:
        logging.info(f"Üres/Hiányzó mappák listája: {missing_folders}")

    logging.info("=== SQLITE FÁJL FELTÖLTÉSE A GOOGLE DRIVE CÉLMAP PÁBA ===")
    try:
        upload_or_update_db(service, LOCAL_DB_NAME, TARGET_DB_FOLDER_ID)
        logging.info("=== FOLYAMAT SIKERESEN BEFEJEZŐDÖTT ===")
    except Exception as e:
        logging.error(f"Hiba a feltöltés során: {e}")

if __name__ == "__main__":
    main()
