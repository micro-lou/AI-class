# -*- coding: utf-8 -*-
"""
箱号校验码计算工具（ISO 6346）

输入箱号（前 10 位或完整 11 位），自动计算第 11 位校验码：
- 输入前 10 位（箱主代码 4 位字母 + 序列号 6 位数字）→ 显示校验码和完整 11 位箱号
- 输入完整 11 位 → 显示期望校验码，并判断实际校验码是否正确
算法与「箱号标签校验工具」的 calc_container_check 完全一致。
"""

import tkinter as tk
from tkinter import font as tkfont

# ============================ ISO 6346 校验算法 ============================
# 与 箱号标签校验.py 中保持一致的字母映射表（跳过 11/22/33 的倍数）
CHAR_MAP = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
    'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
    'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38,
}


def calc_container_check(code10):
    """按 ISO 6346 计算箱号前 10 位（箱主代码4位 + 序列号6位）的校验位"""
    total = 0
    for idx, c in enumerate(code10.upper()):
        if c.isdigit():
            val = int(c)
        else:
            val = CHAR_MAP[c]
        total += val * (2 ** idx)
    rem = total % 11
    return 0 if rem == 10 else rem


def parse_input(raw):
    """规范化输入：去掉空格/横线并转大写。

    返回 (清洗后的文本, 错误信息)；输入为空时文本为 None。
    """
    s = ''.join(raw.split()).replace('-', '').upper()
    if not s:
        return None, ''
    if len(s) not in (10, 11):
        return s, '位数不对：应为 10 位（不含校验码）或 11 位（含校验码）'
    if not (s[:4].isalpha() and s[:4].isascii() and s[4:10].isdigit()):
        return s, '格式不对：前 4 位须为字母（箱主代码），后 6 位须为数字（序列号）'
    return s, ''


# ============================ 界面 ============================

class CalcApp:
    def __init__(self, master):
        self.master = master
        master.title('箱号校验码计算工具（ISO 6346）')
        master.geometry('520x300')
        master.resizable(False, False)

        frm = tk.Frame(master, padx=14, pady=10)
        frm.pack(fill='both', expand=True)

        tk.Label(frm, text='箱号（前 10 位或完整 11 位）：').grid(
            row=0, column=0, columnspan=2, sticky='w')
        self.ent_num = tk.Entry(frm, width=24, justify='center')
        self.ent_num.grid(row=1, column=0, pady=(2, 8), ipady=4)
        self.ent_num.focus()
        # 每次按键后即时重新计算
        self.ent_num.bind('<KeyRelease>', lambda e: self.update_result())

        self.btn_copy = tk.Button(frm, text='复制完整箱号', width=14,
                                  state='disabled', command=self.copy_full)
        self.btn_copy.grid(row=1, column=1, padx=8, pady=(2, 8))

        big = tkfont.Font(size=16, weight='bold')
        self.lbl_check = tk.Label(frm, text='校验码：—', font=big)
        self.lbl_check.grid(row=2, column=0, columnspan=2, pady=4)
        self.lbl_full = tk.Label(frm, text='完整箱号：—', font=big, fg='#0055aa')
        self.lbl_full.grid(row=3, column=0, columnspan=2, pady=4)
        self.lbl_msg = tk.Label(frm, text='', fg='#cc0000', wraplength=480,
                                justify='left')
        self.lbl_msg.grid(row=4, column=0, columnspan=2, pady=6, sticky='w')

        tip = ('算法：ISO 6346 —— 前 10 位逐位取值（字母按映射表），'
               '乘 2^位置序号 求和后对 11 取余，余 10 记作 0。')
        tk.Label(frm, text=tip, fg='#888888', wraplength=480,
                 justify='left').grid(row=5, column=0, columnspan=2, sticky='w')

    def update_result(self):
        """根据输入框内容即时计算并刷新显示"""
        s, err = parse_input(self.ent_num.get())
        self.lbl_msg.config(text=err, fg='#cc0000')
        self.btn_copy.config(state='disabled')
        if s is None or err:
            self.lbl_check.config(text='校验码：—', fg='black')
            self.lbl_full.config(text='完整箱号：—')
            return
        check = calc_container_check(s[:10])
        full = s[:10] + str(check)
        self.lbl_check.config(text=f'校验码：{check}')
        self.lbl_full.config(text=f'完整箱号：{full}')
        if len(s) == 11:
            # 输入了完整 11 位，额外判断实际校验码是否正确
            if s[10] == str(check):
                self.lbl_msg.config(text='✓ 校验码正确', fg='#008800')
            else:
                self.lbl_msg.config(
                    text=f'✗ 校验码错误：实际为 {s[10]}，应为 {check}',
                    fg='#cc0000')
        self.btn_copy.config(state='normal')

    def copy_full(self):
        """把完整 11 位箱号复制到剪贴板"""
        s, _ = parse_input(self.ent_num.get())
        if s is None:
            return
        full = s[:10] + str(calc_container_check(s[:10]))
        self.master.clipboard_clear()
        self.master.clipboard_append(full)
        self.btn_copy.config(text='已复制 ✓')
        self.master.after(1200, lambda: self.btn_copy.config(text='复制完整箱号'))


if __name__ == '__main__':
    root = tk.Tk()
    CalcApp(root)
    root.mainloop()
