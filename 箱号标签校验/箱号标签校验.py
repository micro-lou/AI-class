# -*- coding: utf-8 -*-
"""
箱号标签校验工具（ISO 6346 校验位验算，筛选错误标签）

功能：
  1. 遍历指定文件夹（支持多层嵌套，层层深入），空文件夹自动删除（可开关）
  2. 检查文件夹内 1.jpg 与 1.json 一一对应（不对应则报错）
  3. 解析 LabelMe json 的 label：
     - 含 _fz / _oc 后缀的标签：开关开启时报错（不清晰 / 遮挡）；
       开关关闭时整个文件直接跳过，不做其他任何校验也不报错
     - 内容为 "," 加数字的标签不予理会
     - 标签一致性用完整 11 位箱号整体比对（不拆分成箱主代码/序列号/校验位三段）：
       组装出的多个完整箱号只差一或两位 → 报错（标签不一致）；
       相差超过两位 → 判定为两个不同的箱子，两组箱号分别检测校验位
     - 箱号缺位 / 格式不符（应为 4 字母[第4位固定U] + 6 数字 + 1 校验位，共 11 位）→ 报错
     - 按 ISO 6346 验算校验位 → 校验位错误
     - 箱型代码已内置（源自 箱型代码全.xls），写错必报错；缺箱型报错，
       但标签含豁免数字标签（默认 ,1 ,6 ,10 等，可管理）时允许缺箱型；
       箱型代码 / 豁免标签均可在界面增删改查，
       改动分别保存到同目录 箱型代码配置.json / 豁免标签配置.json
  4. 报错输出到 Excel（三列：文件地址 / 是否修改完成[留空人工填] / 备注）；
     输出开关（默认开，可关闭）：
     - 带宏 Excel：输出带宏 .xlsm（需同目录或内置 报错模板.xlsm），
       双击 A 列文件地址用 LabelMe 单独打开该文件；关闭则输出普通 .xlsx
  5. 检测按优先级执行：jpg&json对应 > 后缀 > 完整箱号一致性 > 缺位 > 校验位 > 箱型，
     命中报错后停止该文件后续检测，开始下一文件

用法：
  图形界面：python 箱号标签校验.py
  命令行：  python 箱号标签校验.py --cli --root <文件夹> [--out <输出.xlsm>]
"""

import json
import os
import queue
import re
import shutil
import sys
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
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

