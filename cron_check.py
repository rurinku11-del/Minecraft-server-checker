import os
import requests
from mcstatus import BedrockServer

HOST = os.getenv("SERVER_HOST", "Dreamworld-Cr8M.aternos.me")
PORT = int(os.getenv("SERVER_PORT", "52525"))
WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")

try:
    server = BedrockServer(HOST, PORT, timeout=10)
    status = server.status()

    players = status.players.online
    maximum = status.players.max
    latency = round(status.latency)

    message = (
        "🟢 **Minecraft Server ONLINE**\n"
        f"`{HOST}:{PORT}`\n"
        f"👥 Players: `{players}/{maximum}`\n"
        f"📡 Ping: `{latency} ms`"
    )

except Exception as e:
    message = (
        "🔴 **Minecraft Server OFFLINE**\n"
        f"`{HOST}:{PORT}`"
    )

print(message)

if WEBHOOK:
    requests.post(
        WEBHOOK,
        json={"content": message},
        timeout=10
    )
