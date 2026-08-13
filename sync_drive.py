import os
import io
import json
import sqlite3
import logging
import pandas as pd

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ==============================================================================
# NAPLÓZÁS
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==============================================================================
# CÉL ADATBÁZIS
# ==============================================================================

DESKTOP_DB_PATH = r"C:\Users\User\Desktop\ceges_adatok.db"

LOCAL_DB_NAME = (
    DESKTOP_DB_PATH
    if os.path.exists(r"C:\Users\User\Desktop")
    else "ceges_adatok.db"
)


# ==============================================================================
# GOOGLE DRIVE CÉLMAPPA
# ==============================================================================

TARGET_DB_FOLDER_ID = "1qqL-xyNBbWVFgFLxBeTX3EKjd7vjiRbR"


# ==============================================================================
# MULTITENANT MAPPA MAPPING
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
        "payout_report": "1YW3v3__H92zsHrT1zQZreV9q9FsYYe23",
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
        "felhomatrac_2026": "1OlJCdki0z-TC1lrewUrL4f0nPzGAbpwO",
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
        "payout_report": "1QSxQSYv6vKByO4zp8-MsswpSfkT5em7_",
        "payment_report": "1K0SeRyibeikLr9giUWgOQr5YlxncEvr4",
        "resrev_report": "1byLJxJlTywGIjisMscG3FpO76ZCjo53q",
        # TEYA MEGOSZTOTT MAPPA ÉS A KÉT MASTER RIPORT
        "teya_master_osszegzes": "0AP3HkLh_ANsVUk9PVA",
        "teya_master_nyers": "0AP3HkLh_ANsVUk9PVA"
    }
}


# ==============================================================================
# GOOGLE DRIVE KAPCSOLAT
# ==============================================================================

def get_drive_service():
    gdrive_json_str = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")

    if not gdrive_json_str:
        raise ValueError(
            "HIBA: A 'GDRIVE_SERVICE_ACCOUNT_JSON' "
            "környezeti változó hiányzik!"
        )

    creds_dict = json.loads(gdrive_json_str)

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    return build("drive", "v3", credentials=creds)


# ==============================================================================
# LEGFRISSEBB FÁJL KERESÉSE (KÖZÖS MEGHAJTÓK TÁMOGATÁSÁVAL)
# ==============================================================================

