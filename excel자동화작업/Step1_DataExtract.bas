' ===============================================
' 근태 자동화 시스템 - 통합 모듈
' 파일: 자동화 테이블.xlsm에 저장
' ===============================================
Option Explicit

' ═══════════════════════════════════════════════════════════════
' 1단계: 데이터 추출
' ═══════════════════════════════════════════════════════════════
Sub Step1_ExtractData()
    Dim srcPath As String
    Dim srcWB As Workbook
    Dim srcWS As Worksheet
    Dim tgtWS As Worksheet
    
    srcPath = SelectSourceFile()
    If srcPath = "" Then
        MsgBox "파일이 선택되지 않았습니다.", vbExclamation
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Set srcWB = Workbooks.Open(srcPath, ReadOnly:=True)
    
    On Error Resume Next
    Set srcWS = srcWB.Sheets("근태기록")
    On Error GoTo 0
    
    If srcWS Is Nothing Then
        MsgBox "원본 파일에 '근태기록' 시트가 없습니다.", vbCritical
        srcWB.Close SaveChanges:=False
        Exit Sub
    End If
    
    Set tgtWS = ThisWorkbook.Sheets(1)
    Call CopyAttendanceData(srcWS, tgtWS)
    
    srcWB.Close SaveChanges:=False
    Application.ScreenUpdating = True
    
    MsgBox "1단계 완료: 데이터 추출이 완료되었습니다!" & vbCrLf & _
           "다음: Step2_RefineData 실행", vbInformation
End Sub

Private Function SelectSourceFile() As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    
    With fd
        .Title = "원본 근태 파일 선택"
        .Filters.Clear
        .Filters.Add "Excel 파일", "*.xlsm; *.xlsx; *.xls"
        .AllowMultiSelect = False
        .InitialFileName = ThisWorkbook.Path & "\"
        
        If .Show = True Then
            SelectSourceFile = .SelectedItems(1)
        Else
            SelectSourceFile = ""
        End If
    End With
End Function

Private Sub CopyAttendanceData(srcWS As Worksheet, tgtWS As Worksheet)
    Dim infoRows As Variant, dataRows As Variant
    Dim i As Long, empName As String
    
    infoRows = Array(5, 8, 11, 14, 17, 20, 23, 26, 29, 32)
    dataRows = Array(6, 9, 12, 15, 18, 21, 24, 27, 30, 33)
    
    For i = LBound(infoRows) To UBound(infoRows)
        empName = srcWS.Cells(infoRows(i), 11).Value
        If Trim(empName) = "" Then GoTo NextEmployee
        
        srcWS.Range("A" & infoRows(i) & ":AE" & infoRows(i)).Copy
        tgtWS.Range("A" & infoRows(i)).PasteSpecial Paste:=xlPasteValues
        
        srcWS.Range("A" & dataRows(i) & ":AE" & dataRows(i)).Copy
        tgtWS.Range("A" & dataRows(i)).PasteSpecial Paste:=xlPasteValues
NextEmployee:
    Next i
    Application.CutCopyMode = False
End Sub

' ═══════════════════════════════════════════════════════════════
' 2단계: 데이터 정제 (설정시트 기반 정렬 포함)
' ═══════════════════════════════════════════════════════════════
Sub Step2_RefineData()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(1)
    
    Application.ScreenUpdating = False
    Randomize
    
    ' 설정시트가 있으면 직원 순서 정렬 먼저 수행
    On Error Resume Next
    Dim settingsWS As Worksheet
    Set settingsWS = ThisWorkbook.Sheets("설정시트")
    On Error GoTo 0
    
    If Not settingsWS Is Nothing Then
        Call ReorderBySettings(ws, settingsWS)
    End If
    
    Call FillDateHeaders(ws)
    Call RefineAttendanceData(ws)
    Call ClearHiddenAreas(ws)
    
    Application.ScreenUpdating = True
    MsgBox "2단계 완료: 데이터 정제가 완료되었습니다!", vbInformation
End Sub