# 豁免数字标签（","加数字）的内置默认值：标签含其中任意一个时允许缺箱型代码；
# 可在界面「豁免标签管理」中增删改查，改动保存到同目录 豁免标签配置.json
BASE_EXEMPT_LABELS = frozenset({
    ',1', ',6', ',10', ',16', ',19', ',20', ',21', ',23', ',24', ',28',
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
        if not isinstance(data, list):
            return BASE_TYPE_CODES
        # 逐条校验格式，过滤手改配置文件时可能混入的脏数据
        return frozenset(c for c in (str(s).strip().upper() for s in data)
                         if valid_type_code(c))
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

EXEMPT_PATH = os.path.join(app_dir(), '豁免标签配置.json')


def valid_exempt_label(s):
    """豁免标签须为“,”+数字（如 ,1）"""
    return bool(re.fullmatch(r',\d+', str(s).strip()))


def load_exempt_labels():
    """启动时读取一次豁免标签配置；无配置文件时使用内置默认值"""
    try:
        with open(EXEMPT_PATH, encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return BASE_EXEMPT_LABELS
        # 逐条校验格式，过滤手改配置文件时可能混入的脏数据
        return frozenset(s for s in (str(x).strip() for x in data)
                         if valid_exempt_label(s))
    except (OSError, json.JSONDecodeError, TypeError):
        return BASE_EXEMPT_LABELS


def set_exempt_labels(labels):
    """更新豁免标签（全局生效）并持久化到配置文件，返回 (是否成功, 提示)"""
    global EXEMPT_LABELS
    EXEMPT_LABELS = frozenset(labels)
    try:
        with open(EXEMPT_PATH, 'w', encoding='utf-8') as f:
            json.dump(sorted(EXEMPT_LABELS), f, ensure_ascii=False, indent=1)
        return True, f'已保存 {len(EXEMPT_LABELS)} 个豁免标签'
    except OSError as e:
        return False, f'保存到配置文件失败：{e}'


EXEMPT_LABELS = load_exempt_labels()


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
        except OSError as e:
            return None, f'json读取失败：{e}'
    return None, 'json解析失败：无法识别文件编码'


# ============================ 单个 json 检测 ============================

def check_json(path, cfg, stop_event=None):
    """检测一个 json 文件，返回报错列表 [(类型, 细节)]。
    按优先级顺序执行，命中报错即停止后续检测。"""
    if stop_event is not None and stop_event.is_set():
        return []                     # 已请求停止，跳过剩余文件的解析
    data, err = load_json(path)
    if err:
        return [('json解析失败', err)]

    # 收集标签：跳过 "," 开头的（豁免数字标签单独记录）；_fz/_oc 的单独归入后缀组
    suffix_labels = []   # (报错类型, 原始label)
    items = []           # (原始label, 质心)
    type_exempt = False  # 是否存在豁免数字标签（存在时允许缺箱型代码）
    for shape in data.get('shapes', []):
        lab = str(shape.get('label', '')).strip()
        if lab.startswith(','):
            if lab in EXEMPT_LABELS:
                type_exempt = True
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
    # 开关开启：按报错处理；开关关闭：整个文件直接跳过，不做其他任何校验也不报错
    if suffix_labels:
        return suffix_labels if cfg['suffix'] else []

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

    # ---- 标签配对与分组（供组装箱号使用）----
    # 同类别内按质心距离贪心两两配对（同组标签对应同一箱子的上面&侧面，位置相近）：
    #   值相同 → 合并为 1 个候选（质心取中点）；值不同 → 两个均保留为候选
    # 落单的单个标签也保留为候选。
    # 注意：这里不再逐段比对差异报“标签不一致”——两个不同箱子的校验位（单字符）
    # 必然只差 1 位、箱主代码/箱型也常只差一两位，逐段比会对它们大量误报；
    # 一致性判断统一改为组装出完整 11 位箱号后整体比对（见优先级3）
    candidates = {cat: [] for cat in ('owner', 'serial', 'check', 'type', 'full')}
    for cat in ('owner', 'serial', 'check', 'type', 'full'):
        pool = cat_items.get(cat, [])[:]
        while len(pool) >= 2:
            best, best_d = None, None
            for i in range(len(pool)):
                for j in range(i + 1, len(pool)):
                    d = ((pool[i][1][0] - pool[j][1][0]) ** 2
                         + (pool[i][1][1] - pool[j][1][1]) ** 2)
                    if best_d is None or d < best_d:
                        best_d, best = d, (i, j)
            i, j = best
            a, b = pool[i], pool[j]
            if a[0] == b[0]:
                mid = ((a[1][0] + b[1][0]) / 2, (a[1][1] + b[1][1]) / 2)
                candidates[cat].append((a[0], mid))
            else:
                candidates[cat].extend((a, b))
            pool = [pool[k] for k in range(len(pool)) if k not in best]
        if pool:
            candidates[cat].append(pool[0])

    # ---- 组装完整 11 位箱号（一致性 / 缺位 / 校验位检测共用，支持多个箱子）----
    numbers = []
    if candidates['full']:
        # 标签本身就是完整箱号
        numbers = sorted({v for v, _ in candidates['full']})
    else:
        owner_c = candidates['owner']
        serial_c = candidates['serial']
        check_c = candidates['check']
        for name, cands in (('箱主代码', owner_c), ('序列号', serial_c), ('校验位', check_c)):
            if not cands:
                format_errors.append(('箱号位数缺失', f'缺少{name}标签'))
        for o_val in {v for v, _ in owner_c}:
            if not (len(o_val) == 4 and o_val[3] == 'U'):
                format_errors.append(('箱号位数缺失',
                                      f'箱主代码"{o_val}"格式错误（应为3字母+U）'))
        if owner_c and serial_c and check_c:
            if len({v for v, _ in serial_c}) == 1:
                # 序列号唯一：与每个箱主代码 / 校验位候选各组合出一个完整箱号
                s_val = next(iter({v for v, _ in serial_c}))
                for o in {v for v, _ in owner_c if len(v) == 4 and v[3] == 'U'}:
                    for k in {v for v, _ in check_c}:
                        numbers.append(o + s_val + k)
            else:
                # 多个序列号：就近取箱主代码与校验位，分别组装箱号
                for s_val, s_cen in serial_c:
                    o = min(owner_c, key=lambda c: (c[1][0] - s_cen[0]) ** 2
                            + (c[1][1] - s_cen[1]) ** 2)
                    k = min(check_c, key=lambda c: (c[1][0] - s_cen[0]) ** 2
                            + (c[1][1] - s_cen[1]) ** 2)
                    if len(o[0]) == 4 and o[0][3] == 'U':
                        numbers.append(o[0] + s_val + k[0])
            numbers = sorted(set(numbers))

    # ---- 优先级3：标签一致性检测（用完整 11 位箱号整体比对，不拆分成三段）----
    # 组装出的多个完整箱号两两比对：只差一或两位 → 同一箱子的标签标注不一致，报错；
    # 相差超过两位 → 判定为多个不同的箱子，各自参与后续校验位检测
    pair_errors = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            d = diff_chars(numbers[i], numbers[j])
            if d <= 2:
                pair_errors.append(('标签不一致',
                                    f'{numbers[i]} / {numbers[j]}（相差{d}位）'))
    if len(numbers) <= 1:
        # 单个箱号时箱型代码也应一致：两个箱型只差一两位 → 标签不一致
        # （多个箱号时不同箱型属正常，仅在箱型检测中校验是否在代码表中）
        types = sorted({v for v, _ in candidates['type']})
        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                d = diff_chars(types[i], types[j])
                if d <= 2:
                    pair_errors.append(('标签不一致',
                                        f'{types[i]} / {types[j]}（相差{d}位）'))
    if cfg['pair'] and pair_errors:
        return pair_errors

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

    # ---- 优先级6：箱型检测（写错必报；缺箱型默认报错，含豁免数字标签时放行）----
    if cfg['typecode']:
        tc_errors = []
        types = sorted({v for v, _ in cat_items.get('type', [])})
        for t in types:
            if t not in TYPE_CODES:
                tc_errors.append(('箱型不存在', f'{t} 不在国标箱型代码表中'))
        if not types and not type_exempt:
            tc_errors.append(('缺少箱型', '未找到箱型代码标签（含豁免标签时放行，可在「豁免标签管理」中配置）'))
        if tc_errors:
            return tc_errors

    return []


# ============================ 文件夹遍历与汇总 ============================

def scan_dirs(root, cfg, stop_event=None):
    """遍历 root（支持多层嵌套），返回 (各目录待检 json 路径列表, 配对报错列表)。
    先收集完所有目录再统一检测，避免逐目录等待导致并行度不足"""
    dir_targets = []   # [[json路径, ...], ...] 按遍历顺序，每项对应一个目录
    errors = []
    for dirpath, dirnames, filenames in os.walk(root):
        if stop_event is not None and stop_event.is_set():
            break
        jpgs, jsons = {}, {}
        for name in filenames:
            stem, ext = os.path.splitext(name)
            ext = ext.lower()
            if ext in ('.jpg', '.jpeg'):
                jpgs[stem] = os.path.join(dirpath, name)
            elif ext == '.json':
                jsons[stem] = os.path.join(dirpath, name)

        # ---- 优先级1：jpg 与 json 一一对应 ----
        if cfg['pairing']:
            for stem in sorted(set(jpgs) - set(jsons)):
                errors.append((jpgs[stem], '缺少json文件', ''))
            for stem in sorted(set(jsons) - set(jpgs)):
                errors.append((jsons[stem], '缺少jpg文件', ''))
            targets = sorted(set(jpgs) & set(jsons))
        else:
            targets = sorted(jsons)
        dir_targets.append([jsons[s] for s in targets])
    return dir_targets, errors


def template_path():
    """宏模板路径：exe/脚本同目录优先（便于手动改宏），其次 PyInstaller 解包内置；
    都没有返回 None（输出降级为不带宏的普通 .xlsx）"""
    p = os.path.join(app_dir(), '报错模板.xlsm')
    if os.path.exists(p):
        return p
    if getattr(sys, 'frozen', False):
        p = os.path.join(sys._MEIPASS, '报错模板.xlsm')
        if os.path.exists(p):
            return p
    return None


def normalize_out(out_xlsx, macro=True):
    """输出路径规范化：macro=True 且有宏模板时强制 .xlsm（宏只能存于 xlsm）；
    macro=False 时强制 .xlsx（普通工作簿存 .xlsm 会报格式不符）"""
    low = out_xlsx.lower()
    if macro and template_path():
        if low.endswith('.xlsx'):
            return out_xlsx[:-len('.xlsx')] + '.xlsm'
        if not low.endswith('.xlsm'):
            return out_xlsx + '.xlsm'
    else:
        if low.endswith('.xlsm'):
            return out_xlsx[:-len('.xlsm')] + '.xlsx'
        if not low.endswith('.xlsx'):
            return out_xlsx + '.xlsx'
    return out_xlsx


def precheck_output(out_xlsx):
    """检测开始前预检 Excel 输出，返回错误信息（无问题返回 None）：
    openpyxl 是否安装、目标文件是否被 Excel 打开锁定、所在目录是否可写"""
    try:
        from openpyxl import Workbook
    except ImportError:
        return '未安装 openpyxl（pip install openpyxl），无法生成 Excel'
    try:
        if os.path.exists(out_xlsx):     # 已有文件被 Excel 打开时处于锁定状态
            with open(out_xlsx, 'a'):
                pass
        probe = out_xlsx + '.probe'      # 同目录试写后删除，验证目录可写
        Workbook().save(probe)
        os.remove(probe)
    except OSError as e:
        return f'输出 Excel 无法写入：{e}'
    return None


def run_detection(root, cfg, out_xlsx, log, stop_event):
    """主流程：遍历 root，返回汇总信息 dict"""
    root = os.path.abspath(root)     # Excel 双击打开需绝对路径
    # 按带宏开关规范化扩展名：开→.xlsm（宏才能保留），关→.xlsx
    normalized = normalize_out(out_xlsx, cfg.get('macro', True))
    if normalized != out_xlsx:
        log(f'[信息] 输出路径已按宏开关调整为：{normalized}')
    out_xlsx = normalized

    # 先预检输出，避免整趟扫描跑完后才发现写不了 Excel
    err = precheck_output(out_xlsx)
    if err:
        raise ValueError(err)

    # 先一次性收集所有目录与 json 路径，再整体提交线程池并行解析
    dir_targets, all_errors = scan_dirs(root, cfg, stop_event)
    n_dirs = len(dir_targets)
    paths = [p for targets in dir_targets for p in targets]

    n_json = 0
    n_deleted = 0
    # 大批量小文件以读盘为主，多线程并行解析 json 可显著提速；
    # stop_event 传入 check_json：请求停止后尚未开始的任务直接跳过
    max_workers = min(8, os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = iter(pool.map(lambda p: check_json(p, cfg, stop_event), paths))
        stopped = False
        for targets in dir_targets:
            if stopped:
                break
            for jpath in targets:
                if stop_event.is_set():
                    stopped = True
                    break
                n_json += 1
                file_errors = next(results)
                # 检测正常的文件不打日志，日志框只显示报错信息
                if file_errors:
                    for etype, detail in file_errors:
                        all_errors.append((jpath, etype, detail))
                        log(f'  ✗ {os.path.basename(jpath)} ← {etype}：{detail}')

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

    write_excel(out_xlsx, all_errors, macro=cfg.get('macro', True))

    return {
        'dirs': n_dirs,
        'json': n_json,
        'errors': len(all_errors),
        'deleted': n_deleted,
        'out': out_xlsx,
    }


def write_excel(path, errors, macro=True):
    """报错写入 Excel：文件地址 / 是否修改完成（留空人工填）/ 备注。
    macro=True 且有宏模板时输出带宏 .xlsm：双击 A 列文件地址用 LabelMe
    单独打开该文件；宏参数存隐藏列 Z（Z2 LabelMe 完整路径）。
    宏开关关闭或模板缺失时降级为普通 .xlsx（无上述打开功能）"""
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, Alignment

    tmpl = template_path() if macro else None
    if tmpl:
        wb = load_workbook(tmpl, keep_vba=True)   # keep_vba=True 保留宏
        ws = wb.active
    else:
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
    if tmpl:
        # Z 列隐藏参数供双击宏读取（Z2 LabelMe 完整路径）
        ws['Z2'] = shutil.which('labelme') or ''
        ws.column_dimensions['Z'].hidden = True
    wb.save(path)


# ============================ 图形界面 ============================

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')

# 大批量检测时的界面保护：日志区最多保留行数（超出删最旧的）、
# 单次 _poll 最多刷入条数（其余留给下一轮，避免长时间霸占 UI 线程）
MAX_LOG_LINES = 5000
LOG_BATCH_LIMIT = 300

CHECK_ITEMS = [
    ('pairing',   'jpg/json 文件对应检测'),
    ('suffix',    '_fz/_oc 后缀检测（关闭时含此类标签的文件直接跳过）'),
    ('pair',      '标签一致性检测（完整箱号比对，只差1~2位）'),
    ('digits',    '箱号缺位/位数检测'),
    ('checkdigit', '校验位检测（ISO 6346）'),
    ('typecode',  '箱型检测（写错/缺失报错，含豁免标签时缺箱型放行）'),
    ('cleanup',   '删除空文件夹'),
]


class SetManagerDialog(tk.Toplevel):
    """集合管理窗口：查（搜索/列表）、增、删、改、恢复默认。
    箱型代码与豁免标签两个管理窗口共用同一套交互逻辑"""

    def __init__(self, master, title, noun, fmt_hint, get_items, valid_item,
                 save_items, base_items, base_desc, log,
                 normalize=str, sort_key=None):
        """noun：条目名（提示文案用）；fmt_hint：格式提示；
        get_items：取当前集合；valid_item：格式校验；
        save_items(set)->(是否成功, 提示)；base_items / base_desc：恢复默认；
        log：日志回调；normalize：新增/修改输入的规范化；sort_key：列表排序"""
        super().__init__(master)
        self.title(title)
        self.geometry('440x540')
        self.transient(master)
        self.grab_set()
        self.noun = noun
        self.fmt_hint = fmt_hint
        self.get_items = get_items
        self.valid_item = valid_item
        self.save_items = save_items
        self.base_items = base_items
        self.base_desc = base_desc
        self.log = log
        self.normalize = normalize
        self.sort_key = sort_key or (lambda s: s)

        tk.Label(self, text='搜索：').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        self.ent_search = tk.Entry(self)
        self.ent_search.grid(row=0, column=1, columnspan=2, sticky='we', padx=4)
        self.ent_search.bind('<KeyRelease>', lambda e: self._refresh())

        frm_list = tk.Frame(self)
        frm_list.grid(row=1, column=0, columnspan=3, sticky='news', padx=4, pady=4)
        self.lst = tk.Listbox(frm_list, selectmode='extended')
        sb = tk.Scrollbar(frm_list, orient='vertical', command=self.lst.yview)
        self.lst.config(yscrollcommand=sb.set)
        self.lst.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        tk.Label(self, text=f'新增{noun}：').grid(row=2, column=0, sticky='e', padx=4, pady=4)
        self.ent_new = tk.Entry(self)
        self.ent_new.grid(row=2, column=1, sticky='we', padx=4)
        tk.Button(self, text='添加', width=8, command=self._add).grid(row=2, column=2, padx=4)

        frm_ops = tk.Frame(self)
        frm_ops.grid(row=3, column=0, columnspan=3, pady=6)
        tk.Button(frm_ops, text='删除所选', width=10, command=self._del).pack(side='left', padx=6)
        tk.Button(frm_ops, text='修改所选', width=10, command=self._edit).pack(side='left', padx=6)
        tk.Button(frm_ops, text='恢复默认', width=10, command=self._reset).pack(side='left', padx=6)

        self.lbl_status = tk.Label(self, text='', fg='gray')
        self.lbl_status.grid(row=4, column=0, columnspan=3, pady=2)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self._refresh()

    def _filtered(self):
        """按搜索框内容过滤后的条目（查）"""
        kw = self.ent_search.get().strip()
        items = sorted(self.get_items(), key=self.sort_key)
        return [c for c in items if not kw or kw in c]

    def _refresh(self):
        self.lst.delete(0, 'end')
        for c in self._filtered():
            self.lst.insert('end', c)
        self.lbl_status.config(text=f'当前共 {len(self.get_items())} 个{self.noun}'
                                    f'（显示 {self.lst.size()} 个）')

    def _save(self, items, ok_msg):
        ok, tip = self.save_items(items)
        self.lbl_status.config(text=tip, fg='gray' if ok else 'red')
        if ok:
            self.log(f'[{self.noun}] {ok_msg}：{tip}')
        self._refresh()

    def _add(self):
        """增"""
        val = self.normalize(self.ent_new.get().strip())
        if not self.valid_item(val):
            messagebox.showwarning('提示', self.fmt_hint)
            return
        cur = self.get_items()
        if val in cur:
            messagebox.showinfo('提示', f'{val} 已存在。')
            return
        self._save(cur | {val}, f'新增 {val}')
        self.ent_new.delete(0, 'end')

    def _del(self):
        """删"""
        sel = list(self.lst.curselection())
        if not sel:
            messagebox.showinfo('提示', f'请先在列表中选择要删除的{self.noun}。')
            return
        vals = [self.lst.get(i) for i in sel]
        if not messagebox.askyesno('确认', f'确定删除 {len(vals)} 个{self.noun}？\n' + '、'.join(vals)):
            return
        self._save(self.get_items() - set(vals), f'删除 {len(vals)} 个')

    def _edit(self):
        """改"""
        sel = list(self.lst.curselection())
        if len(sel) != 1:
            messagebox.showinfo('提示', f'请先在列表中选择 1 个要修改的{self.noun}。')
            return
        old = self.lst.get(sel[0])
        new = simpledialog.askstring(f'修改{self.noun}', f'将 "{old}" 修改为：',
                                     initialvalue=old, parent=self)
        if new is None:
            return
        new = self.normalize(new.strip())
        if not self.valid_item(new):
            messagebox.showwarning('提示', self.fmt_hint)
            return
        cur = self.get_items()
        if new in cur and new != old:
            messagebox.showinfo('提示', f'{new} 已存在。')
            return
        self._save((cur - {old}) | {new}, f'修改 {old} → {new}')

    def _reset(self):
        """恢复内置默认"""
        if not messagebox.askyesno('确认', f'确定恢复为内置的 {len(self.base_items)} 个{self.base_desc}？'):
            return
        self._save(self.base_items, '恢复默认')


class CheckerApp:
    def __init__(self, master):
        self.master = master
        master.title('箱号标签校验工具（ISO 6346）')
        master.geometry('880x720')

        self.stop_event = threading.Event()
        self.msg_queue = queue.Queue()
        self.running = False
        self._set_wins = {}   # 已打开的集合管理窗口（箱型代码 / 豁免标签）

        frm_paths = tk.Frame(master, padx=10, pady=8)
        frm_paths.pack(fill='x')
        self.ent_root, _ = self._path_row(frm_paths, 0, '待检文件夹：', self._pick_dir)
        default_out = os.path.join(DESKTOP, f'报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsm')
        self.ent_out, _ = self._path_row(frm_paths, 1, '输出Excel：', self._pick_out)
        self.ent_out.insert(0, default_out)
        # 最近一次自动生成的默认输出路径；输入框内容与之相同（或为空）即视为
        # 未自定义，仍随所选文件夹自动更新，方向键等按键不会造成误判
        self._out_default = default_out

        frm_opts = tk.LabelFrame(master, text='输出选项', padx=10, pady=6)
        frm_opts.pack(fill='x', padx=10, pady=4)
        self.chk_macro = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frm_opts, variable=self.chk_macro,
            text='生成带宏 Excel（.xlsm，Excel 中双击文件地址直接打开 LabelMe）'
        ).grid(row=0, column=0, sticky='w', pady=2)

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
        self.btn_exempt = tk.Button(frm_btn, text='豁免标签管理…', width=14, command=self.manage_exempt)
        self.btn_exempt.pack(side='left', padx=8)
        self.btn_start = tk.Button(frm_btn, text='开始检测', width=14, command=self.start)
        self.btn_start.pack(side='left', padx=8)
        self.btn_stop = tk.Button(frm_btn, text='停止', width=10, command=self.stop, state='disabled')
        self.btn_stop.pack(side='left', padx=8)

        self.log_text = scrolledtext.ScrolledText(master, height=16, state='disabled', wrap='none')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=8)

        self.master.after(100, self._poll)

    def _path_row(self, parent, row, label, browse_cmd):
        tk.Label(parent, text=label, width=10, anchor='e').grid(row=row, column=0, sticky='e', pady=3)
        ent = tk.Entry(parent)
        ent.grid(row=row, column=1, sticky='we', padx=4, pady=3)
        btn = tk.Button(parent, text='浏览…', command=browse_cmd)
        btn.grid(row=row, column=2, padx=4)
        parent.columnconfigure(1, weight=1)
        return ent, btn

    def _pick_dir(self):
        d = filedialog.askdirectory(initialdir=DESKTOP)
        if d:
            self.ent_root.delete(0, 'end')
            self.ent_root.insert(0, d)
            # 用户未自定义过输出地址时，随所选文件夹自动更新默认值（生成在桌面）
            cur = self.ent_out.get()
            if not cur.strip() or cur == self._out_default:
                name = os.path.basename(os.path.normpath(d))
                default_out = os.path.join(
                    DESKTOP, f'{name}_报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsx')
                self.ent_out.delete(0, 'end')
                self.ent_out.insert(0, default_out)
                self._out_default = default_out

    def _pick_out(self):
        f = filedialog.asksaveasfilename(defaultextension='.xlsm',
                                         filetypes=[('Excel 工作簿（带宏，支持点击打开 LabelMe）', '*.xlsm'),
                                                    ('Excel 工作簿', '*.xlsx')],
                                         initialdir=DESKTOP)
        if f:
            # 用户已自行选择 Excel 生成地址（与默认值不同），之后不再自动覆盖
            self.ent_out.delete(0, 'end')
            self.ent_out.insert(0, f)

    # ==================== 箱型代码 / 豁免标签管理（增删改查） ====================

    def manage_codes(self):
        """打开箱型代码管理窗口"""
        self._open_set_manager(
            'codes', '箱型代码管理', '箱型代码',
            '箱型代码须为 4 位字母数字（如 45G1）。',
            lambda: TYPE_CODES, valid_type_code, set_type_codes,
            BASE_TYPE_CODES, '国标箱型代码',
            normalize=str.upper)

    def manage_exempt(self):
        """打开豁免标签管理窗口"""
        self._open_set_manager(
            'exempt', '豁免标签管理', '豁免标签',
            '豁免标签须为“,”+数字（如 ,1）。',
            lambda: EXEMPT_LABELS, valid_exempt_label, set_exempt_labels,
            BASE_EXEMPT_LABELS, '默认豁免标签',
            sort_key=lambda s: int(s[1:]))

    def _open_set_manager(self, key, title, noun, fmt_hint, get_items,
                          valid_item, save_items, base_items, base_desc,
                          normalize=str, sort_key=None):
        """打开（或置前已打开的）集合管理窗口，箱型代码与豁免标签共用"""
        # 已打开则直接置前，避免重复开窗覆盖控件引用、导致先开窗口操作错乱
        win = self._set_wins.get(key)
        if win is not None and win.winfo_exists():
            win.lift()
            win.focus_force()
            return
        win = SetManagerDialog(self.master, title, noun, fmt_hint,
                               get_items, valid_item, save_items,
                               base_items, base_desc, self.log,
                               normalize=normalize, sort_key=sort_key)
        self._set_wins[key] = win

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
        if not out.lower().endswith(('.xlsx', '.xlsm')):
            out += '.xlsx'          # 有宏模板时 run_detection 内会再转为 .xlsm

        cfg = {k: v.get() for k, v in self.cfg_vars.items()}
        cfg['macro'] = self.chk_macro.get()     # 输出选项：是否带宏
        if not any(v.get() for v in self.cfg_vars.values()):
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
        """每 100ms 批量取一次日志：合并为一次插入、只滚动一次，
        并裁剪超出上限的旧行，避免大批量时逐条刷新把界面拖卡"""
        lines = []
        finish_args = None
        while len(lines) < LOG_BATCH_LIMIT:
            try:
                msg = self.msg_queue.get_nowait()
            except queue.Empty:
                break
            if isinstance(msg, tuple):
                kind, payload = msg
                finish_args = (payload if kind == '__done__' else None,
                              None if kind == '__done__' else payload)
                break
            lines.append(msg)
        if lines:
            self.log_text.config(state='normal')
            self.log_text.insert('end', '\n'.join(lines) + '\n')
            n_lines = int(self.log_text.index('end-1c').split('.')[0])
            if n_lines > MAX_LOG_LINES:
                self.log_text.delete('1.0', f'{n_lines - MAX_LOG_LINES}.0')
            self.log_text.see('end')
            self.log_text.config(state='disabled')
        if finish_args is not None:
            self._finish(*finish_args)
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
                     f"结果已保存至：{summary['out']}",
                     'Excel 中：双击「文件地址」直接打开该文件。'
                     '首次打开需点「启用内容」允许宏。']
            for ln in lines:
                self.log(f'[信息] {ln}')
            messagebox.showinfo('完成', '\n'.join(lines))


# ============================ 入口 ============================

def run_cli(args):
    # 中文 Windows 控制台默认 GBK 编码，日志中的 ✓/✗ 等字符无法编码时会崩溃
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    if not os.path.isdir(args.root):
        print(f'错误：待检文件夹不存在：{args.root}')
        sys.exit(1)
    out = args.out or os.path.join(DESKTOP, f'报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsm')
    if not out.lower().endswith(('.xlsx', '.xlsm')):
        out += '.xlsx'          # 有宏模板时 run_detection 内会再转为 .xlsm
    cfg = {key: True for key, _ in CHECK_ITEMS}
    cfg['macro'] = True              # 输出选项默认开
    stop_event = threading.Event()
    try:
        summary = run_detection(args.root, cfg, out, print, stop_event)
    except ValueError as e:          # 输出预检失败（openpyxl 缺失 / 路径不可写）
        print(f'错误：{e}')
        sys.exit(1)
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
