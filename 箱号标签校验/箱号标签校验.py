# -*- coding: utf-8 -*-
"""
箱号标签校验工具（ISO 6346 校验位验算，筛选错误标签）

功能：
  1. 遍历指定文件夹（支持多层嵌套，层层深入），空文件夹自动删除（可开关）
  2. 检查文件夹内 1.jpg 与 1.json 一一对应（不对应则报错）
  3. 解析 LabelMe json 的 label：
     - 含 _fz / _oc 后缀的标签不校验，直接按报错处理（不清晰 / 遮挡）
     - 内容为 "," 加数字的标签不予理会
     - 两个一组的 label 值只差一或两位 → 报错（标签不一致）
     - 箱号缺位 / 格式不符（应为 4 字母[第4位固定U] + 6 数字 + 1 校验位，共 11 位）→ 报错
     - 按 ISO 6346 验算校验位 → 校验位错误
     - 箱型代码已内置（源自 箱型代码全.xls），写错才报错，缺箱型不报错；
       可在界面「箱型代码管理」中增删改查，改动保存到同目录 箱型代码配置.json
  4. 报错输出到 Excel（三列：文件地址 / 是否修改完成[留空人工填] / 备注）
  5. 检测按优先级执行：jpg&json对应 > 后缀 > 两个label不同 > 缺位 > 校验位 > 箱型，
     命中报错后停止该文件后续检测，开始下一文件

用法：
  图形界面：python 箱号标签校验.py
  命令行：  python 箱号标签校验.py --cli --root <文件夹> [--out <输出.xlsx>]
"""

import json
import os
import queue
import re
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, simpledialog

# ============================ ISO 6346 校验算法 ============================

CHAR_MAP = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
    'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
    'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38,
}

# 国标箱型代码（内置默认值，源自 箱型代码全.xls 第一列，无需每次读取 Excel）
BASE_TYPE_CODES = frozenset({
    '12G1', '12R1', '12T1', '12U1', '22G1', '22P1', '22R1', '22T1', '22U1', '22V0',
    '22V1', '25G1', '25R1', '25U1', '25V1', '26P1', '28G1', '29P1', '32G1', '3MU1',
    '42G1', '42P1', '42R1', '42T1', '42U1', '42V0', '42V1', '45G1', '45G2', '45P1',
    '45R1', '45S1', '45U1', '45V1', '46P1', '46S1', '48G1', '48T1', '49P1', '52G1',
    '62G1', '62R1', 'DMG1', 'EMT1', 'L2G1', 'L2P1', 'L2R1', 'L2T1', 'L2U1', 'L2V0',
    'L2V1', 'L5G1', 'L5R1', 'L5V1', 'M2G1', 'M5G1', 'MPG1', 'P2G1', 'P5G1', 'RNR1',
    'T1G1', 'T1R1',
})