' ─────────────────────────────────────────────────
' 설정시트 기반 직원 순서 재정렬
' 설정시트 구조: A열=순서, B열=성명, 1행=헤더
' ─────────────────────────────────────────────────
Private Sub ReorderBySettings(ws As Worksheet, settingsWS As Worksheet)
    Dim infoRows As Variant, dataRows As Variant
    Dim i As Long, j As Long
    Dim settingsNames() As String
    Dim settingsCount As Long
    Dim lastRow As Long
    
    infoRows = Array(5, 8, 11, 14, 17, 20, 23, 26, 29, 32)
    dataRows = Array(6, 9, 12, 15, 18, 21, 24, 27, 30, 33)
    
    ' 설정시트에서 이름 가져오기 (B열, 2행부터)
    lastRow = settingsWS.Cells(settingsWS.Rows.Count, 2).End(xlUp).Row
    If lastRow < 2 Then Exit Sub
    
    settingsCount = 0
    For i = 2 To lastRow
        If Trim(settingsWS.Cells(i, 2).Value) <> "" Then
            ReDim Preserve settingsNames(settingsCount)
            settingsNames(settingsCount) = Trim(settingsWS.Cells(i, 2).Value)
            settingsCount = settingsCount + 1
        End If
    Next i
    
    If settingsCount = 0 Then Exit Sub
    
    ' 현재 데이터를 배열에 저장
    Dim empNames(9) As String
    Dim empInfoData(9) As Variant
    Dim empDataData(9) As Variant
    Dim empCount As Long
    empCount = 0
    
    For i = 0 To UBound(infoRows)
        Dim currentName As String
        currentName = Trim(ws.Cells(infoRows(i), 11).Value) ' K열
        If currentName <> "" Then
            empNames(empCount) = currentName
            empInfoData(empCount) = ws.Range("A" & infoRows(i) & ":AE" & infoRows(i)).Value
            empDataData(empCount) = ws.Range("A" & dataRows(i) & ":AE" & dataRows(i)).Value
            empCount = empCount + 1
        End If
    Next i
    
    If empCount = 0 Then Exit Sub
    
    ' 정렬된 결과 배열
    Dim sortedInfoData(9) As Variant
    Dim sortedDataData(9) As Variant
    Dim sortedNames(9) As String
    Dim sortedCount As Long
    Dim usedFlags(9) As Boolean
    
    sortedCount = 0
    
    ' 설정시트 순서대로 매칭
    For i = 0 To settingsCount - 1
        If sortedCount > 9 Then Exit For
        
        Dim foundIdx As Long
        foundIdx = -1
        
        For j = 0 To empCount - 1
            If Not usedFlags(j) And empNames(j) = settingsNames(i) Then
                foundIdx = j
                usedFlags(j) = True
                Exit For
            End If
        Next j
        
        If foundIdx >= 0 Then
            sortedNames(sortedCount) = empNames(foundIdx)
            sortedInfoData(sortedCount) = empInfoData(foundIdx)
            sortedDataData(sortedCount) = empDataData(foundIdx)
            sortedCount = sortedCount + 1
        End If
    Next i
    
    ' 매칭되지 않은 기존 직원도 마지막에 추가 (데이터 보존)
    For j = 0 To empCount - 1
        If Not usedFlags(j) And sortedCount <= 9 Then
            sortedNames(sortedCount) = empNames(j)
            sortedInfoData(sortedCount) = empInfoData(j)
            sortedDataData(sortedCount) = empDataData(j)
            sortedCount = sortedCount + 1
        End If
    Next j
    
    ' 시트에 적용
    For i = 0 To sortedCount - 1
        ws.Range("A" & infoRows(i) & ":AE" & infoRows(i)).ClearContents
        ws.Range("A" & dataRows(i) & ":AE" & dataRows(i)).ClearContents
        
        If Not IsEmpty(sortedInfoData(i)) Then
            ws.Range("A" & infoRows(i) & ":AE" & infoRows(i)).Value = sortedInfoData(i)
            ws.Range("A" & dataRows(i) & ":AE" & dataRows(i)).Value = sortedDataData(i)
        End If
    Next i
End Sub

