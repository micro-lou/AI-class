# -*- coding: utf-8 -*-
"""
箱号标签校验工具（ISO 6346 校验位验算，筛选错误标签）

功能：
  1. 遍历指定文件夹（支持多层嵌套，逐层并行枚举，网络盘深目录不拖慢扫描），
     空文件夹自动删除（可开关）
  2. 检查文件夹内 1.jpg 与 1.json 一一对应（不对应则报错）；
     json 内无任何标签（shapes 为空）时报“json文件为空”
  3. 解析 LabelMe json 的 label：
     - 含 _fz / _oc 后缀的标签：开关开启时报错（不清晰 / 遮挡）；
       开关关闭时整个文件直接跳过，不做其他任何校验也不报错
     - 内容为 "," 加数字的标签不予理会
     - 标签按类别框（","加数字的标注框）分组：质心落在框内（允许超出
       图宽 4%，约 77px）的标签归为同一组，相邻两组靠得近也不会混淆；
       框外的标签视为危险标识/相邻箱喷字，不参与校验；框内只有孤立数字
       （无箱主代码/序列号）的组视为危险标识组，整组忽略。
       无类别框时退回全局比对（此时单数字标签多于箱号组数的话，
       多出的按与序列号距离截断，视为危险标识不参与组装）；
       逗号写反的类别标签（如 "1,"）框同样参与分组，但报错提示改正
     - 标签一致性用完整 11 位箱号整体比对（不拆分成三段）：组装出的
       多个完整箱号只差一两位且差异不含校验位（校验位相同）→ 报错
       （标签不一致），并分别验算两者校验位判定哪个正确，备注给出
       修改意见；校验位不同或相差超过两位 → 判定为不同的箱子，各自
       检测校验位（错的报“校验位应为X”）
       同一箱子的标签被画进多个类别框（如上面、侧面各画一个框）时，
       各组箱号相同或差异不含校验位（校验位相同）即并为一箱后照常检
       测；两框箱号校验位不同则按两个箱子独立检测——即便真是同一箱
       也只报校验位错误（备注含应为的校验位），不给跨框修改意见，
       避免把同图中相邻两箱误判成标签不一致
     - 箱号缺位 / 格式不符（应为 4 字母[第4位为设备类型码U/J/Z] + 6 数字 +
       1 校验位，共 11 位）→ 报错
     - 箱主代码前 3 位与 BIC 注册箱主代码比对，不在表中时按相近代码给出
       修改建议；第 4 位设备类型码仅允许 U（货运集装箱）/ J（可拆卸集装箱
       配件）/ Z（底盘车/拖车）；未注册箱主代码所在箱号校验位验算通过
       （校验位覆盖箱主代码，通过即证明代码真实）时视为新箱主自动入库
       不报错，同文件其余报错（箱型缺失/写错、其他箱子的校验位错误等）
       不阻断入库，入库后照常返回其余报错；BIC 代码可在界面增删改查，
       改动保存到同目录 BIC箱主代码配置.json
     - 按 ISO 6346 验算校验位 → 校验位错误
     - 箱型代码已内置（源自 箱型代码全.xls），写错必报错；缺箱型报错，
       但标签含豁免数字标签（默认 ,1 ,6 ,10 等，可管理）时允许缺箱型；
       箱型代码 / 豁免标签均可在界面增删改查，
       改动分别保存到同目录 箱型代码配置.json / 豁免标签配置.json
  4. 报错输出到 Excel（三列：文件地址 / 是否修改完成[留空人工填] / 备注），
     无报错时不生成 Excel 文件；输出开关（默认开，可关闭）：
     - 带宏 Excel：输出带宏 .xlsm（需同目录或内置 报错模板.xlsm），
       双击 A 列文件地址用 LabelMe 打开整个报错列表并定位到该行，
       可用 上一张/下一张（快捷键 A/D）按表内顺序切换；关闭则输出普通 .xlsx
  5. 检测逐箱按优先级执行：jpg&json对应 > json无标签 > 后缀 > 完整箱号
     一致性 > 缺位 > 箱主代码 > 校验位 > 箱型，命中报错后停止该箱后续检测
     （同文件多个箱子报错互不阻断、逐箱累加），全部箱子检完后开始下一文件
  6. 检测结果缓存（默认开，可关闭，存同目录 检测结果缓存.json）：重跑时
     未修改的文件（修改时间/大小不变且配置一致）直接复用上次结果，只实际
     检测变化过的文件；任一配置（箱型/豁免/BIC/检测开关）改动后自动全量
     重检，检测代码的判定逻辑更新后同样自动全量重检，删除缓存文件亦可
     强制全量；保存时只保留本次扫描过的文件，换文件夹后旧条目自动清除

用法：
  图形界面：python 箱号标签校验.py（exe 也可把待检文件夹直接拖到图标上启动；
  上次的待检文件夹与输出目录自动记忆，下次启动预填）
  命令行：  python 箱号标签校验.py --cli --root <文件夹> [--out <输出.xlsm>]
"""

import hashlib
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

BIC_PATH = os.path.join(app_dir(), 'BIC箱主代码配置.json')

# 设备类型码（箱主代码第4位，ISO 6346）：仅允许以下三种
EQUIPMENT_CODES = {
    'U': '货运集装箱',
    'J': '可拆卸集装箱配件',
    'Z': '底盘车/拖车',
}


# BIC 注册箱主代码前缀（内置默认值，源自 BIC箱主代码.csv，取代码前 3 位；
# 标签中的箱主代码第 4 位为设备类型码，仅比对前 3 位）
BASE_BIC_PREFIXES = frozenset({
    'MAE', 'MSC', 'CMD', 'CMA', 'COS', 'HLC', 'ONE', 'EIS', 'YML', 'HDM',
    'PIL', 'ZIM', 'RCL', 'WHL', 'SIT', 'TSH', 'KMT', 'SNK', 'MAT', 'APL',
    'OOL', 'NYK', 'MOL', 'CSA', 'CCN', 'SML', 'MIS', 'HJS', 'SEA', 'IRS',
    'MES', 'SIN', 'CUL', 'MAR', 'ACL', 'MAC', 'CSC', 'FSC', 'SAF', 'SAA',
    'CNC', 'PAB', 'DRC', 'CLH', 'NAX', 'BLK', 'VIN', 'HHL', 'MML', 'SLL',
    'CCL', 'KOR', 'TSL', 'SCN', 'NFF', 'NJT', 'KRL', 'TCL', 'CAI', 'TRI',
    'BRI', 'FES', 'GWD', 'ITL', 'UES', 'XES', 'PRS', 'CRX', 'WFL', 'MEB',
    'CFL', 'SNC', 'SEG', 'DOL', 'ALI', 'CAR', 'GES', 'STA', 'AML', 'SCZ',
    'RIL', 'NCL', 'SHL', 'CLL', 'LOJ', 'MCN', 'ESP', 'CLA', 'RZD', 'KZR',
    'KLR', 'KBS', 'BNS', 'CSX', 'NSC', 'CPC', 'CNR', 'GMR', 'IBG', 'MGR',
    'SCM', 'ASU', 'NEX', 'EXF', 'DHL', 'DSL', 'GEL', 'NVO', 'KLU', 'JKL',
    'ARC', 'RFU', 'SNR', 'UPU', 'EKU', 'JRU', 'KNU',
})