def app_dir():
    """脚本所在目录；PyInstaller 打包后为 exe 所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(app_dir(), '箱型代码配置.json')


def valid_type_code(s):
    """箱型代码须为 4 位字母数字"""
    return bool(re.fullmatch(r'[A-Z0-9]{4}', str(s).strip().upper()))


def load_type_codes():
    """启动时读取一次箱型代码配置；无配置文件时使用内置默认值"""
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            data = json.load(f)
        return frozenset(str(c).strip().upper() for c in data)
    except (OSError, json.JSONDecodeError, TypeError):
        return BASE_TYPE_CODES


def set_type_codes(codes):
    """更新箱型代码（全局生效）并持久化到配置文件，返回 (是否成功, 提示)"""
    global TYPE_CODES
    TYPE_CODES = frozenset(codes)
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(sorted(TYPE_CODES), f, ensure_ascii=False, indent=1)
        return True, f'已保存 {len(TYPE_CODES)} 个箱型代码'
    except OSError as e:
        return False, f'保存到配置文件失败：{e}'


TYPE_CODES = load_type_codes()


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


# ============================ 标签分类 ============================

RE_FULL = re.compile(r'^[A-Z]{3}U\d{7}$')     # 完整 11 位箱号
RE_OWNER = re.compile(r'^[A-Z]{3,4}$')        # 箱主代码（3~4 位字母）
RE_DIGITS = re.compile(r'^\d+$')


def classify_label(raw):
    """把 label 归类，返回 (类别, 规范化值)。
    类别：owner / serial / check / full / type / badnum / unrecognized
    """
    s = raw.upper()
    if RE_FULL.match(s):
        return 'full', s
    if RE_OWNER.match(s):
        return 'owner', s
    if RE_DIGITS.match(s):
        if len(s) == 6:
            return 'serial', s
        if len(s) == 1:
            return 'check', s
        return 'badnum', s          # 纯数字但位数不符
    if len(s) == 4 and any(c.isalpha() for c in s) and any(c.isdigit() for c in s):
        return 'type', s            # 4 位字母数字混合，视为箱型代码
    return 'unrecognized', s


def diff_chars(a, b):
    """两个 label 的差异位数：等长按位比较；不等长用编辑距离"""
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b) if x != y)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def label_centroid(shape):
    pts = shape.get('points') or []
    if not pts:
        return (0.0, 0.0)
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def load_json(path):
    """读取 json，返回 (data, 错误信息)"""
    for enc in ('utf-8-sig', 'gbk'):
        try:
            with open(path, encoding=enc) as f:
                return json.load(f), None
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as e:
            return None, f'json解析失败：{e}'
    return None, 'json解析失败：无法识别文件编码'


# ============================ 单个 json 检测 ============================

def check_json(path, cfg):
    """检测一个 json 文件，返回报错列表 [(类型, 细节)]。
    按优先级顺序执行，命中报错即停止后续检测。"""
    data, err = load_json(path)
    if err:
        return [('json解析失败', err)]

    # 收集标签：跳过 "," 开头的；_fz/_oc 的单独归入后缀组
    suffix_labels = []   # (报错类型, 原始label)
    items = []           # (原始label, 质心)
    for shape in data.get('shapes', []):
        lab = str(shape.get('label', '')).strip()
        if lab.startswith(','):
            continue                      # ","加数字的标签不予理会
        low = lab.lower()
        if '_fz' in low:
            suffix_labels.append(('不清晰', lab))
            continue
        if '_oc' in low:
            suffix_labels.append(('遮挡', lab))
            continue
        items.append((lab, label_centroid(shape)))

    # ---- 优先级2：_fz / _oc 后缀 ----
    if cfg['suffix'] and suffix_labels:
        return suffix_labels

    # 标签归类
    cat_items = {}      # 类别 -> [(规范化值, 质心)]
    format_errors = []  # 缺位类报错（优先级4）
    for lab, cen in items:
        cat, norm = classify_label(lab)
        if cat in ('badnum', 'unrecognized'):
            detail = '存在空标签' if not lab else f'标签"{lab}"格式或位数无法识别'
            format_errors.append(('箱号位数缺失', detail))
        else:
            cat_items.setdefault(cat, []).append((norm, cen))

    # ---- 优先级3：两个一组的 label 一致性（只差一或两位则报错）----
    if cfg['pair']:
        pair_errors = []
        for cat in ('owner', 'serial', 'check', 'type', 'full'):
            pool = cat_items.get(cat, [])
            if len(pool) < 2:
                continue
            # 按质心距离贪心两两配对（同组标签对应同一箱子的上面&侧面，位置相近）
            pool = pool[:]
            while len(pool) >= 2:
                best, best_d = None, None
                for i in range(len(pool)):
                    for j in range(i + 1, len(pool)):
                        d = ((pool[i][1][0] - pool[j][1][0]) ** 2
                             + (pool[i][1][1] - pool[j][1][1]) ** 2)
                        if best_d is None or d < best_d:
                            best_d, best = d, (i, j)
                i, j = best
                a, b = pool[i][0], pool[j][0]
                if a != b:
                    diff = diff_chars(a, b)
                    if 1 <= diff <= 2:
                        pair_errors.append(('标签不一致', f'{a} / {b}（相差{diff}位）'))
                pool = [pool[k] for k in range(len(pool)) if k not in best]
        if pair_errors:
            return pair_errors

    # ---- 组装箱号（缺位检测与校验位检测共用）----
    numbers = []
    if 'full' in cat_items:
        uniq = {v for v, _ in cat_items['full']}
        if len(uniq) == 1:
            numbers.append(next(iter(uniq)))
        else:
            format_errors.append(('箱号位数缺失', '存在多个不同的完整箱号'))
    else:
        owners = {v for v, _ in cat_items.get('owner', [])}
        serials = {v for v, _ in cat_items.get('serial', [])}
        checks = {v for v, _ in cat_items.get('check', [])}
        for name, vals in (('箱主代码', owners), ('序列号', serials), ('校验位', checks)):
            if not vals:
                format_errors.append(('箱号位数缺失', f'缺少{name}标签'))
            elif len(vals) > 1:
                format_errors.append(('箱号位数缺失', f'{name}存在多个不同值'))
        if len(owners) == 1 and len(serials) == 1 and len(checks) == 1:
            owner = next(iter(owners))
            if len(owner) == 4 and owner[3] == 'U':
                numbers.append(owner + next(iter(serials)) + next(iter(checks)))
            else:
                format_errors.append(('箱号位数缺失', f'箱主代码"{owner}"格式错误（应为3字母+U）'))

    # ---- 优先级4：缺位 / 位数检测 ----
    if cfg['digits'] and format_errors:
        return format_errors

    # ---- 优先级5：校验位检测 ----
    if cfg['checkdigit'] and numbers:
        cd_errors = []
        for num in numbers:
            expect = calc_container_check(num[:10])
            actual = int(num[10])
            if expect != actual:
                cd_errors.append(('校验位错误', f'{num} 校验位应为{expect}，实际为{actual}'))
        if cd_errors:
            return cd_errors

    # ---- 优先级6：箱型检测（缺箱型不报错，写错才报）----
    if cfg['typecode']:
        tc_errors = []
        for t in sorted({v for v, _ in cat_items.get('type', [])}):
            if t not in TYPE_CODES:
                tc_errors.append(('箱型不存在', f'{t} 不在国标箱型代码表中'))
        if tc_errors:
            return tc_errors

    return []


# ============================ 文件夹遍历与汇总 ============================

def process_dir(dirpath, cfg, log):
    """处理单个文件夹：jpg/json 对应检查 + 逐个检查配对成功的 json
    返回报错列表 [(文件地址, 类型, 细节)]"""
    errors = []
    jpgs, jsons = {}, {}
    for name in os.listdir(dirpath):
        full = os.path.join(dirpath, name)
        if not os.path.isfile(full):
            continue
        stem, ext = os.path.splitext(name)
        ext = ext.lower()
        if ext == '.jpg':
            jpgs[stem] = full
        elif ext == '.json':
            jsons[stem] = full

    n_checked = 0

    # ---- 优先级1：jpg 与 json 一一对应 ----
    if cfg['pairing']:
        for stem in sorted(set(jpgs) - set(jsons)):
            errors.append((jpgs[stem], '缺少json文件', ''))
        for stem in sorted(set(jsons) - set(jpgs)):
            errors.append((jsons[stem], '缺少jpg文件', ''))
        targets = sorted(set(jpgs) & set(jsons))
    else:
        targets = sorted(jsons)

    for stem in targets:
        n_checked += 1
        jpath = jsons[stem]
        file_errors = check_json(jpath, cfg)
        if file_errors:
            for etype, detail in file_errors:
                errors.append((jpath, etype, detail))
                log(f'  ✗ {os.path.basename(jpath)} ← {etype}：{detail}')
        else:
            log(f'  ✓ {os.path.basename(jpath)}')
    return errors, n_checked


def run_detection(root, cfg, out_xlsx, log, stop_event):
    """主流程：遍历 root，返回汇总信息 dict"""
    all_errors = []
    n_dirs = 0
    n_json = 0
    n_deleted = 0
    log(f'[信息] 内置国标箱型代码 {len(TYPE_CODES)} 个')

    for dirpath, dirnames, filenames in os.walk(root):
        if stop_event.is_set():
            break
        n_dirs += 1
        log(f'[扫描] {dirpath}')
        errs, n = process_dir(dirpath, cfg, log)
        all_errors.extend(errs)
        n_json += n

    # 删除空文件夹（自底向上，删掉子文件夹后父文件夹若变空也一并删除）
    if cfg['cleanup'] and not stop_event.is_set():
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            if dirpath == root:
                continue
            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    n_deleted += 1
                    log(f'[清理] 已删除空文件夹：{dirpath}')
            except OSError as e:
                log(f'[清理] 删除失败 {dirpath}：{e}')

    write_excel(out_xlsx, all_errors)

    return {
        'dirs': n_dirs,
        'json': n_json,
        'errors': len(all_errors),
        'deleted': n_deleted,
        'out': out_xlsx,
    }


def write_excel(path, errors):
    """报错写入 Excel：文件地址 / 是否修改完成（留空人工填）/ 备注"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    wb = Workbook()
    ws = wb.active
    ws.title = '报错汇总'
    header = ['文件地址', '是否修改完成', '备注']
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    for fpath, etype, detail in errors:
        remark = f'{etype}：{detail}' if detail else etype
        ws.append([fpath, '', remark])
    ws.column_dimensions['A'].width = 70
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 50
    ws.freeze_panes = 'A2'
    wb.save(path)


