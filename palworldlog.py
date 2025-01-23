import os
import time
import configparser
import requests
import re

# Configuración inicial del archivo config.ini
CONFIG_PATH = "config.ini"
LOG_PATH = r"Z:\\Steam\\steamapps\\common\\PalServer\\Pal\\Binaries\\Win64\\chatlog.txt"

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return config

def send_to_discord(webhook_url, message):
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a Discord: {e}")

def remove_timestamp(line):
    # Remueve la fecha y hora al inicio de la línea
    return re.sub(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ", "", line)

def process_log_line(line, config, webhook_url):
    # Eliminar timestamp al inicio
    line = remove_timestamp(line)

    # Mensajes de configuración
    message_to_join = config.get("MESSAGES", "messagetojoin")
    message_to_leave = config.get("MESSAGES", "messagetoleave")
    message_to_chat = config.get("MESSAGES", "messagetochat")
    message_to_was_killed = config.get("MESSAGES", "messagetowaskilled")
    message_to_attacked = config.get("MESSAGES", "messagetoattacked")
    message_to_die = config.get("MESSAGES", "messagetodie")

    # Regex para cada tipo de evento
    join_regex = re.compile(r"SYSTEM said \[(.+?)\] joined the server\.")
    leave_regex = re.compile(r"SYSTEM said \[(.+?)\] left the server\.")
    chat_regex = re.compile(r"(.+?) said (.+)")
    was_killed_regex = re.compile(r"SYSTEM said '(.+?)' was killed (.+)")
    attacked_regex = re.compile(r"SYSTEM said '(.+?)' was attacked by a wild '(.+?)' and died\.")
    die_regex = re.compile(r"SYSTEM said '(.+?)' died to extreme body temperature\.")

    # Detección de eventos
    if match := join_regex.search(line):
        user = match.group(1)
        send_to_discord(webhook_url, message_to_join.replace("USUARIO", user))
    elif match := leave_regex.search(line):
        user = match.group(1)
        send_to_discord(webhook_url, message_to_leave.replace("USUARIO", user))
    elif match := chat_regex.search(line):
        user, message = match.groups()
        send_to_discord(webhook_url, message_to_chat.replace("USUARIO", user).replace("mensaje", message))
    elif match := was_killed_regex.search(line):
        user, reason = match.groups()
        send_to_discord(webhook_url, message_to_was_killed.replace("USUARIO", user).replace("(mensaje del log)", reason))
    elif match := attacked_regex.search(line):
        user, beast = match.groups()
        send_to_discord(webhook_url, message_to_attacked.replace("USUARIO", user).replace("NOMBRE DE LA BESTIA", beast))
    elif match := die_regex.search(line):
        user = match.group(1)
        send_to_discord(webhook_url, message_to_die.replace("USUARIO", user))

def tail_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        # Ir al final del archivo
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)  # Esperar si no hay nuevas líneas
                continue
            yield line.strip()

def main():
    # Cargar configuración
    config = load_config()
    webhook_url = config.get("DISCORD", "webhook_url")

    print("Iniciando monitoreo del archivo log...")
    try:
        for line in tail_file(LOG_PATH):
            process_log_line(line, config, webhook_url)
    except KeyboardInterrupt:
        print("Monitoreo detenido por el usuario.")

if __name__ == "__main__":
    main()