def valid_bic_prefix(s):
    """BIC 箱主代码前缀须为 3 位字母"""
    return bool(re.fullmatch(r'[A-Z]{3}', str(s).strip().upper()))


def load_bic_prefixes():
    """启动时读取一次 BIC 箱主代码配置；无配置文件时使用内置默认值"""
    try:
        with open(BIC_PATH, encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return BASE_BIC_PREFIXES
        # 逐条校验格式，过滤手改配置文件时可能混入的脏数据
        return frozenset(p for p in (str(s).strip().upper() for s in data)
                         if valid_bic_prefix(p))
    except (OSError, json.JSONDecodeError, TypeError):
        return BASE_BIC_PREFIXES


def set_bic_prefixes(prefixes):
    """更新 BIC 箱主代码（全局生效）并持久化到配置文件，返回 (是否成功, 提示)"""
    global BIC_PREFIXES
    BIC_PREFIXES = frozenset(prefixes)
    try:
        with open(BIC_PATH, 'w', encoding='utf-8') as f:
            json.dump(sorted(BIC_PREFIXES), f, ensure_ascii=False, indent=1)
        return True, f'已保存 {len(BIC_PREFIXES)} 个箱主代码'
    except OSError as e:
        return False, f'保存到配置文件失败：{e}'


BIC_PREFIXES = load_bic_prefixes()

# 自动入库的锁与本次运行新增记录（check_json 在线程池中并发调用，
# 需加锁避免多个线程同时写配置文件；_NEW_BIC 供检测结束后汇总打日志）
BIC_LOCK = threading.Lock()
_NEW_BIC = set()


def auto_add_bic_prefixes(prefixes):
    """把通过其余全部检测的未注册箱主代码前缀自动加入注册表并持久化；
    返回本次实际新增的前缀集合（已存在的不重复添加）"""
    global BIC_PREFIXES
    with BIC_LOCK:
        new = set(prefixes) - BIC_PREFIXES
        if not new:
            return set()
        set_bic_prefixes(BIC_PREFIXES | new)
        _NEW_BIC.update(new)
        return new


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


def number_pair_error(a, b, d):
    """两个完整箱号只差 1~2 位 → 标签不一致。分别验算两个箱号的校验位，
    判定哪个更可能正确，在备注中给出修改意见而非仅报相差位数：
    - 一对一错：错的那个应以对的为准修改
    - 只在校验位上不同：其一必错（前10位相同校验位唯一），结论确定
    - 都对（差异位在前10位）或都错：无法自动判定，提示人工核对"""
    # 统一成对箱号的顺序：同一对箱号无论来自组内还是跨组比对，报错文本
    # 完全一致，去重才能合并（否则 A/B、B/A 两条文本在 Excel 里重复成行）
    a, b = sorted((a, b))
    ok_a = calc_container_check(a[:10]) == int(a[10])
    ok_b = calc_container_check(b[:10]) == int(b[10])
    base = f'{a} / {b}（相差{d}位）'
    if ok_a and not ok_b:
        tip = f'{b} 应改为 {a}'
    elif ok_b and not ok_a:
        tip = f'{a} 应改为 {b}'
    elif ok_a and ok_b:
        tip = '两者校验位均正确，无法自动判定，需人工核对'
    else:
        exp_a = a[:10] + str(calc_container_check(a[:10]))
        exp_b = b[:10] + str(calc_container_check(b[:10]))
        # 前10位相同时只提示一次（两个错误箱号对应同一个正确箱号）
        exp = exp_a if exp_a == exp_b else f'{exp_a} 或 {exp_b}'
        tip = f'两者校验位均错误，应为 {exp}，需人工核对'
    return ('标签不一致', f'{base}，{tip}')


def equipment_code_error(owner):
    """箱主代码第 4 位设备类型码检测：仅允许 U/J/Z
    （货运集装箱/可拆卸集装箱配件/底盘车/拖车），非法返回报错，否则 None"""
    equip = owner[3]
    if equip in EQUIPMENT_CODES:
        return None
    names = '/'.join(f'{k}{v}' for k, v in EQUIPMENT_CODES.items())
    return ('箱主代码错误', f'{owner} 第4位"{equip}"非设备类型码，应为 {names}')


def bic_prefix_error(owner):
    """箱主代码前 3 位与 BIC 注册表比对：已注册返回 None；
    未注册返回报错——存在只差 1 位的注册代码时给出修改建议"""
    prefix = owner[:3]
    if prefix in BIC_PREFIXES:
        return None
    # 只差 1 位的注册代码 → 给出修改建议（按字母序取全部，一般只有 0~3 个）
    near = sorted(p for p in BIC_PREFIXES if diff_chars(prefix, p) == 1)
    if near:
        return ('箱主代码错误',
                f'{owner} 前3位"{prefix}"不在BIC注册箱主代码中，'
                f'疑似"{prefix}"应为 "{" / ".join(near)}"，需人工核对')
    return ('箱主代码错误', f'{owner} 前3位"{prefix}"不在BIC注册箱主代码中，需人工核对')


# ============================ 标签分类 ============================

# 完整 11 位箱号（第4位设备类型码不限字母，非 U/J/Z 的由优先级5检测报错）
RE_FULL = re.compile(r'^[A-Z]{4}\d{7}$')


def valid_owner_label(s):
    """箱主代码标签合法：4 位字母且第 4 位为设备类型码 U/J/Z"""
    return len(s) == 4 and s[3] in EQUIPMENT_CODES and s.isalpha()
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


# 分组容差：标签质心允许超出类别框的距离（按图宽比例）。
# 依据 0830第一批 实测：同组标签质心最大超出 46px，
# 危险标识 / 相邻箱标签距框最近 114px，取 4%（1920px 宽约 77px）居中留余量
CATEGORY_TOL_RATIO = 0.04


def bbox_of(shape):
    """shape 点集的外接矩形 (x0, y0, x1, y1)；无点返回 None"""
    pts = shape.get('points') or []
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def dist_outside(cen, box):
    """质心到矩形的距离（在矩形内部为 0）"""
    x, y = cen
    x0, y0, x1, y1 = box
    dx = max(x0 - x, x - x1, 0)
    dy = max(y0 - y, y - y1, 0)
    return (dx * dx + dy * dy) ** 0.5


def group_by_category(items, category_boxes, image_width):
    """按类别框（","加数字的标注框）把标签分组：质心落在某框内（允许超出
    CATEGORY_TOL_RATIO 比例的范围）即归该组；框重叠、质心同时在多个框内时
    取框中心更近的组（相邻两组靠得近也不会混淆）；不在任何框范围内的标签
    丢弃（危险标识 / 相邻箱喷字，不参与校验）。
    无类别框时全部标签归单一组（退回全局比对逻辑）。
    返回 [组内标签列表, ...]，每个元素为 [(label, 质心), ...]"""
    if not category_boxes:
        return [items] if items else []
    # imageWidth 缺失或非数字（损坏 json）时退回 1920 默认值
    width = image_width if isinstance(image_width, (int, float)) and image_width > 0 else 1920
    tol = round(width * CATEGORY_TOL_RATIO)
    centers = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in category_boxes]

    def rank(i, cen):
        # 主判据：质心到框边缘的超出距离（框内为 0）；框重叠时多个框同为 0，
        # 用到框中心的距离决胜，把标签归给真正所属的那组
        d_out = dist_outside(cen, category_boxes[i])
        cx, cy = centers[i]
        d_ctr = (cen[0] - cx) ** 2 + (cen[1] - cy) ** 2
        return (d_out, d_ctr)

    groups = [[] for _ in category_boxes]
    for lab, cen in items:
        best_i = min(range(len(category_boxes)), key=lambda i: rank(i, cen))
        if dist_outside(cen, category_boxes[best_i]) <= tol:
            groups[best_i].append((lab, cen))
    return groups