def get_latest_excel_file(service, folder_id, report_type=""):
    query = f"'{folder_id}' in parents and trashed=false"

    # Teya Master fájlok specifikus szűrése, hogy ne a napi fájlokat válassza ki
    if report_type == "teya_master_osszegzes":
        query += " and name contains 'MASTER_Osszegzes'"
    elif report_type == "teya_master_nyers":
        query += " and name contains 'MASTER_Nyers'"

    results = service.files().list(
        q=query,
        orderBy="modifiedTime desc",
        pageSize=50,
        fields="files(id, name, mimeType, modifiedTime)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = results.get("files", [])

    if not files:
        return None, None, None

    for file_info in files:
        file_name = file_info.get("name", "").lower()
        mime_type = file_info.get("mimeType", "").lower()

        is_supported_file = (
            file_name.endswith(".xlsx")
            or file_name.endswith(".xls")
            or file_name.endswith(".csv")
            or "spreadsheet" in mime_type
            or "excel" in mime_type
            or "octet-stream" in mime_type
        )

        if is_supported_file:
            return (
                file_info["id"],
                file_info["name"],
                mime_type
            )

    first_file = files[0]

    return (
        first_file["id"],
        first_file["name"],
        first_file.get("mimeType", "")
    )


# ==============================================================================
# FÁJL LETÖLTÉSE
# ==============================================================================

def download_file_bytes(service, file_id, mime_type):
    if "google-apps.spreadsheet" in mime_type:
        request = service.files().export_media(
            fileId=file_id,
            mimeType=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )
    else:
        request = service.files().get_media(
            fileId=file_id,
            supportsAllDrives=True
        )

    return io.BytesIO(request.execute())


# ==============================================================================
# PONTOS LAPNÉV KERESÉSE
# ==============================================================================

def find_exact_sheet_name(sheet_names, required_sheet_name):
    required_normalized = required_sheet_name.strip().lower()

    for sheet_name in sheet_names:
        current_normalized = str(sheet_name).strip().lower()

        if current_normalized == required_normalized:
            return sheet_name

    return None


# ==============================================================================
# PAYMENT REPORT KÉT LAPJÁNAK BEOLVASÁSA
# ==============================================================================

def load_payment_report_sheets(excel_bytes):
    excel_bytes.seek(0)

    try:
        excel_file = pd.ExcelFile(excel_bytes)
        sheet_names = excel_file.sheet_names

    except Exception as error:
        raise ValueError(
            "A Payment Report fájlt nem sikerült Excel-fájlként "
            f"megnyitni: {error}"
        )

    card_sheet = find_exact_sheet_name(
        sheet_names,
        "Card payments"
    )

    external_sheet = find_exact_sheet_name(
        sheet_names,
        "External payments"
    )

    missing_sheets = []

    if card_sheet is None:
        missing_sheets.append("Card payments")

    if external_sheet is None:
        missing_sheets.append("External payments")

    if missing_sheets:
        available_sheets = ", ".join(str(name) for name in sheet_names)
        missing_text = ", ".join(missing_sheets)

        raise ValueError(
            f"Hiányzó kötelező Payment Report lap: {missing_text}. "
            f"A fájlban található lapok: {available_sheets}"
        )

    excel_bytes.seek(0)

    card_df = pd.read_excel(
        excel_bytes,
        sheet_name=card_sheet
    )

    excel_bytes.seek(0)

    external_df = pd.read_excel(
        excel_bytes,
        sheet_name=external_sheet
    )

    return {
        "payment_report": {
            "dataframe": card_df,
            "sheet_name": str(card_sheet)
        },

        "external_payments": {
            "dataframe": external_df,
            "sheet_name": str(external_sheet)
        }
    }


# ==============================================================================
# EGYÉB RIPORTOK BEOLVASÁSA
# ==============================================================================

def load_excel_smart(excel_bytes, report_type):
    excel_bytes.seek(0)

    try:
        excel_file = pd.ExcelFile(excel_bytes)
        sheet_names = excel_file.sheet_names

    except Exception as excel_error:
        excel_bytes.seek(0)

        try:
            dataframe = pd.read_csv(
                excel_bytes,
                sep=None,
                engine="python"
            )

            return dataframe, "CSV_Format"

        except Exception:
            raise ValueError(
                f"Sikertelen beolvasás: {excel_error}"
            )

    if not sheet_names:
        excel_bytes.seek(0)

        dataframe = pd.read_excel(
            excel_bytes,
            sheet_name=0
        )

        return dataframe, "Sheet_0"

    target_sheet = sheet_names[0]

    # --------------------------------------------------------------------------
    # PAYOUT REPORT
    # --------------------------------------------------------------------------

    if report_type == "payout_report":
        matched_sheet = None

        for sheet_name in sheet_names:
            clean_sheet_name = str(sheet_name).strip().lower()

            if clean_sheet_name.startswith("payout"):
                matched_sheet = sheet_name
                break

        if matched_sheet is not None:
            target_sheet = matched_sheet

        elif len(sheet_names) >= 2:
            target_sheet = sheet_names[1]

        else:
            target_sheet = sheet_names[0]

    # --------------------------------------------------------------------------
    # RESERVATION REVENUE REPORT
    # --------------------------------------------------------------------------

    elif report_type == "resrev_report":
        if len(sheet_names) >= 3:
            target_sheet = sheet_names[2]

        elif len(sheet_names) >= 2:
            target_sheet = sheet_names[1]

        else:
            target_sheet = sheet_names[0]

    # --------------------------------------------------------------------------
    # MINDEN MÁS RIPORT (BELEÉRTVE A TEYA MASTER FÁJLOKAT IS)
    # --------------------------------------------------------------------------

    else:
        target_sheet = sheet_names[0]

    excel_bytes.seek(0)

    dataframe = pd.read_excel(
        excel_bytes,
        sheet_name=target_sheet
    )

    return dataframe, str(target_sheet)


# ==============================================================================
# DATAFRAME MENTÉSE SQL-TÁBLÁBA
# ==============================================================================

def save_dataframe_to_sql(dataframe, table_name, connection):
    dataframe = dataframe.dropna(
        how="all",
        axis=1
    )

    dataframe.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False
    )

    logging.info(
        f"      ✔ SQL-tábla sikeresen létrehozva: "
        f"'{table_name}' "
        f"({len(dataframe)} sor, {len(dataframe.columns)} oszlop)"
    )


