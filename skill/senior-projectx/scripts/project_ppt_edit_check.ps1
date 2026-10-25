param(
    [Parameter(Mandatory=$true)][string] $SourcePptx,
    [Parameter(Mandatory=$true)][string] $OutputPptx,
    [Parameter(Mandatory=$true)][string] $EvidenceJson,
    [Parameter(Mandatory=$true)][int] $ChartSlide,
    [Parameter(Mandatory=$true)][int] $TableSlide,
    [int] $TitleSlide=1,
    [int] $TitleShapeIndex=1,
    [int] $WorkbookSheetIndex=1,
    [string] $WorkbookCell='B2',
    [int] $TableRow=2,
    [int] $TableColumn=2
)
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $SourcePptx).Path
$target=[System.IO.Path]::GetFullPath($OutputPptx)
$evidence=[System.IO.Path]::GetFullPath($EvidenceJson)
foreach($path in @($target,$evidence)) {
    if(Test-Path -LiteralPath $path) {throw 'A new test output path is required.'}
    if(-not (Test-Path -LiteralPath (Split-Path -Parent $path) -PathType Container)) {throw 'Output parent must exist.'}
}
$sourceHash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$ppt=New-Object -ComObject PowerPoint.Application
$initial=$ppt.Presentations.Count
$deck=$null; $book=$null
try {
    # An actual deck window is required for reliable ChartData hosting.
    Copy-Item -LiteralPath $source -Destination $target
    $deck=$ppt.Presentations.Open($target,$false,$false,$true)
    $title=$deck.Slides.Item($TitleSlide).Shapes.Item($TitleShapeIndex)
    if($title.HasTextFrame -ne -1 -or $title.TextFrame.HasText -ne -1) {throw 'The selected title shape has no text.'}
    $oldTitle=$title.TextFrame.TextRange.Text
    $temporaryTitle=$oldTitle+' __ProjectX_EDIT_CHECK__'
    $title.TextFrame.TextRange.Text=$temporaryTitle
    $tableShape=@($deck.Slides.Item($TableSlide).Shapes | Where-Object {$_.HasTable -eq -1})[0]
    if($null -eq $tableShape) {throw 'No native table on the selected slide.'}
    $oldCell=$tableShape.Table.Cell($TableRow,$TableColumn).Shape.TextFrame.TextRange.Text
    $temporaryCell=$oldCell+' __ProjectX_EDIT_CHECK__'
    $tableShape.Table.Cell($TableRow,$TableColumn).Shape.TextFrame.TextRange.Text=$temporaryCell
    $chartShape=@($deck.Slides.Item($ChartSlide).Shapes | Where-Object {$_.HasChart -eq -1})[0]
    if($null -eq $chartShape) {throw 'No native chart on the selected slide.'}
    $chartShape.Chart.ChartData.Activate()
    $book=$chartShape.Chart.ChartData.Workbook
    $cell=$book.Worksheets.Item($WorkbookSheetIndex).Range($WorkbookCell)
    if($null -eq $cell.Value2 -or $cell.Value2 -is [string]) {throw 'Select one numeric chart-source cell.'}
    $oldValue=[double]$cell.Value2
    $cell.Value2=$oldValue+1.25
    # Embedded workbooks are saved by their presentation host. Standalone
    # Workbook.Save() is not supported for every Office embedding version.
    $book.Close($false); $book=$null
    $chartShape.Chart.Refresh()
    $deck.SaveAs($target,24); $deck.Close(); $deck=$null
    $deck=$ppt.Presentations.Open($target,$false,$false,$true)
    if($deck.Slides.Item($TitleSlide).Shapes.Item($TitleShapeIndex).TextFrame.TextRange.Text -ne $temporaryTitle) {throw 'Text edit did not persist.'}
    $tableShape=@($deck.Slides.Item($TableSlide).Shapes | Where-Object {$_.HasTable -eq -1})[0]
    if($tableShape.Table.Cell($TableRow,$TableColumn).Shape.TextFrame.TextRange.Text -ne $temporaryCell) {throw 'Table edit did not persist.'}
    $chartShape=@($deck.Slides.Item($ChartSlide).Shapes | Where-Object {$_.HasChart -eq -1})[0]
    $chartShape.Chart.ChartData.Activate()
    $book=$chartShape.Chart.ChartData.Workbook
    $cell=$book.Worksheets.Item($WorkbookSheetIndex).Range($WorkbookCell)
    if([Math]::Abs([double]$cell.Value2-($oldValue+1.25)) -gt 1e-10) {throw 'Workbook edit did not persist.'}
    $book.Close($false); $book=$null
    $editedHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if($editedHash -eq $sourceHash) {throw 'The saved edit test has no change.'}
    $deck.Close(); $deck=$null
    # Restore the entire disposable copy, including chart cache and embedded
    # workbook together. Their asynchronous caches must not diverge on restore.
    Copy-Item -LiteralPath $source -Destination $target -Force
    if((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $sourceHash) {throw 'Test-copy restoration failed.'}
    if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $sourceHash) {throw 'Source file changed.'}
    [ordered]@{status='pass';text_edit_persisted=$true;table_edit_persisted=$true;chart_workbook_edit_persisted=$true;edits_verified_before_restore=$true;edited_copy_sha256=$editedHash.ToLowerInvariant();test_values_restored=$true;restoration_method='byte_identical_source_copy_after_native_edit_verification';source_unchanged=$true;source_sha256=$sourceHash.ToLowerInvariant();output_sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant();chart_slide=$ChartSlide;table_slide=$TableSlide;workbook_cell=$WorkbookCell} | ConvertTo-Json | Set-Content -LiteralPath $evidence -Encoding UTF8
    Write-Output 'Native text, table and chart-data edits survived save/reopen; test values restored.'
} finally {
    if($null -ne $book) {try {$book.Close($false)} catch {}}
    if($null -ne $deck) {try {$deck.Close()} catch {}}
    try {if($initial -eq 0 -and $ppt.Presentations.Count -eq 0) {$ppt.Quit()}} catch {}
}