def assemble_group(group, truncate_extra=False):
    """单组标签（同一箱子的上面&侧面标注）配对并组装完整 11 位箱号，
    组内做一致性比对。返回 (箱号列表, 箱型列表, 不一致报错, 缺位报错)；
    组内没有箱主代码/序列号/完整箱号时返回 None——视为危险标识等孤立
    标注组（如类别框只框住一个孤立数字），整组忽略不校验。
    truncate_extra=True（无类别框的全局组）时，单数字标签多于箱号组数
    的话多出的按危险标识截断；有类别框时框外标签已被分组剔除，无需截断"""
    cat_items = {}      # 类别 -> [(规范化值, 质心)]
    format_errors = []  # 缺位类报错（优先级4）
    for lab, cen in group:
        cat, norm = classify_label(lab)
        if cat in ('badnum', 'unrecognized'):
            detail = '存在空标签' if not lab else f'标签"{lab}"格式或位数无法识别'
            format_errors.append(('箱号位数缺失', detail))
        else:
            cat_items.setdefault(cat, []).append((norm, cen))
    # 无箱号主体的组：只有校验位/箱型/格式错标签 → 孤立标注，整组忽略
    if not (cat_items.get('owner') or cat_items.get('serial')
            or cat_items.get('full')):
        return None

    # ---- 组内配对（供组装箱号使用）----
    # 同类别内按质心距离贪心两两配对（同组标签对应同一箱子的上面&侧面，位置相近）：
    #   值相同 → 合并为 1 个候选（质心取中点）；值不同 → 两个均保留为候选
    # 落单的单个标签也保留为候选。
    # 注意：不逐段比对差异报“标签不一致”——两个不同箱子的校验位（单字符）
    # 必然只差 1 位、箱主代码/箱型也常只差一两位，逐段比会对它们大量误报；
    # 一致性判断统一在组装出完整 11 位箱号后整体比对（见下方）
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

    # ---- 组装完整 11 位箱号 ----
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
            if not valid_owner_label(o_val):
                format_errors.append(('箱号位数缺失',
                                      f'箱主代码"{o_val}"格式错误（应为3字母+U/J/Z）'))
        if owner_c and serial_c and check_c:
            # 兜底（无类别框时的全局组）：合并后的单数字标签数多于箱号组数
            # （箱主代码/序列号合并后的较大值）时，多出的单数字并非校验位而是
            # 危险标识，按与序列号的距离只保留最近的若干个作校验位，其余忽略
            n_boxes = max(len({v for v, _ in owner_c}),
                          len({v for v, _ in serial_c}))
            if truncate_extra and len(check_c) > n_boxes:
                check_c = sorted(
                    check_c,
                    key=lambda c: min((c[1][0] - s[1][0]) ** 2
                                      + (c[1][1] - s[1][1]) ** 2
                                      for s in serial_c))[:n_boxes]
            if len({v for v, _ in serial_c}) == 1:
                # 序列号唯一：与每个箱主代码 / 校验位候选各组合出一个完整箱号
                s_val = next(iter({v for v, _ in serial_c}))
                for o in {v for v, _ in owner_c if valid_owner_label(v)}:
                    for k in {v for v, _ in check_c}:
                        numbers.append(o + s_val + k)
            else:
                # 多个序列号：就近取箱主代码与校验位，分别组装箱号
                for s_val, s_cen in serial_c:
                    o = min(owner_c, key=lambda c: (c[1][0] - s_cen[0]) ** 2
                            + (c[1][1] - s_cen[1]) ** 2)
                    k = min(check_c, key=lambda c: (c[1][0] - s_cen[0]) ** 2
                            + (c[1][1] - s_cen[1]) ** 2)
                    if valid_owner_label(o[0]):
                        numbers.append(o[0] + s_val + k[0])
            numbers = sorted(set(numbers))

    # ---- 组内标签一致性检测（完整 11 位箱号整体比对，不拆分成三段）----
    # 组装出的多个完整箱号两两比对：只差一两位且差异不含校验位（校验位
    # 相同）→ 同一箱子的标签标注不一致，分别验算两个箱号的校验位判定
    # 哪个更可能正确，备注给出修改意见；校验位不同或相差超过两位 → 判定
    # 为不同的箱子，各自参与后续校验位检测（错的报“校验位应为X”）
    pair_errors = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            d = diff_chars(numbers[i], numbers[j])
            if d <= 2 and numbers[i][10] == numbers[j][10]:
                pair_errors.append(number_pair_error(numbers[i], numbers[j], d))
    # 箱型不参与标签不一致比对：不同箱型只可能是写错/缺失，交由优先级7的
    # 箱型检测（是否在代码表中）单独校验，避免上面&侧面标注了不同箱型误报

    # 箱型取全集（含落单未配对的），供箱型检测用
    types = sorted({v for v, _ in cat_items.get('type', [])})
    return numbers, types, pair_errors, format_errors


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

