#!/bin/bash

SERVICE_LABEL="com.niean.assistant-dashboard"
PORT=8090
DOMAIN="gui/$(id -u)"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/$SERVICE_LABEL.plist"
EXPECTED_EXEC="$PROJECT_DIR/scripts/start-http-exec.sh"

if [ ! -f "$PLIST" ]; then
    echo "LaunchAgent plist not found: $PLIST" >&2
    exit 1
fi

if [ ! -x "$EXPECTED_EXEC" ]; then
    echo "Start script is not executable: $EXPECTED_EXEC" >&2
    exit 1
fi

if ! launchctl print "$DOMAIN/$SERVICE_LABEL" >/dev/null 2>&1; then
    launchctl bootstrap "$DOMAIN" "$PLIST"
elif ! launchctl print "$DOMAIN/$SERVICE_LABEL" | grep -q "$EXPECTED_EXEC"; then
    launchctl bootout "$DOMAIN/$SERVICE_LABEL" >/dev/null 2>&1 || true
    launchctl bootstrap "$DOMAIN" "$PLIST"
fi

before_pid="$(lsof -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null || true)"

launchctl kickstart -k "$DOMAIN/$SERVICE_LABEL"

after_pid=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
    after_pid="$(lsof -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$after_pid" ] && [ "$after_pid" != "$before_pid" ]; then
        echo "Restarted $SERVICE_LABEL on port $PORT, pid $after_pid"
        exit 0
    fi
    sleep 1
done

if [ -n "$after_pid" ]; then
    echo "Service is listening on port $PORT, pid $after_pid"
    exit 0
fi

echo "Service failed to listen on port $PORT" >&2
launchctl print "$DOMAIN/$SERVICE_LABEL" >&2 || true
exit 1
