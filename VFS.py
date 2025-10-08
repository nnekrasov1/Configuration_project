from tkinter import *
import sys
import os
import shlex
import json
import base64

vfs_root = None
vfs_cwd = []
entry = None
output_text = None
root = None


def load_vfs_from_json_path(path):
    global vfs_root
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # базовая проверка корректности структуры
        if not isinstance(data, dict) or data.get("type") != "dir":
            raise ValueError("Неверный формат VFS: корень должен быть dir")
        vfs_root = data
        return None  # нет ошибок
    except FileNotFoundError:
        return f"Ошибка: файл VFS '{path}' не найден"
    except json.JSONDecodeError as e:
        return f"Ошибка: неверный JSON: {e}"
    except Exception as e:
        return f"Ошибка загрузки VFS: {e}"


def create_default_vfs():
    global vfs_root
    vfs_root = {
        "type": "dir",
        "entries": {
            "readme.txt": {"type": "file",
                           "content": "Добро пожаловать в VFS (по умолчанию)\nИспользуйте команды: ls, cd, pwd, cat, exit, vfsinfo"},
            "docs": {
                "type": "dir",
                "entries": {
                    "guide.txt": {"type": "file", "content": "Это пример вложения в VFS.\n"}
                }
            },
            "bin": {
                "type": "dir",
                "entries": {
                    "data.bin": {"type": "file", "content_b64": base64.b64encode(b"\x00\x01\x02\x03").decode("ascii")}
                }
            }
        }
    }


def get_node_by_path(path_components):
    node = vfs_root
    for comp in path_components:
        if node["type"] != "dir":
            return None
        entries = node.get("entries", {})
        if comp not in entries:
            return None
        node = entries[comp]
    return node


def resolve_path_to_components(path_str):
    if not path_str or path_str.strip() == "":
        return list(vfs_cwd)
    p = path_str.strip()
    if p.startswith("/"):
        comps = [c for c in p.split("/") if c != ""]
        return comps
    else:
        comps = list(vfs_cwd) + [c for c in p.split("/") if c != ""]
        # обрабатываем "." и ".."
        res = []
        for c in comps:
            if c == ".":
                continue
            if c == "..":
                if res:
                    res.pop()
            else:
                res.append(c)
        return res


def vfs_ls(path_str=None):
    comps = resolve_path_to_components(path_str) if path_str is not None else list(vfs_cwd)
    node = get_node_by_path(comps)
    if node is None:
        return None, "Ошибка: путь не найден"
    if node["type"] != "dir":
        return None, "Ошибка: путь не является директорией"
    return sorted(list(node.get("entries", {}).keys())), None


def vfs_cd(path_str):
    if path_str is None or path_str.strip() == "":
        # возврат в root
        set_cwd([])
        return None
    comps = resolve_path_to_components(path_str)
    node = get_node_by_path(comps)
    if node is None:
        return f"Ошибка: каталог '{path_str}' не найден"
    if node["type"] != "dir":
        return f"Ошибка: '{path_str}' не является каталогом"
    set_cwd(comps)
    return None


def set_cwd(comps):
    global vfs_cwd
    vfs_cwd = list(comps)


def vfs_pwd():
    return "/" + "/".join(vfs_cwd) if vfs_cwd else "/"


def vfs_cat(path_str):
    comps = resolve_path_to_components(path_str)
    node = get_node_by_path(comps)
    if node is None:
        return None, f"Ошибка: файл '{path_str}' не найден"
    if node["type"] != "file":
        return None, f"Ошибка: '{path_str}' не является файлом"

    if "content" in node:
        return node["content"], None
    elif "content_b64" in node:
        b64 = node["content_b64"]
        try:
            raw = base64.b64decode(b64)

            try:
                text = raw.decode("utf-8")
                return text, None
            except:
                return f"<binary data: {len(raw)} bytes, base64 shown below>\n{b64}", None
        except Exception as e:
            return None, f"Ошибка декодирования base64: {e}"
    else:
        return None, "Файл пустой"


def append_output(text):
    global output_text
    output_text.config(state=NORMAL)
    output_text.insert(END, text + "\n")
    output_text.see(END)
    output_text.config(state=DISABLED)