def dedupe_errors(errors):
    """同一（类型, 细节）报错只保留一条：同一异常标签被分到多个组、
    或多个形状带相同标签时会累积出完全重复的报错，Excel 无需重复成行"""
    seen = set()
    out = []
    for e in errors:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def check_json(path, cfg, stop_event=None):
    """检测一个 json 文件，返回报错列表 [(类型, 细节)]。
    按优先级顺序执行，命中报错即停止后续检测。"""
    if stop_event is not None and stop_event.is_set():
        return []                     # 已请求停止，跳过剩余文件的解析
    data, err = load_json(path)
    if err:
        return [('json解析失败', err)]
    # shapes 缺失 / 为 null / 条目非对象（手改或损坏的 json）：按损坏文件报错，
    # 不让遍历时的异常一路抛到线程池外、中断整个检测丢失已扫出的结果
    shapes = data.get('shapes')
    if not isinstance(shapes, list) or not all(isinstance(s, dict) for s in shapes):
        return [('json解析失败', 'shapes 字段缺失或格式异常')]
    # 优先级1.5：json 无任何标签（shapes 为空，如画布上未标注就保存）→
    # 文件级报错，优先级仅次于 jpg/json 一一对应；避免落入末尾“缺少箱型”
    # 兜底报错造成误导
    if not shapes:
        return [('json文件为空', 'shapes 为空，无任何标注标签')]

    # 收集标签："," 开头的类别标签记录其框（用于分组）；_fz/_oc 的归入后缀组
    suffix_labels = []   # (报错类型, 原始label)
    items = []           # (原始label, 质心)
    category_boxes = []  # 类别框 (x0, y0, x1, y1)，箱号标签按框分组
    reversed_labels = [] # 逗号写反的类别标签（如 "1,"）：框照常用，但要报错
    type_exempt = False  # 是否存在豁免数字标签（存在时允许缺箱型代码）
    for shape in shapes:
        lab = str(shape.get('label', '')).strip()
        # 类别标签："，数字"；逗号写在后面的（如 "1,"）是写反的类别标签，
        # 框同样用于分组，但需报错提示改正
        if re.fullmatch(r'\d+,', lab):
            reversed_labels.append(lab)
        if lab.startswith(',') or re.fullmatch(r'\d+,', lab):
            if lab in EXEMPT_LABELS:
                type_exempt = True
            box = bbox_of(shape)
            if box:
                category_boxes.append(box)  # 类别标签本身不校验，框用于分组
            continue
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
        return dedupe_errors(suffix_labels) if cfg['suffix'] else []

    # ---- 按类别框分组：框外标签（危险标识/相邻箱喷字）不参与校验 ----
    groups = group_by_category(items, category_boxes, data.get('imageWidth'))

    # 逐组配对、组装完整 11 位箱号并做组内一致性比对
    g_data = []   # 每组的 (箱号列表, 箱型列表, 组内不一致报错, 缺位报错)
    for group in groups:
        # 无类别框时唯一一组为全局组，启用单数字危险标识截断兜底
        res = assemble_group(group, truncate_extra=not category_boxes)
        if res is not None:
            g_data.append(res)

    # ---- 并箱：同一箱子的标签被分别画进两个类别框（如上面、侧面各画一个
    # 框）时，每组各自组装出箱号，组内比对发现不了不一致。各组箱号两两
    # 跨组比对，判定为同一箱子才并为一箱（箱号/箱型取并集）后照常检测：
    #   - 箱号完全相同 → 同一箱子（相邻两箱不可能同号）
    #   - 只差一两位且校验位相同（且非两者都验算通过）→ 同一箱子标签
    #     不一致（箱主代码/序列号抄错、校验位照抄），按校验位给修改意见
    # 校验位不同 → 按两个不同的箱子独立检测，不给跨框修改意见——即便
    # 两框真是同一箱子，错的箱号也会在自身的校验位检测中报“应为X”，
    # 信息不丢；这样同图中相邻两箱（序号只差一两位、校验位各不同）不
    # 会被误判成标签不一致
    n = len(g_data)
    parent = list(range(n))          # 并查集：组下标 -> 箱（根）下标

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    cross_pairs = {}                 # 组下标 -> 跨组标签不一致报错（并箱后同箱）
    for i in range(n):
        for j in range(i + 1, n):
            same_box = False
            for a in g_data[i][0]:
                for b in g_data[j][0]:
                    d = diff_chars(a, b)
                    if d == 0:
                        same_box = True
                    elif (d <= 2 and a[10] == b[10]
                          and not (calc_container_check(a[:10]) == int(a[10])
                                   and calc_container_check(b[:10]) == int(b[10]))):
                        same_box = True
                        cross_pairs.setdefault(i, []).append(number_pair_error(a, b, d))
            if same_box:
                parent[find(i)] = find(j)
    boxes = {}                       # 箱根下标 -> 成员组下标列表
    for i in range(n):
        boxes.setdefault(find(i), []).append(i)

    # ---- 逐箱检测（优先级3~7，每箱命中即停；多箱报错互不阻断、逐箱累加）----
    errors = []
    for root in sorted(boxes):
        members = boxes[root]
        numbers = sorted({x for i in members for x in g_data[i][0]})
        types = sorted({t for i in members for t in g_data[i][1]})
        # 优先级3：标签一致性（组内+跨组比对结论，备注已含修改意见）
        pair_errors = dedupe_errors(
            [e for i in members for e in g_data[i][2]]
            + [e for i in members for e in cross_pairs.get(i, [])])
        if cfg['pair'] and pair_errors:
            errors.extend(pair_errors)
            continue
        # 优先级4：缺位 / 位数
        fmt_errors = dedupe_errors([e for i in members for e in g_data[i][3]])
        if cfg['digits'] and fmt_errors:
            errors.extend(fmt_errors)
            continue
        # 优先级5：箱主代码（前3位比对BIC注册表，第4位限U/J/Z）。
        # 前 3 位未注册的先记下不立即报：其所在箱号校验位验算通过（校验位
        # 覆盖箱主代码+序列号，通过即证明箱主代码真实）时视为新箱主自动
        # 入库且不报错——不要求其余检测全部通过；校验位不通过或检测关闭
        # 时按优先级照常报错。第 4 位设备类型码错误属格式错误，必报
        oc_errors = []
        equip_bad = False
        unknown_owners = {}
        owners = sorted({x[:4] for x in numbers})
        if cfg['ownercode']:
            for owner in owners:
                eq_err = equipment_code_error(owner)
                if eq_err:
                    equip_bad = True
                    oc_errors.append(eq_err)
                    continue
                p_err = bic_prefix_error(owner)
                if p_err:
                    unknown_owners[owner] = p_err
            if equip_bad:
                errors.extend(oc_errors)
                continue
        # 优先级6：校验位（ISO 6346）
        cd_errors = []
        verified = set()   # 校验位验算通过的箱号（其箱主代码已证实真实）
        if cfg['checkdigit']:
            for num in numbers:
                expect = calc_container_check(num[:10])
                actual = int(num[10])
                if expect != actual:
                    cd_errors.append(('校验位错误', f'{num} 校验位应为{expect}，实际为{actual}'))
                else:
                    verified.add(num)
        # 优先级7：箱型（写错必报；缺箱型默认报错，含豁免数字标签时放行）
        tc_errors = []
        if cfg['typecode']:
            for t in types:
                if t not in TYPE_CODES:
                    tc_errors.append(('箱型不存在', f'{t} 不在国标箱型代码表中'))
            if not types and not type_exempt:
                tc_errors.append(('缺少箱型', '未找到箱型代码标签（含豁免标签时放行，可在「豁免标签管理」中配置）'))
        # 校验位通过的箱号 → 其未注册箱主代码自动入库并撤销对应报错；校验位
        # 检测关闭时无法确认箱号真实性，不自动入库（避免污染注册表）
        if unknown_owners and verified:
            ok = {o for o in unknown_owners if any(x[:4] == o for x in verified)}
            if ok:
                auto_add_bic_prefixes({o[:3] for o in ok})
                for o in ok:
                    del unknown_owners[o]
        # owners 已排序，按序输出未入库箱主代码的报错，保证多次运行顺序稳定
        oc_errors.extend(unknown_owners[o] for o in sorted(unknown_owners))
        # 按优先级取最先命中：箱主代码（5）> 校验位（6）> 箱型（7）
        if oc_errors:
            errors.extend(oc_errors)
        elif cd_errors:
            errors.extend(cd_errors)
        elif tc_errors:
            errors.extend(tc_errors)

    # 整个文件没有任何箱号组（只有类别框/豁免标签，无箱号主体）时，
    # 仍按缺箱型报错提醒该文件无内容可检（沿用原文件级行为）
    if cfg['typecode'] and not g_data and not type_exempt:
        errors.append(('缺少箱型', '未找到箱型代码标签（含豁免标签时放行，可在「豁免标签管理」中配置）'))

    # 逗号写反的类别标签（如 "1,"）：文件级报错，提示改为 ",1"
    #（不影响分组，与各箱报错一并输出）
    if cfg['digits']:
        for lab in reversed_labels:
            errors.append(('箱号位数缺失', f'标签"{lab}"逗号写反，应为",{lab[:-1]}"'))
    return dedupe_errors(errors)