' ─────────────────────────────────────────────────
' 날짜 헤더 자동 채우기
' ─────────────────────────────────────────────────
Private Sub FillDateHeaders(ws As Worksheet)
    Dim dateRows As Variant, dtR As Variant
    Dim c As Long, headerFmt As String
    
    dateRows = Array(4, 7, 10, 13, 16, 19, 22, 25, 28, 31)
    
    For Each dtR In dateRows
        headerFmt = ws.Cells(dtR, 1).NumberFormat
        For c = 2 To 31
            With ws.Cells(dtR, c)
                If Trim(.Value) = "" Then
                    .Value = ws.Cells(dtR, c - 1).Value + 1
                    .NumberFormat = headerFmt
                    .Font.Name = "바탕"
                    .Font.Size = 12
                    .Font.Color = RGB(0, 0, 139)
                End If
            End With
        Next c
    Next dtR
End Sub

' ─────────────────────────────────────────────────
' 출퇴근 데이터 정제
' ─────────────────────────────────────────────────
Private Sub RefineAttendanceData(ws As Worksheet)
    Dim dateRows As Variant
    Dim r As Long, c As Long, cell As Range
    Dim inStart As String, inEnd As String
    Dim outStart As String, outEnd As String
    
    dateRows = Array(4, 7, 10, 13, 16, 19, 22, 25, 28, 31)
    
    For r = 5 To 33
        If IsInArray(r, dateRows) Then GoTo NextRow
        
        For c = 1 To 31
            Set cell = ws.Cells(r, c)
            
            If cell.MergeCells Then GoTo NextCell
            If cell.Interior.Color = RGB(0, 176, 240) Then GoTo NextCell
            
            If r = 6 And c >= 26 And c <= 31 Then
                inStart = "08:00": inEnd = "08:30"
                outStart = "17:30": outEnd = "17:35"
            Else
                inStart = "08:40": inEnd = "08:50"
                outStart = "18:00": outEnd = "18:10"
            End If
            
            Dim origFmt As String, origIndent As Long, origShrink As Boolean
            origFmt = cell.NumberFormat
            origIndent = cell.IndentLevel
            origShrink = cell.ShrinkToFit
            
            If c > 25 Then
                Call ProcessFutureDate(cell, c, inStart, inEnd, outStart, outEnd, origFmt, origIndent, origShrink)
            Else
                Call ProcessExistingDate(cell, inStart, inEnd, outStart, outEnd, origFmt, origIndent, origShrink)
            End If
NextCell:
        Next c
NextRow:
    Next r
End Sub

Private Sub ProcessFutureDate(cell As Range, dayNum As Long, inStart As String, inEnd As String, _
                               outStart As String, outEnd As String, origFmt As String, origIndent As Long, origShrink As Boolean)
    Dim chkDate As Date
    chkDate = DateSerial(Year(Date), Month(Date), dayNum)
    
    If Weekday(chkDate, vbMonday) > 5 Then
        cell.ClearContents
    Else
        cell.Value = RandomTime(inStart, inEnd) & vbLf & RandomTime(outStart, outEnd)
        With cell
            .WrapText = True
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlTop
            .NumberFormat = origFmt
            .IndentLevel = origIndent
            .ShrinkToFit = origShrink
        End With
    End If
End Sub

Private Sub ProcessExistingDate(cell As Range, inStart As String, inEnd As String, _
                                 outStart As String, outEnd As String, origFmt As String, origIndent As Long, origShrink As Boolean)
    If InStr(cell.Value, ":") = 0 Then Exit Sub
    
    Dim timesArr As Variant, cleanTimes() As String
    Dim i As Long, t As String, cnt As Long
    
    timesArr = Split(cell.Value, vbLf)
    cnt = 0
    
    For i = LBound(timesArr) To UBound(timesArr)
        t = Trim(timesArr(i))
        If Len(t) > 0 Then
            ReDim Preserve cleanTimes(cnt)
            cleanTimes(cnt) = t
            cnt = cnt + 1
        End If
    Next i
    
    If cnt = 0 Then Exit Sub
    
    If cnt >= 3 Then
        SortTimes cleanTimes
        Dim firstTime As String, lastTime As String
        firstTime = cleanTimes(0)
        lastTime = cleanTimes(UBound(cleanTimes))
        ReDim cleanTimes(1)
        cleanTimes(0) = firstTime
        cleanTimes(1) = lastTime
    ElseIf cnt = 2 Then
        SortTimes cleanTimes
        If TimeValue(cleanTimes(1)) < TimeValue("12:00") Then
            Dim origIn As String
            origIn = cleanTimes(0)
            ReDim cleanTimes(1)
            cleanTimes(0) = origIn
            cleanTimes(1) = RandomTime(outStart, outEnd)
        End If
    ElseIf cnt = 1 Then
        Dim singleTime As String
        singleTime = cleanTimes(0)
        ReDim cleanTimes(1)
        If TimeValue(singleTime) < TimeValue("12:00") Then
            cleanTimes(0) = singleTime
            cleanTimes(1) = RandomTime(outStart, outEnd)
        Else
            cleanTimes(0) = RandomTime(inStart, inEnd)
            cleanTimes(1) = singleTime
        End If
    End If
    
    cell.Value = cleanTimes(0) & vbLf & cleanTimes(1)
    With cell
        .WrapText = True
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlTop
        .NumberFormat = origFmt
        .IndentLevel = origIndent
        .ShrinkToFit = origShrink
    End With