# ==============================================================================
# SQLITE FELTÖLTÉSE VAGY FRISSÍTÉSE (KÖZÖS MEGHAJTÓK TÁMOGATÁSÁVAL)
# ==============================================================================

def upload_or_update_db(
    service,
    local_file_path,
    target_folder_id
):
    query = (
        f"'{target_folder_id}' in parents "
        "and name='ceges_adatok.db' "
        "and trashed=false"
    )

    results = service.files().list(
        q=query,
        fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    existing_files = results.get("files", [])

    media = MediaFileUpload(
        local_file_path,
        mimetype="application/x-sqlite3",
        resumable=True
    )

    if existing_files:
        file_id = existing_files[0]["id"]

        logging.info(
            "Drive-on lévő adatbázisfájl frissítése "
            f"(ID: {file_id})..."
        )

        service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True
        ).execute()

    else:
        logging.info(
            "Új adatbázisfájl feltöltése a célmappába..."
        )

        file_metadata = {
            "name": "ceges_adatok.db",
            "parents": [target_folder_id]
        }

        service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()


# ==============================================================================
# FŐPROGRAM
# ==============================================================================

def main():
    logging.info(
        "=== MULTITENANT DRIVESYNCBOT INDÍTÁSA ==="
    )

    try:
        service = get_drive_service()

    except Exception as error:
        logging.error(
            f"Autentikációs hiba: {error}"
        )
        return

    # --------------------------------------------------------------------------
    # KORÁBBI HELYI ADATBÁZIS TÖRLÉSE
    # --------------------------------------------------------------------------

    if os.path.exists(LOCAL_DB_NAME):
        try:
            os.remove(LOCAL_DB_NAME)

        except Exception as error:
            logging.warning(
                "A korábbi helyi adatbázist nem sikerült törölni: "
                f"{error}"
            )

    connection = sqlite3.connect(LOCAL_DB_NAME)

    total_tables_created = 0
    missing_folders = []
    failed_reports = []

    # --------------------------------------------------------------------------
    # HÁZAK FELDOLGOZÁSA
    # --------------------------------------------------------------------------

    for house_key, reports in HOUSES_MAPPING.items():
        logging.info(
            f"\n--- 🏠 HÁZ FELDOLGOZÁSA: "
            f"[{house_key.upper()}] ---"
        )

        # ----------------------------------------------------------------------
        # RIPORTTÍPUSOK FELDOLGOZÁSA
        # ----------------------------------------------------------------------

        for report_type, folder_id in reports.items():
            base_table_name = f"{house_key}_{report_type}"

            try:
                file_id, file_name, mime_type = (
                    get_latest_excel_file(
                        service,
                        folder_id,
                        report_type
                    )
                )

                if not file_id:
                    logging.warning(
                        "   ⚠️ Nem található fájl a mappában: "
                        f"[{base_table_name}] "
                        f"(Folder ID: {folder_id})"
                    )

                    missing_folders.append(base_table_name)
                    continue

                excel_bytes = download_file_bytes(
                    service,
                    file_id,
                    mime_type
                )

                # ==============================================================
                # PAYMENT REPORT
                # ==============================================================

                if report_type == "payment_report":
                    payment_sheets = (
                        load_payment_report_sheets(
                            excel_bytes
                        )
                    )

                    # ----------------------------------------------------------
                    # CARD PAYMENTS
                    # ----------------------------------------------------------

                    card_result = payment_sheets["payment_report"]

                    card_table_name = (
                        f"{house_key}_payment_report"
                    )

                    logging.info(
                        f"   ➜ Megtalálva: "
                        f"[{card_table_name}] "
                        f"<-- Fájl: '{file_name}' "
                        f"| Fül: '{card_result['sheet_name']}'"
                    )

                    save_dataframe_to_sql(
                        dataframe=card_result["dataframe"],
                        table_name=card_table_name,
                        connection=connection
                    )

                    total_tables_created += 1

                    # ----------------------------------------------------------
                    # EXTERNAL PAYMENTS
                    # ----------------------------------------------------------

                    external_result = (
                        payment_sheets["external_payments"]
                    )

                    external_table_name = (
                        f"{house_key}_external_payments"
                    )

                    logging.info(
                        f"   ➜ Megtalálva: "
                        f"[{external_table_name}] "
                        f"<-- Fájl: '{file_name}' "
                        f"| Fül: '{external_result['sheet_name']}'"
                    )

                    save_dataframe_to_sql(
                        dataframe=external_result["dataframe"],
                        table_name=external_table_name,
                        connection=connection
                    )

                    total_tables_created += 1

                # ==============================================================
                # MINDEN MÁS RIPORT (BELEÉRTVE A TEYA MASTER FÁJLOKAT IS)
                # ==============================================================

                else:
                    dataframe, used_sheet = load_excel_smart(
                        excel_bytes,
                        report_type
                    )

                    logging.info(
                        f"   ➜ Megtalálva: "
                        f"[{base_table_name}] "
                        f"<-- Fájl: '{file_name}' "
                        f"| Fül: '{used_sheet}'"
                    )

                    save_dataframe_to_sql(
                        dataframe=dataframe,
                        table_name=base_table_name,
                        connection=connection
                    )

                    total_tables_created += 1

            except Exception as error:
                logging.error(
                    f"   ❌ Hiba a(z) "
                    f"[{base_table_name}] "
                    f"feldolgozásakor: {error}"
                )

                failed_reports.append(base_table_name)

    connection.close()

    # --------------------------------------------------------------------------
    # ÖSSZEGZÉS
    # --------------------------------------------------------------------------

    # Várható táblaszám dinamikus kiszámítása
    expected_table_count = sum(
        len(reports) + (1 if "payment_report" in reports else 0)
        for reports in HOUSES_MAPPING.values()
    )

    logging.info(
        f"\n=== MŰVELET ÖSSZEGZÉSE: "
        f"{total_tables_created} / "
        f"{expected_table_count} "
        "TÁBLA LÉTREHOZVA ==="
    )

    if missing_folders:
        logging.info(
            "Üres vagy hiányzó mappák listája: "
            f"{missing_folders}"
        )

    if failed_reports:
        logging.info(
            "Hibásan feldolgozott riportok listája: "
            f"{failed_reports}"
        )

    # --------------------------------------------------------------------------
    # SQLITE FELTÖLTÉSE
    # --------------------------------------------------------------------------

    logging.info(
        "=== SQLITE FÁJL FELTÖLTÉSE "
        "A GOOGLE DRIVE CÉLMAPPÁBA ==="
    )

    try:
        upload_or_update_db(
            service,
            LOCAL_DB_NAME,
            TARGET_DB_FOLDER_ID
        )

        logging.info(
            "=== FOLYAMAT SIKERESEN BEFEJEZŐDÖTT ==="
        )

    except Exception as error:
        logging.error(
            f"Hiba a feltöltés során: {error}"
        )


# ==============================================================================
# PROGRAM INDÍTÁSA
# ==============================================================================

if __name__ == "__main__":
    main()
