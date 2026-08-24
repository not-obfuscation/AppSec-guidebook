"""Тест-кейсы правила os-command-shell-built.

Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило обязано
сработать, `ok:` — обязано промолчать. Сверка:

    .venv-tools/bin/python pilot/semgrep/check.py os-command
"""

import os
import subprocess


# --- ловит -----------------------------------------------------------

def ping_concat(host):
    # ruleid: os-command-shell-built
    os.system("ping -c 1 " + host)


def ping_fstring(host):
    # ruleid: os-command-shell-built
    subprocess.run(f"ping -c 1 {host}", shell=True)


def ping_percent(host):
    cmd = "ping -c 1 %s" % host
    # ruleid: os-command-shell-built
    subprocess.check_output(cmd, shell=True)


def label_popen(name):
    cmd = "echo " + name
    # ruleid: os-command-shell-built
    subprocess.Popen(cmd, shell=True)


# --- молчит ----------------------------------------------------------

def ping_argv(host):
    # Без оболочки, аргументы списком: метасимволы теряют силу.
    # ok: os-command-shell-built
    subprocess.run(["ping", "-c", "1", host], shell=False)


def label_argv(name):
    # Список аргументов, оболочки нет.
    # ok: os-command-shell-built
    subprocess.run(["echo", name])


def fixed_command():
    # Команда постоянная, данных в ней нет.
    # ok: os-command-shell-built
    subprocess.run("df -h", shell=True)


def system_constant():
    # Постоянная строка без данных.
    # ok: os-command-shell-built
    os.system("uptime")