def safe_check_json(path, cfg, stop_event=None):
    """check_json 的兜底包装：json 内容损坏（字段类型异常等）引发意外异常时，
    降级为该文件的一条报错并继续检测后续文件，而不是中断整个检测、
    丢失已扫出的全部结果"""
    try:
        return check_json(path, cfg, stop_event)
    except Exception as e:
        return [('json解析失败', f'检测时发生未预期异常 {type(e).__name__}: {e}')]


# ============================ 检测结果缓存 ============================
# 修标工作流是「检测 → 修 → 重跑验证」，重跑时绝大多数文件没动过。
# 缓存键为 json 路径，条目存 [配置指纹, 修改时间, 大小, 报错列表]：
# 路径 + 修改时间 + 大小 + 配置指纹全部一致才复用，任一变化即重新检测。
# 保存时只保留本次扫描过的文件，历史运行的陈旧条目自动清除（见 run_detection）。
# 删除同目录 检测结果缓存.json 可随时强制全量重检

CACHE_PATH = os.path.join(app_dir(), '检测结果缓存.json')

# 检测逻辑版本：缓存指纹只含配置内容，检测代码的判定逻辑改动不会体现在
# 文件的修改时间/大小里，改动判定逻辑时把此号 +1，旧缓存全部失效自动全量重检
LOGIC_VERSION = 5


def valid_cache_entry(v):
    """缓存条目格式校验（防手改/损坏的脏数据混入）：应为
    [配置指纹(str), 修改时间(int), 大小(int), 报错列表(每个2元素)]"""
    return (isinstance(v, list) and len(v) == 4
            and isinstance(v[0], str) and isinstance(v[1], int)
            and isinstance(v[2], int) and isinstance(v[3], list)
            and all(isinstance(e, list) and len(e) == 2 for e in v[3]))


def load_result_cache():
    """读取上次运行的结果缓存（json路径 -> 条目）；
    无文件、损坏或条目格式不对的按空缓存处理"""
    try:
        with open(CACHE_PATH, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if valid_cache_entry(v)}


def save_result_cache(cache):
    """把检测结果缓存写回（先写临时文件再原子替换，避免中途被杀留下半个
    文件）；写失败静默跳过，不影响检测结果"""
    try:
        tmp = CACHE_PATH + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        os.replace(tmp, CACHE_PATH)
    except OSError:
        pass