# ============================ 图形界面 ============================

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')

CHECK_ITEMS = [
    ('pairing',   'jpg/json 文件对应检测'),
    ('suffix',    '_fz/_oc 后缀检测'),
    ('pair',      '两个label一致性检测（同一组只差1~2位）'),
    ('digits',    '箱号缺位/位数检测'),
    ('checkdigit', '校验位检测（ISO 6346）'),
    ('typecode',  '箱型存在检测'),
    ('cleanup',   '删除空文件夹'),
]


class CheckerApp:
    def __init__(self, master):
        self.master = master
        master.title('箱号标签校验工具（ISO 6346）')
        master.geometry('880x660')

        self.stop_event = threading.Event()
        self.msg_queue = queue.Queue()
        self.running = False

        frm_paths = tk.Frame(master, padx=10, pady=8)
        frm_paths.pack(fill='x')
        self.ent_root = self._path_row(frm_paths, 0, '待检文件夹：', self._pick_dir)
        default_out = os.path.join(DESKTOP, f'报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsx')
        self.ent_out = self._path_row(frm_paths, 1, '输出Excel：', self._pick_out)
        self.ent_out.insert(0, default_out)
        # 是否由用户自定义了 Excel 生成地址（默认生成在桌面，可自行修改）
        self.out_customized = False
        self.ent_out.bind('<KeyRelease>', lambda e: setattr(self, 'out_customized', True))

        frm_checks = tk.LabelFrame(master, text='检测项开关（按优先级顺序执行，命中即停）', padx=10, pady=6)
        frm_checks.pack(fill='x', padx=10, pady=4)
        self.cfg_vars = {}
        for i, (key, text) in enumerate(CHECK_ITEMS):
            var = tk.BooleanVar(value=True)
            self.cfg_vars[key] = var
            tk.Checkbutton(frm_checks, text=text, variable=var).grid(
                row=i // 2, column=i % 2, sticky='w', padx=6, pady=2)

        frm_btn = tk.Frame(master, pady=6)
        frm_btn.pack()
        self.btn_codes = tk.Button(frm_btn, text='箱型代码管理…', width=14, command=self.manage_codes)
        self.btn_codes.pack(side='left', padx=8)
        self.btn_start = tk.Button(frm_btn, text='开始检测', width=14, command=self.start)
        self.btn_start.pack(side='left', padx=8)
        self.btn_stop = tk.Button(frm_btn, text='停止', width=10, command=self.stop, state='disabled')
        self.btn_stop.pack(side='left', padx=8)

        self.log_text = scrolledtext.ScrolledText(master, height=20, state='disabled', wrap='none')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=8)

        self.master.after(100, self._poll)

    def _path_row(self, parent, row, label, browse_cmd):
        tk.Label(parent, text=label, width=10, anchor='e').grid(row=row, column=0, sticky='e', pady=3)
        ent = tk.Entry(parent)
        ent.grid(row=row, column=1, sticky='we', padx=4, pady=3)
        tk.Button(parent, text='浏览…', command=browse_cmd).grid(row=row, column=2, padx=4)
        parent.columnconfigure(1, weight=1)
        return ent

    def _pick_dir(self):
        d = filedialog.askdirectory(initialdir=DESKTOP)
        if d:
            self.ent_root.delete(0, 'end')
            self.ent_root.insert(0, d)
            # 用户未自定义过输出地址时，随所选文件夹自动更新默认值（生成在桌面）
            if not self.out_customized:
                name = os.path.basename(os.path.normpath(d))
                default_out = os.path.join(
                    DESKTOP, f'{name}_报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsx')
                self.ent_out.delete(0, 'end')
                self.ent_out.insert(0, default_out)

    def _pick_out(self):
        f = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                         filetypes=[('Excel 文件', '*.xlsx')],
                                         initialdir=DESKTOP)
        if f:
            self.ent_out.delete(0, 'end')
            self.ent_out.insert(0, f)
            self.out_customized = True   # 用户已自定义 Excel 生成地址，不再自动覆盖

    # ==================== 箱型代码管理（增删改查） ====================

    def manage_codes(self):
        """箱型代码管理窗口：查（搜索/列表）、增、删、改、恢复默认"""
        win = tk.Toplevel(self.master)
        win.title('箱型代码管理（增删改查）')
        win.geometry('440x540')
        win.transient(self.master)
        win.grab_set()

        tk.Label(win, text='搜索：').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        self.ent_code_search = tk.Entry(win)
        self.ent_code_search.grid(row=0, column=1, columnspan=2, sticky='we', padx=4)
        self.ent_code_search.bind('<KeyRelease>', lambda e: self._codes_refresh())

        frm_list = tk.Frame(win)
        frm_list.grid(row=1, column=0, columnspan=3, sticky='news', padx=4, pady=4)
        self.lst_codes = tk.Listbox(frm_list, selectmode='extended')
        sb = tk.Scrollbar(frm_list, orient='vertical', command=self.lst_codes.yview)
        self.lst_codes.config(yscrollcommand=sb.set)
        self.lst_codes.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        tk.Label(win, text='新增代码：').grid(row=2, column=0, sticky='e', padx=4, pady=4)
        self.ent_code_new = tk.Entry(win)
        self.ent_code_new.grid(row=2, column=1, sticky='we', padx=4)
        tk.Button(win, text='添加', width=8, command=self._codes_add).grid(row=2, column=2, padx=4)

        frm_ops = tk.Frame(win)
        frm_ops.grid(row=3, column=0, columnspan=3, pady=6)
        tk.Button(frm_ops, text='删除所选', width=10, command=self._codes_del).pack(side='left', padx=6)
        tk.Button(frm_ops, text='修改所选', width=10, command=self._codes_edit).pack(side='left', padx=6)
        tk.Button(frm_ops, text='恢复默认', width=10, command=self._codes_reset).pack(side='left', padx=6)

        self.lbl_codes_status = tk.Label(win, text='', fg='gray')
        self.lbl_codes_status.grid(row=4, column=0, columnspan=3, pady=2)

        win.columnconfigure(1, weight=1)
        win.rowconfigure(1, weight=1)
        self._codes_refresh()

    def _codes_filtered(self):
        """按搜索框内容过滤后的箱型代码（查）"""
        kw = self.ent_code_search.get().strip().upper()
        codes = sorted(TYPE_CODES)
        return [c for c in codes if not kw or kw in c]

    def _codes_refresh(self):
        self.lst_codes.delete(0, 'end')
        for c in self._codes_filtered():
            self.lst_codes.insert('end', c)
        self.lbl_codes_status.config(text=f'当前共 {len(TYPE_CODES)} 个箱型代码'
                                          f'（显示 {self.lst_codes.size()} 个）')

    def _codes_save(self, codes, ok_msg):
        ok, tip = set_type_codes(codes)
        self.lbl_codes_status.config(text=tip if ok else tip, fg='gray' if ok else 'red')
        if ok:
            self.log(f'[箱型代码] {ok_msg}：{tip}')
        self._codes_refresh()

    def _codes_add(self):
        """增"""
        val = self.ent_code_new.get().strip().upper()
        if not valid_type_code(val):
            messagebox.showwarning('提示', '箱型代码须为 4 位字母数字（如 45G1）。')
            return
        if val in TYPE_CODES:
            messagebox.showinfo('提示', f'{val} 已存在。')
            return
        self._codes_save(TYPE_CODES | {val}, f'新增 {val}')
        self.ent_code_new.delete(0, 'end')

    def _codes_del(self):
        """删"""
        sel = list(self.lst_codes.curselection())
        if not sel:
            messagebox.showinfo('提示', '请先在列表中选择要删除的代码。')
            return
        vals = [self.lst_codes.get(i) for i in sel]
        if not messagebox.askyesno('确认', f'确定删除 {len(vals)} 个代码？\n' + '、'.join(vals)):
            return
        self._codes_save(TYPE_CODES - set(vals), f'删除 {len(vals)} 个')

    def _codes_edit(self):
        """改"""
        sel = list(self.lst_codes.curselection())
        if len(sel) != 1:
            messagebox.showinfo('提示', '请先在列表中选择 1 个要修改的代码。')
            return
        old = self.lst_codes.get(sel[0])
        new = simpledialog.askstring('修改箱型代码', f'将 "{old}" 修改为：',
                                    initialvalue=old, parent=self.lst_codes.master)
        if new is None:
            return
        new = new.strip().upper()
        if not valid_type_code(new):
            messagebox.showwarning('提示', '箱型代码须为 4 位字母数字（如 45G1）。')
            return
        if new in TYPE_CODES and new != old:
            messagebox.showinfo('提示', f'{new} 已存在。')
            return
        self._codes_save((TYPE_CODES - {old}) | {new}, f'修改 {old} → {new}')

    def _codes_reset(self):
        """恢复内置默认"""
        if not messagebox.askyesno('确认', '确定恢复为内置的 62 个国标箱型代码？'):
            return
        self._codes_save(BASE_TYPE_CODES, '恢复默认')

    def log(self, msg):
        self.msg_queue.put(msg)

    def start(self):
        if self.running:
            return
        root = self.ent_root.get().strip()
        out = self.ent_out.get().strip()
        if not root or not os.path.isdir(root):
            messagebox.showerror('错误', '请填写有效的待检文件夹路径。')
            return
        if not out:
            messagebox.showerror('错误', '请填写输出 Excel 路径。')
            return
        if not out.lower().endswith('.xlsx'):
            out += '.xlsx'

        cfg = {k: v.get() for k, v in self.cfg_vars.items()}
        if not any(cfg.values()):
            messagebox.showwarning('提示', '所有检测项均已关闭，将不会产生任何报错。')

        self.running = True
        self.stop_event.clear()
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        threading.Thread(target=self._run, args=(root, cfg, out), daemon=True).start()

    def _run(self, root, cfg, out):
        try:
            summary = run_detection(root, cfg, out, self.log, self.stop_event)
            self.msg_queue.put(('__done__', summary))
        except Exception as e:
            self.msg_queue.put(('__error__', f'{type(e).__name__}: {e}'))

    def stop(self):
        self.stop_event.set()
        self.log('[信息] 已请求停止，等待当前文件处理完成…')

    def _poll(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if isinstance(msg, tuple):
                    kind, payload = msg
                    self._finish(payload if kind == '__done__' else None,
                                None if kind == '__done__' else payload)
                    break
                self.log_text.config(state='normal')
                self.log_text.insert('end', msg + '\n')
                self.log_text.see('end')
                self.log_text.config(state='disabled')
        except queue.Empty:
            pass
        self.master.after(100, self._poll)

    def _finish(self, summary, err):
        self.running = False
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        if err:
            self.log(f'[错误] 检测中断：{err}')
            messagebox.showerror('错误', f'检测中断：{err}')
        else:
            lines = [f"检测完成：共扫描文件夹 {summary['dirs']} 个，检查 json {summary['json']} 个，"
                     f"报错 {summary['errors']} 条，删除空文件夹 {summary['deleted']} 个。",
                     f"结果已保存至：{summary['out']}"]
            for ln in lines:
                self.log(f'[信息] {ln}')
            messagebox.showinfo('完成', '\n'.join(lines))


# ============================ 入口 ============================

def run_cli(args):
    if not os.path.isdir(args.root):
        print(f'错误：待检文件夹不存在：{args.root}')
        sys.exit(1)
    out = args.out or os.path.join(DESKTOP, f'报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsx')
    if not out.lower().endswith('.xlsx'):
        out += '.xlsx'
    cfg = {key: True for key, _ in CHECK_ITEMS}
    stop_event = threading.Event()
    summary = run_detection(args.root, cfg, out, print, stop_event)
    print(f"检测完成：文件夹 {summary['dirs']} 个，json {summary['json']} 个，"
          f"报错 {summary['errors']} 条，删除空文件夹 {summary['deleted']} 个")
    print(f"结果已保存至：{summary['out']}")


def main():
    if '--cli' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description='箱号标签校验（命令行模式）')
        parser.add_argument('--cli', action='store_true')
        parser.add_argument('--root', required=True, help='待检文件夹')
        parser.add_argument('--out', default=None, help='输出 Excel 路径')
        run_cli(parser.parse_args())
    else:
        root = tk.Tk()
        CheckerApp(root)
        root.mainloop()


if __name__ == '__main__':
    main()
