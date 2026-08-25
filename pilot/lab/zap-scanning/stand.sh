#!/bin/sh
# Стенд «Лавка»: поднять, уронить, сбросить. Только 127.0.0.1:8081.
#
#   ./stand.sh start   поднять
#   ./stand.sh stop    уронить
#   ./stand.sh reset   уронить, забыть журнал и сохранённые заметки, поднять
#
# Удаление лабы — снести каталог: ничего вне него она не создаёт.
D="$(cd "$(dirname "$0")" && pwd)/stand"

case "$1" in
  stop)
    if [ -f "$D/stand.pid" ]; then
      kill "$(cat "$D/stand.pid")" 2>/dev/null
      rm -f "$D/stand.pid"
      echo "стенд остановлен"
    else
      echo "стенд не запущен"
    fi
    ;;
  reset)
    "$0" stop
    rm -f "$D/access.log" "$D/server.log"
    "$0" start
    ;;
  start)
    cd "$D" || exit 1
    if [ -f stand.pid ] && kill -0 "$(cat stand.pid)" 2>/dev/null; then
      echo "стенд уже поднят, pid $(cat stand.pid)"
      exit 0
    fi
    if curl -s -o /dev/null --max-time 2 http://127.0.0.1:8081/; then
      echo "порт 8081 уже занят чем-то другим — освободите его"
      exit 1
    fi
    nohup python3 app.py 8081 > server.log 2>&1 &
    echo $! > stand.pid
    i=0
    while [ $i -lt 60 ]; do
      curl -s -o /dev/null http://127.0.0.1:8081/ && break
      i=$((i + 1))
    done
    echo "стенд на http://127.0.0.1:8081/, pid $(cat stand.pid)"
    ;;
  *)
    echo "использование: $0 start|stop|reset"
    exit 2
    ;;
esac
