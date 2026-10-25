param(
    [Parameter(Mandatory = $true)] [string] $SourceDocx,
    [Parameter(Mandatory = $true)] [string] $OutputDocx,
    [Parameter(Mandatory = $true)] [string] $OutputPdf,
    [Parameter(Mandatory = $true)] [string] $InspectionJson
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $SourceDocx).Path
$output = [System.IO.Path]::GetFullPath($OutputDocx)
$pdf = [System.IO.Path]::GetFullPath($OutputPdf)
$inspection = [System.IO.Path]::GetFullPath($InspectionJson)
foreach ($path in @($output, $pdf, $inspection)) {
    if (Test-Path -LiteralPath $path) { throw 'Refusing to overwrite a roundtrip output.' }
    if (-not (Test-Path -LiteralPath (Split-Path -Parent $path) -PathType Container)) { throw 'Output parent directory is missing.' }
}
if ($source -eq $output) { throw 'Source and output must differ.' }
$word = New-Object -ComObject Word.Application
$owned = ($word.Documents.Count -eq 0)
$doc = $null
try {
    if (-not $owned) { throw 'Existing user Word documents were left untouched; use an isolated session.' }
    $word.Visible = $false; $word.DisplayAlerts = 0
    $readOnly = $true; $confirm = $false
    $doc = $word.Documents.Open([ref] $source, [ref] $confirm, [ref] $readOnly)
    [void] $doc.Fields.Update()
    $format = 16
    $doc.SaveAs2([ref] $output, [ref] $format)
    $noSave = 0; $doc.Close([ref] $noSave); $doc = $null
    $doc = $word.Documents.Open([ref] $output, [ref] $confirm, [ref] $readOnly)
    $items = @(); $index = 0
    foreach ($shape in $doc.InlineShapes) {
        $progId = try { [string] $shape.OLEFormat.ProgID } catch { '' }
        if ($progId -ne 'Equation.DSMT4') { continue }
        $index += 1
        $items += [ordered]@{ index = $index; page = [int] $shape.Range.Information(3);
            width_pt = [double] $shape.Width; height_pt = [double] $shape.Height;
            in_table = [bool] $shape.Range.Information(12); prog_id = $progId }
    }
    $pages = [int] $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($pdf, 17)
    $record = [ordered]@{ status = 'render_review_pending'; word_version = [string] $word.Version;
        pages = $pages; formula_count = $items.Count; saved_closed_reopened = $true;
        equations = $items; source_docx = $source; reopened_docx = $output; pdf = $pdf }
    $record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $inspection -Encoding UTF8
    Write-Output ("Word roundtrip and PDF export completed: " + $pages + ' pages; ' + $items.Count + ' MathType objects.')
}
finally {
    if ($null -ne $doc) { $noSave = 0; try { $doc.Close([ref] $noSave) } catch {} }
    if ($owned -and $word.Documents.Count -eq 0) { $noSave = 0; try { $word.Quit([ref] $noSave) } catch {} }
}