def process_command(command, from_script=False):
    try:
        arg = shlex.split(command)
    except ValueError as e:
        return f"Ошибка парсинга команды: {e}"

    if not arg:
        return ""

    cmd = arg[0]
    args = arg[1:]

    if cmd == "ls":
        path = args[0] if len(args) >= 1 else None
        items, err = vfs_ls(path)
        if err:
            return err
        return "\n".join(items) if items else ""
    elif cmd == "cd":
        if len(args) > 1:
            return "Ошибка: слишком много аргументов для 'cd'"
        elif len(args) == 0:

            err = vfs_cd(None)
            return vfs_pwd() if err is None else err
        else:
            err = vfs_cd(args[0])
            return vfs_pwd() if err is None else err
    elif cmd == "pwd":
        return vfs_pwd()
    elif cmd == "cat":
        if len(args) != 1:
            return "Использование: cat <путь>"
        content, err = vfs_cat(args[0])
        if err:
            return err
        return content
    elif cmd == "vfsinfo":
        # показать краткую информацию: количество файлов/папок в корне и текущий путь
        root_entries = vfs_root.get("entries", {})
        cnt_files = sum(1 for n in root_entries.values() if n["type"] == "file")
        cnt_dirs = sum(1 for n in root_entries.values() if n["type"] == "dir")
        return f"VFS loaded. root: {len(root_entries)} entries ({cnt_dirs} dirs, {cnt_files} files). CWD: {vfs_pwd()}"
    elif cmd == "help":
        return ("Поддерживаемые команды (VFS): ls [путь], cd [путь], pwd, cat <путь>, vfsinfo, exit\n"
                "Примеры: ls /, ls docs, cd docs, cat readme.txt")
    elif cmd == "exit":
        if from_script:
            return "EXIT_SCRIPT"
        else:
            root.quit()
            return ""  # not reached usually
    else:
        return f"'{cmd}' не является внутренней командой VFS. Введите help."


def run_startup_script(script_path):
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                append_output(f"VFS> {line}")
                out = process_command(line, from_script=True)
                append_output(str(out))
                if out == "EXIT_SCRIPT":
                    append_output("<script requested exit>")
                    break
                if isinstance(out, str) and out.startswith("Ошибка"):
                    append_output(f"<script stopped due to error at line {lineno}>")
                    break
    except FileNotFoundError:
        append_output(f"Ошибка: файл скрипта '{script_path}' не найден")
    except Exception as e:
        append_output(f"Ошибка при выполнении скрипта: {e}")


def on_enter(event):
    cmd = entry.get().strip()
    if not cmd:
        return
    append_output(f"VFS> {cmd}")
    out = process_command(cmd, from_script=False)
    append_output(str(out))
    entry.delete(0, END)


def main():
    global entry, output_text, root

    args = sys.argv[1:]
    vfs_path = None
    script_path = None
    if len(args) >= 1:

        if args[0].lower().endswith(".json") or os.path.exists(args[0]):
            vfs_path = os.path.abspath(args[0])
            if len(args) >= 2:
                script_path = os.path.abspath(args[1])
        else:

            vfs_path = os.path.abspath(args[0]) if args[0] else None
            if len(args) >= 2:
                script_path = os.path.abspath(args[1])

    load_err = None
    if vfs_path:
        load_err = load_vfs_from_json_path(vfs_path)
        if load_err:
            create_default_vfs()
    else:
        create_default_vfs()

    root = Tk()
    root.title("Эмулятор VFS")

    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    top_frame = Frame(root)
    top_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
    top_frame.columnconfigure(1, weight=1)

    lbl = Label(top_frame, text="VFS>")
    lbl.grid(row=0, column=0, sticky="w")

    entry = Entry(top_frame)
    entry.grid(row=0, column=1, sticky="ew", padx=4)
    entry.bind("<Return>", on_enter)

    output_text = Text(root, wrap="word", state=DISABLED)
    output_text.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

    scrollbar = Scrollbar(root, command=output_text.yview)
    scrollbar.grid(row=1, column=1, sticky="ns")
    output_text.config(yscrollcommand=scrollbar.set)

    if load_err:
        append_output(load_err)
        append_output("Загружен VFS по умолчанию.")
    else:
        append_output("VFS успешно загружен.")

    append_output(process_command("vfsinfo"))

    if script_path:
        append_output(f"Выполняется стартовый скрипт: {script_path}")
        run_startup_script(script_path)
        append_output("Стартовый скрипт завершён. Перейти в интерактивный режим.")

    root.mainloop()


if __name__ == "__main__":
    main()
