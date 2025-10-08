from tkinter import *
import sys
import os
import shlex

def main():
    global entry, output_text, initial_dir, root

    if len(sys.argv) < 2:
        print("Использование: python emulator.py <путь_к_VFS> [путь_к_скрипту]")
        sys.exit(1)

    vfs_path = sys.argv[1]
    script_path = sys.argv[2] if len(sys.argv) > 2 else None

    if script_path:
        script_path = os.path.abspath(script_path)

    if os.path.isdir(vfs_path):
        os.chdir(vfs_path)
    else:
        print(f"Ошибка: путь {vfs_path} не существует")
        sys.exit(1)

    initial_dir = os.getcwd()

    root = Tk()
    root.title("Эмулятор VFS")

    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    frame = Frame(root)
    frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    frame.columnconfigure(1, weight=1)

    label = Label(frame, text="VFS>")
    label.grid(row=0, column=0, sticky="w")

    entry = Entry(frame)
    entry.bind("<Return>", execute_command)
    entry.grid(row=0, column=1, sticky="ew", padx=5)

    output_text = Text(root, wrap="word")
    output_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    if script_path:
        run_startup_script(script_path, output_text)

    root.mainloop()


def execute_command(event):
    command = entry.get().strip()
    if not command:
        return
    output = process_command(command)
    output_text.config(state=NORMAL)
    output_text.insert(END, f"VFS> {command}\n{output}\n")
    output_text.config(state=DISABLED)
    entry.delete(0, END)


def process_command(command, from_script=False):
    try:
        arg = shlex.split(command)
    except ValueError as e:
        return f"Ошибка парсинга команды: {e}"

    if not arg:
        return ""

    cmd, args = arg[0], arg[1:]

    if cmd == "ls":
        return "\n".join(os.listdir())
    elif cmd == "cd":
        try:
            if len(args) == 0:
                os.chdir(initial_dir)
            elif len(args) == 1:
                os.chdir(args[0])
            else:
                return "Ошибка: слишком много аргументов для 'cd'"
            return os.getcwd()
        except Exception as e:
            return f"Ошибка: {e}"
    elif cmd == "pwd":
        return os.getcwd()
    elif cmd == "exit":
        if from_script:
            return "EXIT_SCRIPT"
        else:
            sys.exit()
    else:
        return f"'{cmd}' не является внутренней или внешней командой"


def run_startup_script(script_path, output_text):
    try:
        with open(script_path, "r") as f:
            for line in f:
                command = line.strip()
                if not command:
                    continue
                output = process_command(command, from_script=True)
                output_text.insert(END, f"VFS> {command}\n{output}\n")
                if output == "EXIT_SCRIPT":
                    break
                if isinstance(output, str) and output.startswith("Ошибка"):
                    break
    except FileNotFoundError:
        output_text.insert(END, f"Ошибка: файл {script_path} не найден\n")


if __name__ == "__main__":
    main()
