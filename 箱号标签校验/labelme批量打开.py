# -*- coding: utf-8 -*-
"""LabelMe 列表模式启动器（由 箱号标签校验工具 生成的报错表 Excel 宏调用）。

用法：python labelme批量打开.py <路径列表文件> [起始索引]

路径列表文件为 UTF-8 文本（带不带 BOM 均可），每行一个文件地址
（图片或 LabelMe json 均可）。按列表顺序注入 labelme 的文件列表面板，
并定位到起始索引对应的文件；之后用 labelme 自带的 上一张/下一张
（快捷键 A / D 或菜单/工具栏按钮）按表内顺序来回切换，
修改保存（Ctrl+S）直接写回原文件。
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from labelme import __appname__
from labelme import _config, _locale
from labelme._app import MainWindow
from labelme._utils import apply_color_theme, new_icon


def read_paths(list_file: str) -> list[str]:
    """读取列表文件：每行一个文件地址，保持顺序，忽略空行"""
    text = Path(list_file).read_text(encoding='utf-8-sig')
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def run(list_file: str, start: int) -> None:
    paths = read_paths(list_file)
    if not paths:
        raise SystemExit(f'列表文件里没有读到任何路径：{list_file}')
    start = max(0, min(start, len(paths) - 1))

    # 以下与 labelme.__main__.main() 的启动流程一致
    config_file = Path(_config.get_user_config_file())
    config_overrides: dict = {}
    try:
        loaded_config = _config.load_config(
            config_file=config_file, config_overrides=config_overrides
        )
        language = loaded_config.get('language')
        color_theme = loaded_config.get('color_theme', 'system')
    except Exception:
        language = None
        color_theme = 'system'
    if not _locale.is_valid_language(language):
        language = None
    translator = QtCore.QTranslator()
    translator.load(
        language or QtCore.QLocale.system().name(),
        str(_locale.TRANSLATE_DIR),
    )

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    apply_color_theme(theme=color_theme)
    app.setApplicationName(__appname__)
    app.setWindowIcon(new_icon('icon'))
    app.installTranslator(translator)

    win = MainWindow(
        config_file=config_file,
        config_overrides=config_overrides,
        file_or_dir=None,
        output_dir=None,
    )

    # 核心：把列表文件的路径按顺序注入 labelme 文件列表
    file_list = win._docks.file_list
    file_list.clear()
    for p in paths:
        item = QtWidgets.QListWidgetItem(p)
        item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        item.setCheckState(QtCore.Qt.CheckState.Checked)
        file_list.addItem(item)

    # 启用 上一张/下一张（快捷键 A / D），定位到起始文件
    win._actions.open_prev_img.setEnabled(True)
    win._actions.open_next_img.setEnabled(True)
    file_list.setCurrentRow(start)

    win.show()
    win.raise_()
    sys.exit(app.exec())


def main() -> None:
    if len(sys.argv) < 2:
        QtWidgets.QMessageBox.critical(
            None, '参数错误',
            '用法：labelme批量打开.py <路径列表文件> [起始索引]',
        )
        sys.exit(1)

    start = 0
    try:
        if len(sys.argv) > 2:
            start = int(sys.argv[2])
    except ValueError:
        start = 0

    # 出错时弹窗提示并写日志（宏以隐藏窗口方式启动，控制台报错用户看不到）
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    try:
        run(sys.argv[1], start)
    except SystemExit:
        raise
    except Exception:
        err = traceback.format_exc()
        try:
            log = Path(__file__).with_suffix('.log')
            log.write_text(err, encoding='utf-8')
        except OSError:
            pass
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Critical, 'LabelMe 启动失败', err
        )
        box.show()
        # 宏以隐藏窗口方式启动本进程，弹窗可能被连带隐藏，用 Win32 API 强制显示
        try:
            import ctypes
            hwnd = int(box.winId())
            ctypes.windll.user32.ShowWindow(hwnd, 9)   # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        box.exec()
        sys.exit(1)


if __name__ == '__main__':
    main()
