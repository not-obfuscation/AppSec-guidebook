"""Модель setuid-обёртки backup-run: эталонная починка.

Отличие от code.py одно: обёртка больше не доверяет окружению
вызывающего. PATH задан константой системных каталогов, а из
переменных пробрасывается ровно одна — LANG. Это тот же приём,
которым sudo (env_reset) и безопасные setuid-программы сбрасывают
окружение до белого списка.

Это модель: хост, программы и процессы изображены структурами данных
Python. Никакие настоящие привилегии не повышаются и не требуются.

Лаборатория гайдбука. Применимо только к этой лабе.
"""

ROOT_UID = 0

SAFE_PATH = "/usr/sbin:/usr/bin"
KEEP_ENV = ("LANG",)  # единственная переменная, которую берём у вызывающего


class Process:
    """Процесс: реальный, эффективный и сохранённый uid плюс окружение."""

    def __init__(self, ruid: int, euid: int, suid: int, env: dict) -> None:
        self.ruid = ruid
        self.euid = euid
        self.suid = suid
        self.env = dict(env)


class Host:
    """Модель хоста: каталоги с программами, файлы, журнал запусков."""

    def __init__(self) -> None:
        self.programs: dict = {}   # путь -> программа(host, proc, argv)
        self.files: dict = {}      # путь -> (владелец, содержимое)
        self.exec_log: list = []   # (путь, euid, argv)

    def install(self, path: str, program, owner: int = ROOT_UID) -> None:
        self.programs[path] = program

    def write_file(self, proc: Process, path: str, content: str) -> None:
        owner = self.files.get(path, (ROOT_UID, ""))[0]
        # Модель проверки ядра: писать в чужой файл может только root.
        if proc.euid != ROOT_UID and owner != proc.euid:
            raise PermissionError(f"{path}: записывать может не {proc.euid}")
        self.files[path] = (proc.euid, content)

    def exec(self, proc: Process, path: str, argv: list) -> str:
        self.exec_log.append((path, proc.euid, argv))
        return self.programs[path](self, proc, argv)


def collect_backup(host: Host, proc: Process, argv: list) -> str:
    """Настоящий сборщик: складывает копию в /var/backups."""
    host.write_file(proc, "/var/backups/latest.tar", "backup data")
    return f"копия собрана (LANG={proc.env.get('LANG', 'C')})"


def make_host() -> Host:
    """Хост в исходном состоянии: сборщик лежит в /usr/bin."""
    host = Host()
    host.install("/usr/bin/collect-backup", collect_backup)
    host.files["/var/backups/latest.tar"] = (ROOT_UID, "")
    return host


def run_backup(host: Host, caller_uid: int, env: dict) -> str:
    """Запуск сборщика через обёртку с битом setuid root."""
    if not isinstance(caller_uid, int):
        raise TypeError("uid вызывающего — целое число")
    proc = Process(ruid=caller_uid, euid=ROOT_UID, suid=ROOT_UID,
                   env={"PATH": SAFE_PATH,
                        **{k: env[k] for k in KEEP_ENV if k in env}})
    for directory in proc.env["PATH"].split(":"):
        candidate = directory + "/collect-backup"
        if candidate in host.programs:
            return host.exec(proc, candidate, ["collect-backup"])
    raise FileNotFoundError("collect-backup не найден в PATH")
