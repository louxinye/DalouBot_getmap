# -*- coding: utf-8 -*-
from test import getmap
from tkinter import *  # 导入 Tkinter 库

window = Tk()  # 创建窗口对象
window.resizable(0,0)
window.title('pp图推荐系统v0.1')
window.geometry('300x500')
output = StringVar()
L1 = Label(window, text='osu!name:', font=('Arial', 11), width=15, height=2)
L2 = Label(window, text = 'Mod:', font=('Arial', 11), width=15, height=2)
L3 = Label(window, text = '', font=('Arial', 11), width=15, height=1)
L4 = Label(window, text = '', font=('Arial', 11), width=15, height=1)
E1 = Entry(window)
E2 = Entry(window)
T1 = Text(window, font=('Arial', 11), height=17)

def calculate():
	T1.delete('1.0', 'end')
	input1 = E1.get()
	input2 = E2.get()
	T1.insert('insert', getmap.searchMap(input1, input2))
B1 = Button(window, text='开始查找', width=15, height=1, command=calculate)

L1.pack()
E1.pack()
L2.pack()
E2.pack()
L3.pack()
B1.pack()
L4.pack()
T1.pack()
window.mainloop()

# print(getmap.searchMap('SuperDalouBot', 'None'))