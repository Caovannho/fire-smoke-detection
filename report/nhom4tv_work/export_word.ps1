$ErrorActionPreference = 'Stop'
$reportRoot = 'C:\HOCTAP_VALAMVIEC\Hoc Tap\fire-smoke-detection\report'
$docPath = Join-Path $reportRoot 'BaoCao_DoAn_Fire_Smoke_Detection_Nhom4TV.docx'
$pdfPath = Join-Path $reportRoot 'nhom4tv_work\verified.pdf'
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $doc = $word.Documents.Open($docPath, $false, $false, $false)
    foreach ($styleId in @(-20, -21, -22, -23, -24, -25, -26, -27, -28)) {
        $tocStyle = $doc.Styles.Item($styleId)
        $tocStyle.Font.Name = 'Times New Roman'
        $tocStyle.Font.Size = 11
        $tocStyle.ParagraphFormat.LineSpacingRule = 0
        $tocStyle.ParagraphFormat.SpaceAfter = 2
        $tocStyle.ParagraphFormat.SpaceBefore = 0
        $tocStyle.ParagraphFormat.FirstLineIndent = 0
    }
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    foreach ($tof in $doc.TablesOfFigures) { $tof.Update() }
    $doc.Repaginate()
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    foreach ($tof in $doc.TablesOfFigures) { $tof.Update() }
    $doc.Repaginate()
    $doc.Save()
    $pageCount = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($pdfPath, 17)
    Write-Output ('Pages: ' + $pageCount)
    Write-Output ('TOC: ' + $doc.TablesOfContents.Count)
    Write-Output ('Figure lists: ' + $doc.TablesOfFigures.Count)
    Write-Output $pdfPath
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    if ($null -ne $word) { $word.Quit() }
}
