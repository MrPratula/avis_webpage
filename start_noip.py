
import json
import subprocess

with open ("config/noip-duc.json", "r") as f:
    config = json.load(f)
    address = config["address"]
    username = config["username"]
    password = config["password"]

# Comando da eseguire
command = f"sudo noip-duc -g {address} --username {username} --password {password}"

# Esegui il comando
processo = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Ottieni l'output e l'errore
stdout, stderr = processo.communicate()

# Decodifica e stampa l'output e l'errore
print("Output:")
print(stdout.decode())
print("Errori:")
print(stderr.decode())