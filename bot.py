import os
import time
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template
from mcstatus import JavaServer

app = Flask(__name__)

SERVER_HOST = os.getenv(
    "SERVER_HOST",
    "Dreamworld-Cr8M.aternos.me"
)

SERVER_PORT = int(os.getenv("SERVER_PORT", "52525"))

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

status_data = {
    "online": False,
    "players": 0,
    "max_players": 0,
    "latency": None,
    "last_check": None,
    "uptime_start": None,
    "checks": 0,
    "failures": 0,
    "error": None
}

lock = threading.Lock()


def send_discord(message):
    if not DISCORD_WEBHOOK:
        return

    try:
        import requests

        requests.post(
            DISCORD_WEBHOOK,
            json={"content": message},
            timeout=10
        )

    except Exception as e:
        print("Discord error:", e)


def check_server():
    global status_data

    was_online = False

    while True:

        try:
            server = JavaServer.lookup(
                f"{SERVER_HOST}:{SERVER_PORT}"
            )

            start = time.time()
            status = server.status()
            latency = round((time.time() - start) * 1000)

            players_online = status.players.online
            players_max = status.players.max

            with lock:
                status_data["online"] = True
                status_data["players"] = players_online
                status_data["max_players"] = players_max
                status_data["latency"] = latency
                status_data["last_check"] = datetime.now(
                    timezone.utc
                ).isoformat()
                status_data["checks"] += 1
                status_data["failures"] = 0
                status_data["error"] = None

                if not was_online:
                    status_data["uptime_start"] = datetime.now(
                        timezone.utc
                    ).isoformat()

            if not was_online:
                send_discord(
                    f"🟢 Minecraft server is ONLINE\n"
                    f"`{SERVER_HOST}:{SERVER_PORT}`"
                )

            was_online = True

        except Exception as e:

            with lock:
                status_data["online"] = False
                status_data["players"] = 0
                status_data["latency"] = None
                status_data["last_check"] = datetime.now(
                    timezone.utc
                ).isoformat()
                status_data["failures"] += 1
                status_data["error"] = str(e)

            if was_online:
                send_discord(
                    f"🔴 Minecraft server went OFFLINE\n"
                    f"`{SERVER_HOST}:{SERVER_PORT}`"
                )

            was_online = False

        time.sleep(CHECK_INTERVAL)


@app.route("/")
def home():
    return render_template(
        "index.html",
        host=SERVER_HOST,
        port=SERVER_PORT
    )


@app.route("/api/status")
def api_status():

    with lock:
        data = dict(status_data)

    return jsonify(data)


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":

    thread = threading.Thread(
        target=check_server,
        daemon=True
    )

    thread.start()

    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port
)
