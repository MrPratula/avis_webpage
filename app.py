import json

import matplotlib.pyplot as plt
import io
import base64

from datetime import datetime

from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

print("Configuring db connection")

# Configura la connessione al database MariaDB
with open("config/db_credentials.json") as f:
    db_credentials = json.load(f)
    user = db_credentials["user"]
    password = db_credentials["password"]
    ip_address = db_credentials["ip_address"]
    schema = db_credentials["schema"]

sql_uri = f"mysql+mysqlconnector://{user}:{password}@{ip_address}/{schema}"

app.config['SQLALCHEMY_DATABASE_URI'] = sql_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

# Inizializza SQLAlchemy
db = SQLAlchemy(app)


# Definisci il modello per la tabella members
class Members(db.Model):
    number = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(16), nullable=False)


# Definisci il modello per la tabella delays con chiave primaria composta
class Delays(db.Model):
    delay_date = db.Column(db.Date, nullable=False)
    member_number = db.Column(db.Integer, db.ForeignKey('members.number'), nullable=False)
    __table_args__ = (
        db.PrimaryKeyConstraint('delay_date', 'member_number'),  # Chiave primaria composta
    )


# Definisci il modello per la tabella absences con chiave primaria composta
class Absences(db.Model):
    absence_date = db.Column(db.Date, nullable=False)
    member_number = db.Column(db.Integer, db.ForeignKey('members.number'), nullable=False)
    __table_args__ = (
        db.PrimaryKeyConstraint('absence_date', 'member_number'),  # Chiave primaria composta
    )

print("Done")

@app.route('/', methods=['GET', 'POST'])
def home():

    if request.method == 'POST':

        # Recupera i dati dei checkbox
        late_selections = [number for number in request.form if number.startswith('late_') and request.form[number]]
        absent_selections = [number for number in request.form if number.startswith('absent_') and request.form[number]]

        # Elenco dei membri selezionati per ritardo
        late_numbers = [number.split('_')[1] for number in late_selections]
        absent_numbers = [number.split('_')[1] for number in absent_selections]

        # Ottieni la data corrente
        current_date = datetime.now().date()

        # Ottieni i membri dal database
        late_members = Members.query.filter(Members.number.in_(late_numbers)).all()
        absent_members = Members.query.filter(Members.number.in_(absent_numbers)).all()

        # Aggiungi i membri ritardatari alla tabella delays solo se non esistono già
        for member in late_members:
            # Controlla se il record esiste già
            existing_delay = Delays.query.filter_by(delay_date=current_date, member_number=member.number).first()
            if not existing_delay:
                delay_entry = Delays(delay_date=current_date, member_number=member.number)
                db.session.add(delay_entry)

        # Aggiungi i membri assenti alla tabella absences solo se non esistono già
        for member in absent_members:
            # Controlla se il record esiste già
            existing_absence = Absences.query.filter_by(absence_date=current_date,
                                                        member_number=member.number).first()

            if not existing_absence:
                absence_entry = Absences(absence_date=current_date, member_number=member.number)
                db.session.add(absence_entry)

        # Commit delle modifiche nel database
        db.session.commit()

    # Ottieni la data corrente
    current_date = datetime.now().date()

    # Recupera i membri dal database
    members = Members.query.order_by(Members.number).all()

    # Recupera i ritardi per la data corrente
    late_today = Delays.query.filter_by(delay_date=current_date).all()

    # Recupera le assenze per la data corrente
    absent_today = Absences.query.filter_by(absence_date=current_date).all()

    # Crea un set di numeri di membri in ritardo
    late_member_numbers = {delay.member_number for delay in late_today}

    # Crea un set di numeri di membri assenti
    absent_member_numbers = {absence.member_number for absence in absent_today}

    return render_template('index.html',
                           members=members,
                           late_member_numbers=late_member_numbers,
                           absent_member_numbers=absent_member_numbers)


# Rotta per la pagina dei grafici
@app.route('/stats')
def stats():
    # Ottenere il conteggio dei ritardi per ogni membro
    delay_counts = db.session.query(Delays.member_number, db.func.count(Delays.delay_date)) \
        .group_by(Delays.member_number).all()
    # Ottenere il conteggio delle assenze per ogni membro
    absence_counts = db.session.query(Absences.member_number, db.func.count(Absences.absence_date)) \
        .group_by(Absences.member_number).all()

    # Trasforma i risultati in un dizionario per accesso più facile
    delay_counts_dict = {member: count for member, count in delay_counts}
    absence_counts_dict = {member: count for member, count in absence_counts}

    # Prendi tutti i membri e riempi con 0 se non ci sono dati su ritardi o assenze
    members = Members.query.order_by(Members.number).all()

    delay_data = []
    absence_data = []

    for member in members:
        delay_data.append((member.nickname, delay_counts_dict.get(member.number, 0)))
        absence_data.append((member.nickname, absence_counts_dict.get(member.number, 0)))

    # Ordina i dati per ritardi e assenze in ordine decrescente (dal più ritardatario al meno)
    delay_data.sort(key=lambda x: x[1], reverse=True)  # Ordina per numero di ritardi
    absence_data.sort(key=lambda x: x[1], reverse=True)  # Ordina per numero di assenze

    # Separare i nomi e i conteggi per plot
    delay_names, delay_values = zip(*delay_data) if delay_data else ([], [])
    absence_names, absence_values = zip(*absence_data) if absence_data else ([], [])

    # Creazione del grafico dei ritardi
    fig1, ax1 = plt.subplots()
    ax1.bar(delay_names, delay_values, color='blue')
    ax1.set_title('Ritardi per membro')
    ax1.set_xlabel('Membro')
    ax1.set_ylabel('Numero di ritardi')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Salva il grafico in formato base64
    delay_img = io.BytesIO()
    plt.savefig(delay_img, format='png')
    delay_img.seek(0)
    delay_img_base64 = base64.b64encode(delay_img.getvalue()).decode()

    # Creazione del grafico delle assenze
    fig2, ax2 = plt.subplots()
    ax2.bar(absence_names, absence_values, color='red')
    ax2.set_title('Assenze per membro')
    ax2.set_xlabel('Membro')
    ax2.set_ylabel('Numero di assenze')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Salva il grafico in formato base64
    absence_img = io.BytesIO()
    plt.savefig(absence_img, format='png')
    absence_img.seek(0)
    absence_img_base64 = base64.b64encode(absence_img.getvalue()).decode()

    return render_template('stats.html', absence_img=absence_img_base64, delay_img=delay_img_base64)


if __name__ == '__main__':
    print("Starting Flask")

    #app.run(host="localhost", port=12345, debug=True)
    app.run(host="0.0.0.0", port=443, ssl_context=("/etc/letsencrypt/live/mrpratula.duckdns.org/fullchain.pem", "/etc/letsencrypt/live/mrpratula.duckdns.org/privkey.pem"), debug=True)

    # app.run(host="0.0.0.0", port=5000, ssl_context=("config/cert.pem", "config/key.pem"), debug=True)
