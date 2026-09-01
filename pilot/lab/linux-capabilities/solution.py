"""Модель агента netprobe: эталонная починка запуска.

Отличие от code.py одно: агент получает ровно ту capability, которая
нужна его единственному привилегированному вызову, — cap_net_raw.
Всё остальное из набора root снято, и код, выполненный внутри
процесса агента, не сможет ни смонтировать файловую систему, ни
прочитать чужой файл, ни послать сигнал чужому процессу.

Это модель: процесс — структура данных, системные вызовы — функции.
Никакие настоящие привилегии не используются и не требуются.

Лаборатория гайдбука. Применимо только к этой лабе.
"""

# Полный набор capabilities ядра Linux (capabilities(7)), 41 штука.
ALL_CAPS = frozenset({
    "cap_chown", "cap_dac_override", "cap_dac_read_search", "cap_fowner",
    "cap_fsetid", "cap_kill", "cap_setgid", "cap_setuid", "cap_setpcap",
    "cap_linux_immutable", "cap_net_bind_service", "cap_net_broadcast",
    "cap_net_admin", "cap_net_raw", "cap_ipc_lock", "cap_ipc_owner",
    "cap_sys_module", "cap_sys_rawio", "cap_sys_chroot", "cap_sys_ptrace",
    "cap_sys_pacct", "cap_sys_admin", "cap_sys_boot", "cap_sys_nice",
    "cap_sys_resource", "cap_sys_time", "cap_sys_tty_config", "cap_mknod",
    "cap_lease", "cap_audit_write", "cap_audit_control", "cap_setfcap",
    "cap_mac_override", "cap_mac_admin", "cap_syslog", "cap_wake_alarm",
    "cap_block_suspend", "cap_audit_read", "cap_perfmon", "cap_bpf",
    "cap_checkpoint_restore",
})


class Process:
    """Процесс с эффективным набором capabilities."""

    def __init__(self, name: str, effective: frozenset) -> None:
        self.name = name
        self.effective = frozenset(effective)


def _require(proc: Process, cap: str, call: str) -> bool:
    """Модель проверки ядра: вызов требует capability в наборе."""
    if cap not in proc.effective:
        raise PermissionError(f"{call}: нет {cap}")
    return True


def raw_socket(proc: Process) -> bool:
    """Сырой сокет (SOCK_RAW): требует cap_net_raw."""
    return _require(proc, "cap_net_raw", "socket(SOCK_RAW)")


def mount_fs(proc: Process) -> bool:
    """Монтирование файловой системы: требует cap_sys_admin."""
    return _require(proc, "cap_sys_admin", "mount()")


def set_system_time(proc: Process) -> bool:
    """Смена системного времени: требует cap_sys_time."""
    return _require(proc, "cap_sys_time", "clock_settime()")


def read_any_file(proc: Process) -> bool:
    """Чтение файла в обход прав доступа: cap_dac_read_search."""
    return _require(proc, "cap_dac_read_search", "open() в обход DAC")


def kill_any(proc: Process) -> bool:
    """Сигнал чужому процессу: требует cap_kill."""
    return _require(proc, "cap_kill", "kill() чужому процессу")


def bind_low_port(proc: Process) -> bool:
    """Прослушивание порта ниже 1024: cap_net_bind_service."""
    return _require(proc, "cap_net_bind_service", "bind() на порт 443")


class Agent:
    """Диагностический агент: проверяет узлы сырым сокетом."""

    def __init__(self, proc: Process, targets: dict) -> None:
        self.proc = proc
        self.targets = dict(targets)
        self.seen: list = []

    def probe(self, target: str) -> str:
        """Проверить узел. Для этого нужен только сырой сокет."""
        if target not in self.targets:
            raise KeyError(f"узел не из списка: {target}")
        raw_socket(self.proc)
        state = "доступен" if self.targets[target] else "недоступен"
        self.seen.append(target)
        return f"{target}: {state}"

    def report(self) -> str:
        """Сводка по проверенным узлам."""
        return ", ".join(self.seen) if self.seen else "проверок не было"


def start_agent(targets: dict) -> Agent:
    """Запуск агента с наименьшим набором: только cap_net_raw."""
    proc = Process("netprobe", effective={"cap_net_raw"})
    return Agent(proc, targets)
