# -*- coding: utf-8 -*-
"""重新生成 报错模板.xlsm（报错汇总表双击宏）。修改下方 VBA_CODE 后运行本脚本即可。

宏功能：双击 A 列「文件地址」→ 整表路径按序写入临时文件（UTF-8），
调用同目录 labelme批量打开.py 以列表模式打开 LabelMe 并定位到双击行，
之后可用 上一张/下一张（快捷键 A/D）按表内顺序切换；
找不到启动脚本或 Python 时降级为单独打开双击的文件。
宏参数存隐藏列：Z2 = LabelMe 完整路径，Z3 = Python 解释器完整路径。
"""
import os
import shutil

import win32com.client as win32

VBA_CODE = r'''Private Const CMD_CELL As String = "Z2"
Private Const PY_CELL As String = "Z3"
Private Const SCRIPT_NAME As String = "labelme批量打开.py"

Private Sub Worksheet_BeforeDoubleClick(ByVal Target As Range, Cancel As Boolean)
    ' 双击 A 列文件地址：整表为列表打开 LabelMe 并定位到该行，可上下切换
    If Target.Column = 1 And Target.Row > 1 And Target.Text <> "" Then
        Cancel = True
        LaunchLabelme Target
    End If
End Sub

Private Sub LaunchLabelme(Target As Range)
    Dim py As String, script As String, useList As Boolean
    py = Trim$(Me.Range(PY_CELL).Text)
    script = ThisWorkbook.Path & Application.PathSeparator & SCRIPT_NAME
    useList = False
    If py <> "" Then
        On Error Resume Next
        If Len(Dir$(script)) > 0 Then
            If Len(Dir$(py)) > 0 Then useList = True
        End If
        On Error GoTo 0
    End If

    If useList Then
        ' ---- 列表模式：整表路径按序写入临时文件（UTF-8），交给启动脚本 ----
        Dim lastRow As Long, r As Long, cnt As Long, idx As Long
        Dim v As String, listFile As String
        lastRow = Me.Cells(Me.Rows.Count, 1).End(xlUp).Row
        Dim stm As Object
        Set stm = CreateObject("ADODB.Stream")
        stm.Type = 2                 ' 文本模式
        stm.Charset = "utf-8"
        stm.Open
        For r = 2 To lastRow
            v = Trim$(CStr(Me.Cells(r, 1).Value))
            If v <> "" Then
                If r = Target.Row Then idx = cnt
                stm.WriteText v & vbCrLf
                cnt = cnt + 1
            End If
        Next r
        listFile = Environ$("TEMP") & "\labelme_filelist.txt"
        stm.SaveToFile listFile, 2   ' 覆盖写入
        stm.Close
        Dim sh As Object, style As Long, pyw As String
        Set sh = CreateObject("WScript.Shell")
        ' 优先 pythonw：无控制台窗口，报错弹窗可见；没有则用 python 隐藏窗口启动
        pyw = Left$(py, InStrRev(py, "\")) & "pythonw.exe"
        If Len(Dir$(pyw)) > 0 Then
            py = pyw
            style = 1
        Else
            style = 0
        End If
        sh.Run Chr(34) & py & Chr(34) & " " & Chr(34) & script & Chr(34) & _
               " " & Chr(34) & listFile & Chr(34) & " " & idx, style, False
    Else
        ' ---- 降级：单独打开双击的文件 ----
        Dim prog As String
        prog = Trim$(Me.Range(CMD_CELL).Text)
        If prog = "" Then prog = "labelme"
        Shell "cmd /c start """" " & Chr(34) & prog & Chr(34) & " " & _
              Chr(34) & Target.Text & Chr(34), vbMinimizedFocus
    End If
End Sub
'''


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '报错模板.xlsm')
    tmp = os.path.join(os.environ['TEMP'], '报错模板_new.xlsm')
    if os.path.exists(tmp):
        os.remove(tmp)

    xl = win32.DispatchEx('Excel.Application')
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Add()
        # 只留一张工作表，命名为 报错汇总
        while wb.Worksheets.Count > 1:
            wb.Worksheets(wb.Worksheets.Count).Delete()
        wb.Worksheets(1).Name = '报错汇总'
        wb.SaveAs(tmp, FileFormat=52)        # xlOpenXMLWorkbookMacroEnabled
        # 宏注入唯一的工作表文档模块（Type=100 且非 ThisWorkbook）
        for comp in wb.VBProject.VBComponents:
            if comp.Type == 100 and comp.Name != 'ThisWorkbook':
                mod = comp.CodeModule
                mod.DeleteLines(1, mod.CountOfLines)
                mod.AddFromString(VBA_CODE)
                break
        wb.Save()
        wb.Close(False)
    finally:
        xl.Quit()

    shutil.move(tmp, out)      # 临时文件在 %TEMP%（可能与工具目录跨盘），不能 os.replace
    print('已生成：', out)


if __name__ == '__main__':
    main()
