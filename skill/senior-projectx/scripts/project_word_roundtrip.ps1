param(
    [Parameter(Mandatory = $true)] [string] $SourceDocx,
    [Parameter(Mandatory = $true)] [string] $OutputDocx,
    [Parameter(Mandatory = $true)] [string] $OutputPdf,
    [Parameter(Mandatory = $true)] [string] $InspectionJson,
    [ValidateSet('SEQ','REF','PAGEREF','PAGE','NUMPAGES')] [string[]] $RefreshFields = @('SEQ','REF'),
    [switch] $NoFieldRefresh
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
if (@($output, $pdf, $inspection | Sort-Object -Unique).Count -ne 3) {
    throw 'Choose separate output paths.'
}
$sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$previousWord = @(Get-Process -Name WINWORD -ErrorAction SilentlyContinue | ForEach-Object {
    "$($_.Id)/$($_.StartTime.ToUniversalTime().Ticks)"
})
$word = $null
$ownedProcess = $null
$doc = $null

function Get-SelectedWordFields($document, [string[]]$kinds, [switch]$Refresh) {
    # Update sequences first, then bookmark-based cross-references. Never update EMBED or links.
    foreach ($kind in $kinds) {
        foreach ($firstStory in $document.StoryRanges) {
            $story = $firstStory
            while ($null -ne $story) {
                foreach ($field in $story.Fields) {
                    $code = ([string]$field.Code.Text).Trim()
                    if ($code -notmatch "^\s*$kind(?:\s|$)") { continue }
                    if ($Refresh) {
                        if ($field.Locked) { throw "Selected Word field is locked: $code" }
                        if (-not $field.Update()) { throw "Word could not refresh field: $code" }
                    }
                    $value = [string]$field.Result.Text
                    if ($value -match '^(?:Error!|\u9519\u8bef[!\uFF01])') { throw "Word field resolved to an error: $code" }
                    [ordered]@{ kind=$kind; story=[int]$story.StoryType; code=$code; result=$value;
                        superscript=[int]$field.Result.Font.Superscript }
                }
                $story = $story.NextStoryRange
            }
        }
    }
}

try {
    $word = New-Object -ComObject Word.Application
    if ($word.Documents.Count -ne 0) { throw 'Existing Word documents were left untouched.' }
    $created = @(Get-Process -Name WINWORD -ErrorAction SilentlyContinue | Where-Object {
        "$($_.Id)/$($_.StartTime.ToUniversalTime().Ticks)" -notin $previousWord
    })
    if ($created.Count -ne 1) { throw 'Could not identify one task-owned Word process.' }
    $ownedProcess = @{ id = $created[0].Id; start = $created[0].StartTime.ToUniversalTime().Ticks }
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    # Never open the user's source in the COM session.
    [System.IO.File]::Copy($source, $output, $false)
    (Get-Item -LiteralPath $output).IsReadOnly = $false
    $doc = $word.Documents.Open($output, $false, $false, $false)
    if ($doc.FullName -ne $output -or $word.Documents.Count -ne 1) { throw 'Unexpected Word document identity.' }
    $wanted = @(@('SEQ','REF','PAGEREF','PAGE','NUMPAGES') | Where-Object { $_ -in $RefreshFields })
    $updated = @()
    if (-not $NoFieldRefresh) {
        $doc.Repaginate()
        $updated = @(Get-SelectedWordFields $doc $wanted -Refresh)
    }
    $doc.Save()
    $doc.Close(0); $doc = $null
    $doc = $word.Documents.Open($output, $false, $true, $false)
    if ($doc.FullName -ne $output -or $word.Documents.Count -ne 1) { throw 'Unexpected reopened document identity.' }
    $doc.Repaginate()
    $persisted = @()
    if (-not $NoFieldRefresh) {
        $persisted = @(Get-SelectedWordFields $doc $wanted)
        if ((ConvertTo-Json -InputObject $updated -Depth 8 -Compress) -cne (ConvertTo-Json -InputObject $persisted -Depth 8 -Compress)) {
            throw 'Selected field results differed after saving and reopening the document.'
        }
    }
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
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $sourceHash) { throw 'Source DOCX changed during roundtrip.' }
    $record = [ordered]@{ status = 'render_review_pending'; word_version = [string] $word.Version;
        pages = $pages; formula_count = $items.Count; saved_closed_reopened = $true;
        equations = $items; source_docx = $source; reopened_docx = $output; pdf = $pdf;
        office_math_count = [int]$doc.OMaths.Count; source_sha256 = $sourceHash;
        reopened_sha256 = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash;
        pdf_sha256 = (Get-FileHash -LiteralPath $pdf -Algorithm SHA256).Hash;
        refreshed_fields = $persisted; refreshed_field_count = $persisted.Count;
        word_process_id = $ownedProcess.id; word_process_start_ticks = $ownedProcess.start }
    $record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $inspection -Encoding UTF8
    Write-Output ("Word roundtrip and PDF export completed: " + $pages + ' pages; ' + $items.Count + ' MathType objects.')
}
finally {
    if ($null -ne $doc -and $doc.FullName -eq $output) { try { $doc.Close(0) } catch {} }
    if ($null -ne $word) {
        if ($null -ne $ownedProcess) {
            $process = Get-Process -Id $ownedProcess.id -ErrorAction SilentlyContinue
            if ($process -and $process.StartTime.ToUniversalTime().Ticks -eq $ownedProcess.start -and $word.Documents.Count -eq 0) {
                try { $word.Quit(0) } catch {}
            }
        }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
}