def cache_fingerprint(cfg):
    """缓存配置指纹：影响检测结果的检测开关 + 三套配置（箱型/豁免/BIC）的
    实际内容 + 检测逻辑版本。任一变化指纹即变 → 旧缓存全部失效，自动全量重检"""
    payload = json.dumps({
        'cfg': {k: bool(cfg.get(k)) for k in
                ('suffix', 'pair', 'digits', 'ownercode', 'checkdigit', 'typecode')},
        'type': sorted(TYPE_CODES),
        'exempt': sorted(EXEMPT_LABELS),
        'bic': sorted(BIC_PREFIXES),
        'logic': LOGIC_VERSION,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode('utf-8')).hexdigest()


def check_json_cached(path, cfg, stop_event, cache, fingerprint, stats):
    """带缓存的检测：文件未变（修改时间/大小不变）且配置指纹一致时直接
    复用上次结果，跳过 json 读取与全部检测。cache 为 None 表示关闭缓存
    （直接全量检测）；stats 为命中计数列表（append 原子，线程安全够用）"""
    if cache is None:
        return safe_check_json(path, cfg, stop_event)
    if stop_event is not None and stop_event.is_set():
        # 已停止：直接跳过且不写缓存，避免把「没检」当成「没错」缓存下来
        return []
    try:
        st = os.stat(path)
    except OSError:
        return safe_check_json(path, cfg, stop_event)   # stat 不到就直接检测
    entry = cache.get(path)
    if (entry is not None and entry[0] == fingerprint
            and entry[1] == st.st_mtime_ns and entry[2] == st.st_size):
        stats.append('hit')
        return entry[3]
    result = safe_check_json(path, cfg, stop_event)
    # 检测中途收到停止请求时不写缓存（此时结果为空并非真实结论）
    if stop_event is None or not stop_event.is_set():
        cache[path] = [fingerprint, st.st_mtime_ns, st.st_size, result]
    stats.append('miss')
    return result


# ============================ 文件夹遍历与汇总 ============================

# 目录扫描并行度：目录枚举是纯网络往返（NAS 高延迟下每个目录几十毫秒），
# 多开线程收益直接；本地 SSD 上线程大多空转，也无副作用
SCAN_WORKERS = 16


def scan_dirs(root, cfg, stop_event=None):
    """并行遍历 root（支持多层嵌套），返回 (各目录待检 json 路径列表, 配对报错列表)。
    先收集完所有目录再统一检测，避免逐目录等待导致并行度不足。
    网络盘上每个目录的枚举都是一次网络往返，单线程 os.walk 目录一多就被
    延迟拖垮，这里逐层并行枚举（同层目录同时下探）；
    结果按目录路径排序，多次运行的报错顺序稳定一致"""
    def scan_one(dirpath):
        """枚举单个目录，返回 (子目录列表, jpg表, json表)；
        目录读不了（权限/断连）按空处理，不中断整个扫描"""
        subdirs, jpgs, jsons = [], {}, {}
        try:
            with os.scandir(dirpath) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            subdirs.append(entry.path)
                            continue
                        name = entry.name
                    except OSError:
                        continue
                    stem, ext = os.path.splitext(name)
                    ext = ext.lower()
                    if ext in ('.jpg', '.jpeg'):
                        jpgs[stem] = os.path.join(dirpath, name)
                    elif ext == '.json':
                        jsons[stem] = os.path.join(dirpath, name)
        except OSError:
            pass
        return subdirs, jpgs, jsons

    found = []       # (dirpath, json路径列表, 配对报错列表)
    level = [root]   # 当前层的目录，逐层向下
    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as pool:
        while level:
            if stop_event is not None and stop_event.is_set():
                break
            next_level = []
            # 同层目录并行枚举（pool.map 结果顺序与 level 一致）
            for dirpath, (subdirs, jpgs, jsons) in zip(level, pool.map(scan_one, level)):
                # ---- 优先级1：jpg 与 json 一一对应 ----
                if cfg['pairing']:
                    pair_errs = []
                    for stem in sorted(set(jpgs) - set(jsons)):
                        pair_errs.append((jpgs[stem], '缺少json文件', ''))
                    for stem in sorted(set(jsons) - set(jpgs)):
                        pair_errs.append((jsons[stem], '缺少jpg文件', ''))
                    targets = sorted(set(jpgs) & set(jsons))
                else:
                    pair_errs = []
                    targets = sorted(jsons)
                found.append((dirpath, [jsons[s] for s in targets], pair_errs))
                next_level.extend(subdirs)
            level = sorted(next_level)
    found.sort(key=lambda item: item[0])   # 按目录路径排序，输出顺序稳定
    dir_targets = [targets for _, targets, _ in found]
    errors = [e for _, _, pair_errs in found for e in pair_errs]
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


def launcher_script_path():
    """LabelMe 列表模式启动脚本（labelme批量打开.py）路径：查找顺序同 template_path"""
    p = os.path.join(app_dir(), 'labelme批量打开.py')
    if os.path.exists(p):
        return p
    if getattr(sys, 'frozen', False):
        p = os.path.join(sys._MEIPASS, 'labelme批量打开.py')
        if os.path.exists(p):
            return p
    return None


def find_python_for_labelme():
    """查找能运行启动脚本的 Python 解释器完整路径，找不到返回 ''。
    未打包时直接用本进程解释器；打包成 exe 后本进程不是 Python，
    从 labelme 命令位置推导（Scripts\\..\\python.exe），再退到 py 启动器 / PATH"""
    if not getattr(sys, 'frozen', False):
        return sys.executable
    lm = shutil.which('labelme')
    if lm:
        cand = os.path.join(os.path.dirname(os.path.dirname(lm)), 'python.exe')
        if os.path.isfile(cand):
            return cand
    for name in ('py', 'python'):
        p = shutil.which(name)
        if p:
            return p
    return ''


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


def precheck_output(out_xlsx, macro=True):
    """检测开始前预检 Excel 输出，返回错误信息（无问题返回 None）：
    openpyxl 是否安装、目标文件是否被 Excel 打开锁定、所在目录是否可写；
    macro=True 时一并预检宏模板能否读取（损坏则提前报错，
    免得整趟扫描跑完后写 Excel 时才发现）"""
    try:
        from openpyxl import Workbook
    except ImportError:
        return '未安装 openpyxl（pip install openpyxl），无法生成 Excel'
    if macro:
        tmpl = template_path()
        if tmpl:
            try:
                from openpyxl import load_workbook
                load_workbook(tmpl, keep_vba=True)
            except Exception as e:
                return (f'宏模板 {os.path.basename(tmpl)} 读取失败'
                        f'（{type(e).__name__}: {e}）；请修复或删除该模板，'
                        f'或关闭「生成带宏 Excel」后重试')
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
    err = precheck_output(out_xlsx, cfg.get('macro', True))
    if err:
        raise ValueError(err)

    # 先一次性收集所有目录与 json 路径，再整体提交线程池并行解析
    _NEW_BIC.clear()          # 本次运行的自动入库记录（结束前汇总打日志）
    log('[信息] 正在扫描待检文件夹…')
    dir_targets, all_errors = scan_dirs(root, cfg, stop_event)
    n_dirs = len(dir_targets)
    paths = [p for targets in dir_targets for p in targets]
    total = len(paths)
    log(f'[信息] 扫描完成：共 {n_dirs} 个文件夹、{total} 个待检 json')

    # 结果缓存：未修改的文件（修改时间/大小不变）且配置指纹一致时
    # 直接复用上次结果；开关关闭（cache=None）则全量检测
    cache = load_result_cache() if cfg.get('cache', True) else None
    fingerprint = cache_fingerprint(cfg)
    cache_stats = []          # 'hit' / 'miss' 标记（append 原子，线程安全够用）

    n_json = 0
    n_deleted = 0
    # 大批量小文件以读盘为主，多线程并行解析 json 可显著提速；
    # stop_event 传入 check_json：请求停止后尚未开始的任务直接跳过
    max_workers = min(8, os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = iter(pool.map(
            lambda p: check_json_cached(p, cfg, stop_event, cache,
                                        fingerprint, cache_stats), paths))
        stopped = False
        for targets in dir_targets:
            if stopped:
                break
            for jpath in targets:
                if stop_event.is_set():
                    stopped = True
                    break
                n_json += 1
                # 大批量时定期报进度，避免长时间无输出看似卡死
                if n_json % PROGRESS_EVERY == 0 and n_json < total:
                    log(f'[进度] 已检测 {n_json} / {total}')
                file_errors = next(results)
                # 检测正常的文件不打日志，日志框只显示报错信息
                if file_errors:
                    for etype, detail in file_errors:
                        all_errors.append((jpath, etype, detail))
                        log(f'  ✗ {os.path.basename(jpath)} ← {etype}：{detail}')

    if cache is not None:
        log(f'[信息] 结果缓存：命中 {cache_stats.count("hit")} 个，'
            f'实际检测 {cache_stats.count("miss")} 个')
        # 缓存瘦身：丢弃本次未扫描到的条目（换待检文件夹 / 文件已删的陈旧记录），
        # 缓存文件不再随历史使用无限增长；中途停止时不清（未扫完的文件下次仍可命中）
        if not stop_event.is_set():
            scanned = set(paths)
            for stale in [p for p in cache if p not in scanned]:
                del cache[stale]
        save_result_cache(cache)

    # 未注册箱主代码通过其余全部检测 → 已自动入库，汇总提示（不产生报错行）
    if _NEW_BIC:
        log(f'[信息] {len(_NEW_BIC)} 个未注册箱主代码已通过其余检测，'
            f'自动加入注册表：{"、".join(sorted(_NEW_BIC))}')

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

    # 无报错时不生成 Excel：目录里不留只有表头的空表，也省去打开确认的步骤
    if not all_errors:
        log('[信息] 未发现任何报错，本次不生成 Excel')
        out_xlsx = None
    else:
        out_xlsx = write_excel(out_xlsx, all_errors, macro=cfg.get('macro', True),
                               log=log)

    return {
        'dirs': n_dirs,
        'json': n_json,
        'errors': len(all_errors),
        'deleted': n_deleted,
        'out': out_xlsx,
    }


def write_excel(path, errors, macro=True, log=None):
    """报错写入 Excel：文件地址 / 是否修改完成（留空人工填）/ 备注。
    macro=True 且有宏模板时输出带宏 .xlsm：双击 A 列文件地址以列表模式打开
    LabelMe（整表按顺序切换，见 labelme批量打开.py）；宏参数存隐藏列 Z
    （Z2 LabelMe 完整路径、Z3 Python 解释器完整路径），
    并把启动脚本释放到输出文件同目录。
    宏开关关闭或模板缺失时降级为普通 .xlsx（无上述打开功能）。
    返回实际写出的路径：宏模板损坏时同样降级普通 .xlsx（换扩展名并打日志），
    保证已扫出的检测结果不丢"""
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, Alignment

    tmpl = template_path() if macro else None
    wb = None
    if tmpl:
        try:
            wb = load_workbook(tmpl, keep_vba=True)   # keep_vba=True 保留宏
        except Exception as e:
            # 模板损坏：降级普通 .xlsx（普通工作簿存 .xlsm 会报格式不符），
            # 宁可丢宏功能也不能丢整趟检测结果
            if log:
                log(f'[警告] 宏模板读取失败（{type(e).__name__}: {e}），'
                    f'降级输出普通 .xlsx')
            if path.lower().endswith('.xlsm'):
                path = path[:-len('.xlsm')] + '.xlsx'
            tmpl = None
    if tmpl:
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
        # Z 列隐藏参数供双击宏读取（Z2 LabelMe 完整路径、Z3 Python 解释器路径）
        ws['Z2'] = shutil.which('labelme') or ''
        ws['Z3'] = find_python_for_labelme()
        ws.column_dimensions['Z'].hidden = True
        # 释放 LabelMe 列表模式启动脚本到输出文件同目录，供宏调用；
        # 释放失败不影响 Excel 生成（宏找不到脚本会降级为单独打开文件）
        launcher = launcher_script_path()
        if launcher:
            try:
                shutil.copyfile(launcher, os.path.join(os.path.dirname(path),
                                                       'labelme批量打开.py'))
            except OSError:
                pass
    wb.save(path)
    return path


# ============================ 图形界面 ============================

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')

SETTINGS_PATH = os.path.join(app_dir(), '界面设置.json')


def load_ui_settings():
    """启动时读取界面记忆设置（上次待检文件夹 / 输出目录）；无文件或损坏返回空"""
    try:
        with open(SETTINGS_PATH, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def save_ui_settings(root, out_dir):
    """记住上次的待检文件夹与输出目录，下次启动时预填；保存失败不影响使用"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump({'root': root, 'out_dir': out_dir}, f,
                      ensure_ascii=False, indent=1)
    except OSError:
        pass


# 大批量检测时的界面保护：日志区最多保留行数（超出删最旧的）、
# 单次 _poll 最多刷入条数（其余留给下一轮，避免长时间霸占 UI 线程）
MAX_LOG_LINES = 5000
LOG_BATCH_LIMIT = 300
# 进度日志间隔：每检测多少个 json 报一次进度，避免长时间无输出看似卡死
PROGRESS_EVERY = 500

CHECK_ITEMS = [
    ('pairing',   'jpg/json 文件对应检测'),
    ('suffix',    '_fz/_oc 后缀检测（关闭时含此类标签的文件直接跳过）'),
    ('pair',      '标签一致性检测（箱号差1~2位且校验位相同才报不一致并给修改意见；校验位不同按不同箱子独立检测）'),
    ('digits',    '箱号缺位/位数检测'),
    ('ownercode', '箱主代码检测（前3位对BIC注册表，第4位限U/J/Z，校验位通过时未注册自动入库）'),
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
        self._set_wins = {}   # 已打开的集合管理窗口（箱型代码 / 豁免标签 / 箱主代码）

        # 上次的输出目录（界面设置记忆），首次使用为桌面
        settings = load_ui_settings()
        self.out_dir = settings.get('out_dir') or DESKTOP
        if not os.path.isdir(self.out_dir):
            self.out_dir = DESKTOP

        frm_paths = tk.Frame(master, padx=10, pady=8)
        frm_paths.pack(fill='x')
        self.ent_root, _ = self._path_row(frm_paths, 0, '待检文件夹：', self._pick_dir)
        default_out = os.path.join(self.out_dir, f'报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsm')
        self.ent_out, _ = self._path_row(frm_paths, 1, '输出Excel：', self._pick_out)
        self.ent_out.insert(0, default_out)
        # 最近一次自动生成的默认输出路径；输入框内容与之相同（或为空）即视为
        # 未自定义，仍随所选文件夹自动更新，方向键等按键不会造成误判
        self._out_default = default_out
        # 上次的待检文件夹仍存在时预填（把文件夹拖到 exe 图标上启动也走这里）
        last_root = settings.get('root', '')
        if last_root and os.path.isdir(last_root):
            self.set_root(last_root)

        frm_opts = tk.LabelFrame(master, text='输出与性能选项', padx=10, pady=6)
        frm_opts.pack(fill='x', padx=10, pady=4)
        self.chk_macro = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frm_opts, variable=self.chk_macro,
            text='生成带宏 Excel（.xlsm，双击文件地址打开 LabelMe 列表并定位到该行，可上下切换）'
        ).grid(row=0, column=0, sticky='w', pady=2)
        self.chk_cache = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frm_opts, variable=self.chk_cache,
            text='结果缓存（重跑时未修改的文件直接复用上次结果，配置改动后自动全量重检）'
        ).grid(row=1, column=0, sticky='w', pady=2)

        frm_checks = tk.LabelFrame(master, text='检测项开关（每箱按优先级顺序执行，命中即停；多箱报错互不阻断、逐箱累加）', padx=10, pady=6)
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
        self.btn_bic = tk.Button(frm_btn, text='箱主代码管理…', width=14, command=self.manage_bic)
        self.btn_bic.pack(side='left', padx=8)
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
        d = filedialog.askdirectory(
            initialdir=self.ent_root.get().strip() or DESKTOP)
        if d:
            self.set_root(d)

    def set_root(self, d):
        """填入待检文件夹并联动默认输出文件名（浏览选择 / 启动预填 /
        文件夹拖到 exe 图标上启动共用）。用户未自定义过输出地址时，
        随所选文件夹自动更新默认值（生成在上次使用的输出目录）"""
        self.ent_root.delete(0, 'end')
        self.ent_root.insert(0, d)
        cur = self.ent_out.get()
        if not cur.strip() or cur == self._out_default:
            name = os.path.basename(os.path.normpath(d))
            default_out = os.path.join(
                self.out_dir, f'{name}_报错汇总_{datetime.now():%Y%m%d_%H%M%S}.xlsx')
            self.ent_out.delete(0, 'end')
            self.ent_out.insert(0, default_out)
            self._out_default = default_out

    def _pick_out(self):
        f = filedialog.asksaveasfilename(defaultextension='.xlsm',
                                         filetypes=[('Excel 工作簿（带宏，支持点击打开 LabelMe）', '*.xlsm'),
                                                    ('Excel 工作簿', '*.xlsx')],
                                         initialdir=self.out_dir)
        if f:
            # 用户已自行选择 Excel 生成地址（与默认值不同），之后不再自动覆盖
            self.ent_out.delete(0, 'end')
            self.ent_out.insert(0, f)
            # 记住用户选择的输出目录，作为之后默认输出的生成位置
            self.out_dir = os.path.dirname(f) or DESKTOP

    # ==================== 箱型代码 / 豁免标签 / 箱主代码管理（增删改查） ====================

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

    def manage_bic(self):
        """打开 BIC 箱主代码管理窗口"""
        self._open_set_manager(
            'bic', 'BIC箱主代码管理', '箱主代码',
            '箱主代码前缀须为 3 位字母（如 MSC）。',
            lambda: BIC_PREFIXES, valid_bic_prefix, set_bic_prefixes,
            BASE_BIC_PREFIXES, 'BIC注册箱主代码',
            normalize=str.upper)

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
        cfg['cache'] = self.chk_cache.get()     # 性能选项：是否启用结果缓存
        if not any(v.get() for v in self.cfg_vars.values()):
            messagebox.showwarning('提示', '所有检测项均已关闭，将不会产生任何报错。')

        # 记住本次待检文件夹与输出目录，下次启动时预填
        save_ui_settings(root, os.path.dirname(out) or DESKTOP)

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
                     f"报错 {summary['errors']} 条，删除空文件夹 {summary['deleted']} 个。"]
            if summary['out']:
                lines.append(f"结果已保存至：{summary['out']}")
                # 按实际输出格式提示：.xlsm 才带双击打开 LabelMe 的宏功能
                if summary['out'].lower().endswith('.xlsm'):
                    lines.append('Excel 中：双击「文件地址」打开 LabelMe 列表并定位到该行，'
                                 '可用快捷键 D/A 上下切换（需启用宏，同目录已生成 labelme批量打开.py）。'
                                 '首次打开需点「启用内容」允许宏。')
                else:
                    lines.append('本次输出为普通 .xlsx（宏开关关闭或缺少宏模板），'
                                 '不具备双击文件地址打开 LabelMe 的功能。')
            else:
                lines.append('未发现任何报错，本次未生成 Excel。')
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
    if summary['out']:
        print(f"结果已保存至：{summary['out']}")
    else:
        print('未发现任何报错，本次未生成 Excel')


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
        app = CheckerApp(root)
        # 资源管理器把文件夹拖到 exe 图标上启动时，argv[1] 为该文件夹路径
        if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
            app.set_root(os.path.abspath(sys.argv[1]))
        root.mainloop()


if __name__ == '__main__':
    main()