End Sub

Private Sub ClearHiddenAreas(ws As Worksheet)
    Dim hideAreas As Variant, addr As Variant
    hideAreas = Array("Z5:AE5", "Z8:AE8", "Z11:AE11", "Z14:AE14", _
                      "Z17:AE17", "Z20:AE20", "Z23:AE23", "Z26:AE26", _
                      "Z29:AE29", "Z32:AE32")
    For Each addr In hideAreas
        ws.Range(addr).ClearContents
    Next addr
End Sub

' ═══════════════════════════════════════════════════════════════
' 유틸리티 함수
' ═══════════════════════════════════════════════════════════════
Private Sub SortTimes(arr() As String)
    Dim i As Long, j As Long, tmp As String
    For i = LBound(arr) To UBound(arr) - 1
        For j = i + 1 To UBound(arr)
            If TimeValue(arr(i)) > TimeValue(arr(j)) Then
                tmp = arr(i): arr(i) = arr(j): arr(j) = tmp
            End If
        Next j
    Next i
End Sub

Private Function RandomTime(t1 As String, t2 As String) As String
    Dim h1 As Integer, m1 As Integer, h2 As Integer, m2 As Integer
    Dim minTot As Long, maxTot As Long, rndTot As Long
    h1 = Hour(TimeValue(t1)): m1 = Minute(TimeValue(t1))
    h2 = Hour(TimeValue(t2)): m2 = Minute(TimeValue(t2))
    minTot = h1 * 60 + m1
    maxTot = h2 * 60 + m2
    rndTot = Int((maxTot - minTot + 1) * Rnd + minTot)
    RandomTime = Format(TimeSerial(rndTot \ 60, rndTot Mod 60, 0), "hh:mm")
End Function

Private Function IsInArray(val As Long, arr As Variant) As Boolean
    Dim x As Long
    For x = LBound(arr) To UBound(arr)
        If arr(x) = val Then IsInArray = True: Exit Function
    Next x
    IsInArray = False
End Function

' ═══════════════════════════════════════════════════════════════
' 3단계: 최종 양식으로 데이터 전송
' ═══════════════════════════════════════════════════════════════
Sub Step3_MapToFinalTemplate()
    Dim srcWS As Worksheet
    Dim tgtWB As Workbook
    Dim tgtWS As Worksheet
    Dim tgtPath As String
    
    Set srcWS = ThisWorkbook.Sheets(1)
    
    ' 기본양식 파일 경로 (같은 폴더에 있는 파일)
    tgtPath = ThisWorkbook.Path & "\기본양식-메크로.xlsm"
    
    ' 파일 존재 확인
    If Dir(tgtPath) = "" Then
        MsgBox "기본양식-메크로.xlsm 파일을 찾을 수 없습니다." & vbCrLf & _
               "경로: " & tgtPath, vbCritical
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Set tgtWB = Workbooks.Open(tgtPath)
    Set tgtWS = tgtWB.Sheets(1)
    
    ' 데이터 전송 실행
    Call TransferDataToTemplate(srcWS, tgtWS)
    
    Application.ScreenUpdating = True
    MsgBox "3단계 완료: 기본양식으로 데이터 전송이 완료되었습니다!" & vbCrLf & _
           "파일을 확인하고 저장하세요.", vbInformation
End Sub

