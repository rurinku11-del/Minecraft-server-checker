import os
import time
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template
from mcstatus import BedrockServer

app = Flask(__name__)

SERVER_HOST = os.getenv(
    "SERVER_HOST",
    "Dreamworld-Cr8M.aternos.me"
)

SERVER_PORT = int(
    os.getenv("SERVER_PORT", "52525")
)

CHECK_INTERVAL = int(
    os.getenv("CHECK_INTERVAL", "60")
)

DISCORD_WEBHOOK = os.getenv(
    "DISCORD_WEBHOOK",
    ""
)

status_data = {
    "online": False,
    "players": 0,
    "max_players": 0,
    "latency": None,
    "motd": "",
    "version": "",
    "gamemode": "",
    "last_check": None,
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

    was_online = False

    while True:

        try:
            server = BedrockServer(
                SERVER_HOST,
                SERVER_PORT,
                timeout=5
            )

            status = server.status()

            with lock:

                status_data["online"] = True

                status_data["players"] = (
                    status.players.online
                )

                status_data["max_players"] = (
                    status.players.max
                )

                status_data["latency"] = round(
                    status.latency
                )

                status_data["motd"] = (
                    getattr(status, "motd", "")
                )

                status_data["version"] = (
                    getattr(status, "version", "")
                )

                status_data["gamemode"] = (
                    getattr(status, "gamemode", "")
                )

                status_data["last_check"] = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                status_data["checks"] += 1
                status_data["failures"] = 0
                status_data["error"] = None

            if not was_online:

                send_discord(
                    "🟢 Minecraft Bedrock server is ONLINE\n"
                    f"`{SERVER_HOST}:{SERVER_PORT}`"
                )

            was_online = True

            print(
                f"[ONLINE] "
                f"{status_data['players']}/"
                f"{status_data['max_players']} "
                f"| {status_data['latency']}ms"
            )

        except Exception as e:

            with lock:

                status_data["online"] = False
                status_data["players"] = 0
                status_data["max_players"] = 0
                status_data["latency"] = None

                status_data["last_check"] = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                status_data["failures"] += 1

                status_data["error"] = str(e)

            print(
                "[OFFLINE]",
                str(e)
            )

            if was_online:

                send_discord(
                    "🔴 Minecraft Bedrock server "
                    "went OFFLINE\n"
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
        return jsonify(
            dict(status_data)
        )


@app.route("/health")
def health():

    return "OK", 200


def start_monitor():

    thread = threading.Thread(
        target=check_server,
        daemon=True
    )

    thread.start()


start_monitor()


if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
