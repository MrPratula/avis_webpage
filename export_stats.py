import json

import pymysql
import csv
import os

# === CONFIGURAZIONE DATABASE ===

with open("config/db_credentials.json") as f:
    db_credentials = json.load(f)
    user = db_credentials["user"]
    password = db_credentials["password"]
    ip_address = db_credentials["ip_address"]
    schema = db_credentials["schema"]


DB_CONFIG = {
    "host": ip_address,
    "user": user,
    "password": password,
    "database": schema
}

# === CREAZIONE CONNESSIONE ===
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# === OTTIENI TUTTI I MEMBRI ===
cursor.execute("SELECT number, nickname FROM members")
members = cursor.fetchall()

# === CREA UNA CARTELLA OUTPUT OPZIONALE ===
os.makedirs("output", exist_ok=True)

# === LISTA PER IL FILE TOTAL.CSV ===
totals = []

for number, nickname in members:
    # --- RITARDI ---
    cursor.execute(
        "SELECT delay_date FROM delays WHERE member_number = %s",
        (number,)
    )
    delays = cursor.fetchall()
    delay_file = f"output/{nickname}_ritardi.csv"
    with open(delay_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["delay_date"])
        writer.writerows(delays)

    # --- ASSENZE ---
    cursor.execute(
        "SELECT absence_date FROM absences WHERE member_number = %s",
        (number,)
    )
    absences = cursor.fetchall()
    absence_file = f"output/{nickname}_assenze.csv"
    with open(absence_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["absence_date"])
        writer.writerows(absences)

    # --- AGGIUNGI AL TOTALE ---
    totals.append([
        nickname,
        len(delays),
        len(absences),
        len(delays) + len(absences)
    ])

# === SCRIVI TOTAL.CSV ===
with open("output/total.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["nickname", "num_delays", "num_absences", "total"])
    writer.writerows(totals)

# === CHIUSURA CONNESSIONE ===
cursor.close()
conn.close()

print("✅ File CSV generati nella cartella 'output/'")