Private Function SelectTargetFile() As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    
    With fd
        .Title = "기본양식 파일 선택"
        .Filters.Clear
        .Filters.Add "Excel 파일", "*.xlsm; *.xlsx; *.xls"
        .AllowMultiSelect = False
        .InitialFileName = ThisWorkbook.Path & "\"
        
        If .Show = True Then
            SelectTargetFile = .SelectedItems(1)
        Else
            SelectTargetFile = ""
        End If
    End With
End Function

' ─────────────────────────────────────────────────
' 자동화 테이블 → 기본양식 데이터 전송
' 기본양식 구조: C열=이름(6,8,10,12...), 그 아래 행=출퇴근
' ─────────────────────────────────────────────────
Private Sub TransferDataToTemplate(srcWS As Worksheet, tgtWS As Worksheet)
    ' 자동화 테이블 행 (정보행, 데이터행)
    Dim srcInfoRows As Variant, srcDataRows As Variant
    srcInfoRows = Array(5, 8, 11, 14, 17, 20, 23, 26, 29, 32)
    srcDataRows = Array(6, 9, 12, 15, 18, 21, 24, 27, 30, 33)
    
    ' 기본양식 행 (이름행, 데이터행) - 6,7 / 8,9 / 10,11...
    Dim tgtNameRows As Variant, tgtDataRows As Variant
    tgtNameRows = Array(6, 8, 10, 12, 14, 16, 18, 20, 22, 24)
    tgtDataRows = Array(7, 9, 11, 13, 15, 17, 19, 21, 23, 25)
    
    Dim i As Long, j As Long
    Dim srcName As String, tgtName As String
    Dim matchFound As Boolean
    Dim transferCount As Long
    
    transferCount = 0
    
    ' 소스(자동화 테이블)의 각 직원에 대해
    For i = 0 To UBound(srcInfoRows)
        srcName = Trim(srcWS.Cells(srcInfoRows(i), 11).Value) ' K열
        If srcName = "" Then GoTo NextSrc
        
        ' 대상(기본양식)에서 같은 이름 찾기
        matchFound = False
        For j = 0 To UBound(tgtNameRows)
            tgtName = Trim(tgtWS.Cells(tgtNameRows(j), 3).Value) ' C열
            
            If srcName = tgtName Then
                ' 출퇴근 데이터 복사 (A:AE, 값만)
                srcWS.Range("A" & srcDataRows(i) & ":AE" & srcDataRows(i)).Copy
                tgtWS.Range("A" & tgtDataRows(j)).PasteSpecial xlPasteValues
                
                ' 가운데 맞춤 서식 적용
                tgtWS.Range("A" & tgtDataRows(j) & ":AE" & tgtDataRows(j)).VerticalAlignment = xlCenter
                
                matchFound = True
                transferCount = transferCount + 1
                Exit For
            End If
        Next j
NextSrc:
    Next i
    
    Application.CutCopyMode = False
    
    If transferCount = 0 Then
        MsgBox "매칭되는 이름이 없습니다. C열 이름을 확인하세요.", vbExclamation
    End If
End Sub

' ═══════════════════════════════════════════════════════════════
' 전체 원클릭 실행
' ═══════════════════════════════════════════════════════════════
Sub RunAllSteps()
    Call Step1_ExtractData
    Call Step2_RefineData
    Call Step3_MapToFinalTemplate
    
    ' 정제 데이터 정리 (자동화 테이블 초기화)
    Call ClearIntermediateData
    
    MsgBox "전체 자동화 완료!" & vbCrLf & _
           "자동화 테이블이 초기화되었습니다.", vbInformation
End Sub

' ─────────────────────────────────────────────────
' 자동화 테이블 정제 데이터 정리 (초기 상태로)
' ─────────────────────────────────────────────────
Private Sub ClearIntermediateData()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(1)
    
    Dim infoRows As Variant, dataRows As Variant
    Dim i As Long
    
    infoRows = Array(5, 8, 11, 14, 17, 20, 23, 26, 29, 32)
    dataRows = Array(6, 9, 12, 15, 18, 21, 24, 27, 30, 33)
    
    ' 정보행과 데이터행의 데이터 클리어 (서식 유지)
    For i = 0 To UBound(infoRows)
        ws.Range("A" & infoRows(i) & ":AE" & infoRows(i)).ClearContents
        ws.Range("A" & dataRows(i) & ":AE" & dataRows(i)).ClearContents
    Next i
End Sub
