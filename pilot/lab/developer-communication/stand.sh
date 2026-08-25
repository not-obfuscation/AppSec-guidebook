#!/bin/sh
# Поднять/уронить/сбросить стенд лабы. Порт 8082, только петля.
D="$(cd "$(dirname "$0")" && pwd)"
PID="$D/stand/stand.pid"
case "$1" in
  stop)
    [ -f "$PID" ] && kill "$(cat "$PID")" 2>/dev/null
    rm -f "$PID"
    ;;
  reset)
    "$0" stop
    "$0" start
    ;;
  start)
    cd "$D/stand" || exit 1
    nohup python3 app.py 8082 > server.log 2>&1 &
    echo $! > "$PID"
    i=0
    while [ $i -lt 50 ]; do
      curl -s -o /dev/null http://127.0.0.1:8082/ && break
      i=$((i+1))
    done
    echo "стенд поднят, pid $(cat "$PID")"
    ;;
  *)
    echo "использование: ./stand.sh start|stop|reset"
    ;;
esac
