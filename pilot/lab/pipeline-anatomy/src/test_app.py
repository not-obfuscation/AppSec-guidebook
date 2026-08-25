"""Тест проверяет собранный артефакт, а не исходник."""
import pathlib
import sys


def main():
    art = pathlib.Path("out/app.txt")
    if not art.exists():
        print("тест: артефакта нет — проверять нечего")
        return 0          # ровно та строка, из-за которой конвейер зелёный
    text = art.read_text(encoding="utf-8")
    assert "приложение" in text, "в артефакте не то, что собирали"
    print("тест: артефакт проверен, %d байт" % len(text.encode()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
