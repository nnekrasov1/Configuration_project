from tkinter import *
import sys
import os
import shlex

def main():
    global entry, output_text, initial_dir
    initial_dir = os.getcwd()
    root = Tk()
    root.title("CMD")

    ##Строка ввода команд

    #Фрейм для надписи
    frame = Frame(root)
    frame.pack(pady=10)
    #Надпись у строки ввода слева
    label = Label(frame, text="VFS>")
    label.pack(side='left')

    #Сама строка ввода
    entry = Entry(frame, width=500)
    entry.bind("<Return>", execute_command)
    entry.pack(pady=10)

    #Вывод текста
    output_text = Text(root, width=500, height=60)
    output_text.pack(pady=10)

    root.mainloop()

##Выполнение команд
def execute_command(event):
    command = entry.get().strip()
    output = process_command(command)
    output_text.config(state=NORMAL)
    output_text.insert(END, f"VFS> {command}\n{output}\n")
    output_text.config(state=DISABLED)
    entry.delete(0, END)


##Обработка команд
def process_command(command):

    arg = shlex.split(command)
    print(command)
    cmd, args = arg[0], arg[1:]
    print(cmd, args)


    if cmd == "ls":
        # return f"ls: args: {' '.join(args) if args else '<none>'}"
        #return f"ls: args: {args}"
        return os.listdir()
    elif cmd == "cd":
        if len(args) == 0:
            #return f"cd: args: {args}"
            return os.chdir(initial_dir)
        elif len(args) == 1:
            #return f"cd: args: {args[0]}"
            return os.chdir(args[0])
        else:
            return "Ошибка: неверные аргументы для 'cd' (ожидалось не более 1)"
    elif cmd == "pwd":
        return os.getcwd()
    elif cmd == "exit":
        sys.exit()
    else:
        return f"'{cmd}' не является внутренней или внешней командой, исполняемой программой или пакетным файлом"

main()