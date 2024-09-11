# run.py

import subprocess
import threading
import time

import pyfiglet
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app import create_app, db

app = create_app()


def wait_for_db():
    retries = 10
    base_delay = 1
    for i in range(retries):
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
            print_colored("[DB_WAIT] - Database is up and running!", 42)
            return
        except OperationalError:
            delay = base_delay * (2 ** i)
            print_colored(f"[DB_WAIT] - Database not ready, retrying in {delay} seconds ({i + 1}/{retries})...", 43)
            time.sleep(delay)
    print_colored("[DB_WAIT] - Failed to connect to the database after several attempts.", 41)
    exit(1)


def run_mqtt_subscription():
    time.sleep(3)
    subprocess.call(['python', 'mqtt_subscription.py'])


def run_sensor_threshold_alert():
    time.sleep(5)
    subprocess.call(['python', 'sensor_threshold_alert.py'])


def print_colored(_text, color_code):
    print(f"\033[{color_code}m{_text}\033[0m", flush=True)


def print_ascii_logo(_text, font='slant'):
    ascii_art = pyfiglet.figlet_format(_text, font=font)
    print_colored(ascii_art, 32)


if __name__ == '__main__':
    logo_text = "SDMM"
    print_ascii_logo(logo_text, font="standard")

    wait_for_db()

    threading.Thread(target=run_mqtt_subscription).start()
    threading.Thread(target=run_sensor_threshold_alert).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
