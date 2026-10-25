<#
.SYNOPSIS
Convert a Senior-ProjectX ToggleTeX DOCX to native MathType using the installed Word add-in.

.DESCRIPTION
Run once on a source-only DOCX. The script rejects existing OLE/OMML objects,
checks the source formula inventory, calls MathType's Word Toggle TeX command
exactly once, saves/reopens the result, and writes a deliberately pending
evidence record. It does not claim native semantic, visual, or editability QA.

The ordered source manifest is senior_projectx.project.equation_source.v1. Only body, table,
algorithm and caption contexts are supported by this whole-main-story helper;
header/footer/footnote formulas require a separate verified conversion route.
#>
param(
    [Parameter(Mandatory = $true)] [string] $SourceDocx,
    [Parameter(Mandatory = $true)] [string] $OutputDocx,
    [Parameter(Mandatory = $true)] [string] $SourceManifest,
    [Parameter(Mandatory = $true)] [string] $EvidenceJson,
    [string] $MathTypeTemplate = '',
    [ValidateRange(1,72)] [double] $MathTypeFullSizePt = 12
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-Sha256([string] $Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-FormulaSourceSchema([string] $Schema) {
    # Existing Project inventories keep their identity and file binding.
    $accepted = @('senior_projectx.project.equation_source.v1', 'nps.project.equation_source.v1')
    if ($Schema -cnotin $accepted) { throw 'Unexpected formula source schema.' }
}

function Get-RelativeFilePath([string] $BaseDirectory, [string] $TargetPath) {
    # Available in Windows PowerShell 5.1 as well as PowerShell 7.
    $baseFull = [System.IO.Path]::GetFullPath($BaseDirectory).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $baseUri = [System.Uri]::new($baseFull)
    $targetUri = [System.Uri]::new([System.IO.Path]::GetFullPath($TargetPath))
    if ($baseUri.Scheme -ne $targetUri.Scheme -or $baseUri.Host -ne $targetUri.Host) { return $TargetPath }
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Find-InstalledMathTypeTemplate($Application, [string] $ExplicitPath) {
    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        if (-not (Test-Path -LiteralPath $ExplicitPath -PathType Leaf)) { throw 'MathTypeTemplate does not exist.' }
        return [System.IO.Path]::GetFullPath($ExplicitPath)
    }
    $wordExe = Join-Path ([string] $Application.Path) 'WINWORD.EXE'
    $bitness = if ([Environment]::Is64BitOperatingSystem) { '64' } else { '32' }
    if (Test-Path -LiteralPath $wordExe -PathType Leaf) {
        $bytes = [System.IO.File]::ReadAllBytes($wordExe)
        $offset = [BitConverter]::ToInt32($bytes, 60)
        $machine = [BitConverter]::ToUInt16($bytes, $offset + 4)
        $bitness = if ($machine -eq 0x014c) { '32' } else { '64' }
    }
    foreach ($programRoot in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
        if ([string]::IsNullOrWhiteSpace($programRoot)) { continue }
        foreach ($name in @('MathType Commands 2016.dotm', 'MathType Commands 2013.dotm', 'MathType Commands.dotm')) {
            $candidate = Join-Path $programRoot ('MathType\Office Support\' + $bitness + '\' + $name)
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
        }
    }
    throw 'The installed Word MathType template could not be located. Supply -MathTypeTemplate explicitly.'
}

function Read-ZipXml([System.IO.Compression.ZipArchive] $Zip, [string] $Name) {
    $entry = $Zip.GetEntry($Name)
    if ($null -eq $entry) { throw "DOCX missing $Name" }
    $reader = [System.IO.StreamReader]::new($entry.Open())
    try { return [xml] $reader.ReadToEnd() }
    finally { $reader.Dispose() }
}

function Get-EquationShapes($Document) {
    $found = [System.Collections.Generic.List[object]]::new()
    foreach ($shape in $Document.InlineShapes) {
        if ($shape.Type -eq 1) {
            $progId = try { [string] $shape.OLEFormat.ProgID } catch { '' }
            if ($progId -eq 'Equation.DSMT4') { $found.Add($shape) }
        }
    }
    return ,$found
}

function Get-ExpectedFormulaTokens($Formulas) {
    # TeX is case-sensitive: $C$ and $c$ are different expressions.
    $tokens = [System.Collections.Generic.Dictionary[string,int]]::new([System.StringComparer]::Ordinal)
    foreach ($formula in $Formulas) {
        $token = if ($formula.placement -eq 'inline') { '$' + $formula.tex + '$' } else { '\[' + $formula.tex + '\]' }
        if (-not $tokens.ContainsKey($token)) { $tokens[$token] = 0 }
        $tokens[$token] += 1
    }
    return ,$tokens
}

function Assert-SourceFormulaTokens([string] $SourceText, $Formulas) {
    $expectedTokens = Get-ExpectedFormulaTokens $Formulas
    foreach ($token in $expectedTokens.Keys) {
        $observed = [regex]::Matches($SourceText, [regex]::Escape($token)).Count
        if ($observed -ne $expectedTokens[$token]) {
            throw "Source formula token count mismatch: $token; expected $($expectedTokens[$token]), observed $observed"
        }
    }
    $allTokens = [regex]::Matches($SourceText, '\$[^$\r\n]+\$|\\\[[\s\S]*?\\\]')
    if ($allTokens.Count -ne $Formulas.Count) { throw 'Source contains unregistered or unmatched ToggleTeX tokens.' }
    for ($i = 0; $i -lt $Formulas.Count; $i++) {
        $formula = $Formulas[$i]
        $expected = if ($formula.placement -eq 'inline') { '$' + $formula.tex + '$' } else { '\[' + $formula.tex + '\]' }
        if ($allTokens[$i].Value -cne $expected) {
            throw "Source formula order/content mismatch at $($formula.formula_id)."
        }
    }
}

$source = (Resolve-Path -LiteralPath $SourceDocx).Path
$manifestPath = (Resolve-Path -LiteralPath $SourceManifest).Path
$output = [System.IO.Path]::GetFullPath($OutputDocx)
$evidencePath = [System.IO.Path]::GetFullPath($EvidenceJson)
if ($source -eq $output) { throw 'SourceDocx and OutputDocx must differ.' }
if ((Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath $evidencePath)) {
    throw 'Refusing to overwrite an output DOCX or evidence JSON.'
}
if ([System.IO.Path]::GetExtension($source).ToLowerInvariant() -ne '.docx' -or
    [System.IO.Path]::GetExtension($output).ToLowerInvariant() -ne '.docx') {
    throw 'Source and output must be DOCX files.'
}
if (-not (Test-Path -LiteralPath ([System.IO.Path]::GetDirectoryName($output)) -PathType Container) -or
    -not (Test-Path -LiteralPath ([System.IO.Path]::GetDirectoryName($evidencePath)) -PathType Container)) {
    throw 'Output and evidence parent directories must already exist.'
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-FormulaSourceSchema ([string] $manifest.schema)
$sourceFromManifest = [string] $manifest.source_docx_path
$manifestSource = if ([System.IO.Path]::IsPathRooted($sourceFromManifest)) {
    [System.IO.Path]::GetFullPath($sourceFromManifest)
} else {
    [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $manifestPath) $sourceFromManifest))
}
if ($manifestSource -ne $source -or $manifest.source_docx_sha256 -ne (Get-Sha256 $source)) {
    throw 'Formula source manifest does not bind the current source DOCX.'
}
$formulas = @($manifest.formulas)
if ($formulas.Count -eq 0) { throw 'Formula manifest is empty.' }
if ($manifest.formula_count -ne $formulas.Count) { throw 'Formula manifest count does not match its entries.' }
$seenIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($formula in $formulas) {
    $id = [string] $formula.formula_id
    $tex = [string] $formula.tex
    $placement = [string] $formula.placement
    $context = [string] $formula.context
    if ([string]::IsNullOrWhiteSpace($id) -or -not $seenIds.Add($id) -or
        [string]::IsNullOrWhiteSpace($tex) -or $placement -notin @('inline', 'display') -or
        $context -notin @('body', 'table', 'algorithm', 'caption')) {
        throw "Unsupported, missing or duplicate formula entry: $id"
    }
}

$zip = [System.IO.Compression.ZipFile]::OpenRead($source)
try {
    foreach ($entry in $zip.Entries) {
        if ($entry.FullName -match '(^|/)(vbaProject|activeX|embeddings)(/|\.|$)') {
            throw 'Source DOCX contains VBA, ActiveX or embedded objects.'
        }
        if ($entry.FullName -like '*.rels') {
            $reader = [System.IO.StreamReader]::new($entry.Open())
            try {
                if ($reader.ReadToEnd() -match 'TargetMode\s*=\s*["'']External["'']') {
                    throw 'Source DOCX contains an external relationship.'
                }
            }
            finally { $reader.Dispose() }
        }
        if ($entry.FullName -like 'word/*.xml' -and $entry.FullName -notlike '*/_rels/*') {
            $xml = Read-ZipXml $zip $entry.FullName
            if ($xml.SelectNodes("//*[local-name()='OLEObject' or local-name()='oMath' or local-name()='oMathPara']").Count) {
                throw 'Source DOCX already contains OLE or OMML; ToggleTeX is reversible and must run on source only.'
            }
        }
    }
}
finally { $zip.Dispose() }

$stage = Join-Path ([System.IO.Path]::GetDirectoryName($output)) ('.senior-projectx-mathtype-' + [guid]::NewGuid().ToString('N') + '.docx')
Copy-Item -LiteralPath $source -Destination $stage
$word = New-Object -ComObject Word.Application
$ownsWordSession = ($word.Documents.Count -eq 0)
$wordVersion = ''
$placementChecks = [System.Collections.Generic.List[bool]]::new()
$conversionCommandCount = 0
$tableContextMarkers = [System.Collections.Generic.List[string]]::new()
try {
    if (-not $ownsWordSession) { throw 'An isolated Word session is required; existing user documents were left open.' }
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $wordVersion = [string] $word.Version
    $installedTemplate = Find-InstalledMathTypeTemplate $word $MathTypeTemplate
    $loadedMathType = $word.AddIns.Add($installedTemplate, $true)
    Write-Output 'Loaded the installed Word MathType command module.'
    Write-Output 'Opening the protected formula-source copy.'
    $doc = $word.Documents.Open($stage)
    try {
        $sourceText = [string] $doc.Content.Text
        Assert-SourceFormulaTokens $sourceText $formulas
        # Formula-only table cells need ordinary text context in some add-in versions.
        # Markers exist only in this working copy and are removed after the single toggle.
        foreach ($table in $doc.Tables) {
            foreach ($cell in $table.Range.Cells) {
                foreach ($paragraph in $cell.Range.Paragraphs) {
                    $cellText = ([regex]::Replace([string] $paragraph.Range.Text, '[\p{C}]', '')).Trim()
                    if (-not [regex]::IsMatch($cellText, '^\$[^$\r\n]+\$$')) { continue }
                    $range = $paragraph.Range.Duplicate
                    $finder = $range.Find
                    $finder.ClearFormatting(); $finder.Text = $cellText
                    $finder.MatchCase = $true; $finder.MatchWildcards = $false; $finder.Wrap = 0
                    if (-not $finder.Execute()) { throw 'A formula-only table cell could not be located.' }
                    $unique = [guid]::NewGuid().ToString('N')
                    $prefix = 'PXBEGIN' + $unique + ' '
                    $suffix = ' PXEND' + $unique
                    $range.InsertBefore($prefix)
                    $range.InsertAfter($suffix)
                    $tableContextMarkers.Add($prefix); $tableContextMarkers.Add($suffix)
                }
            }
        }
        $doc.Content.Select()
        # A second call reverses conversion. Never call this command twice on one selection.
        Write-Output 'Running the Word MathType Toggle TeX command once.'
        $word.Run('MTCommand_TeXToggle') | Out-Null
        $conversionCommandCount += 1
        foreach ($marker in $tableContextMarkers) {
            $range = $doc.Content.Duplicate
            $finder = $range.Find
            $finder.ClearFormatting(); $finder.Text = $marker
            $finder.MatchCase = $true
            $finder.MatchWildcards = $false
            $finder.Wrap = 0
            if (-not $finder.Execute()) { throw 'A temporary table-context marker was not found.' }
            if ($range.InlineShapes.Count -ne 0) { throw 'A temporary marker range overlaps a native equation.' }
            $range.Text = ''
        }
        $equations = Get-EquationShapes $doc
        if ($equations.Count -ne $formulas.Count) {
            $remaining = @([regex]::Matches([string] $doc.Content.Text, '\$[^$\r\n]+\$|\\\[[\s\S]*?\\\]') | ForEach-Object { $_.Value })
            $doc.Save()
            throw "MathType converted $($equations.Count) native objects for $($formulas.Count) source formulas. Unconverted TeX: $($remaining -join ' ; '). Diagnostic copy: $stage"
        }
        if ([regex]::IsMatch([string] $doc.Content.Text, '\$[^$\r\n]+\$|\\\[[\s\S]*?\\\]')) {
            throw 'MathType left ToggleTeX source in Word body/table/Algorithm text.'
        }
        for ($i = 0; $i -lt $formulas.Count; $i++) {
            $formula = $formulas[$i]
            $shape = $equations[$i]
            $inTable = [bool] $shape.Range.Information(12)
            $paragraphText = [string] $shape.Range.Paragraphs.Item(1).Range.Text
            $visibleText = [regex]::Replace($paragraphText, '[\p{C}\s]', '')
            $isDisplay = [string]::IsNullOrEmpty($visibleText)
            # A table cell can contain only an inline equation; an empty
            # surrounding paragraph does not make that object display math.
            $placementOk = if ($formula.placement -eq 'display') { $isDisplay } elseif ($inTable) { $true } else { -not $isDisplay }
            # Numbered display equations often sit in a borderless layout
            # table; that is still body context, not a data table formula.
            $contextOk = if ($formula.context -eq 'table') { $inTable } elseif ($formula.placement -eq 'display') { $true } else { -not $inTable }
            if ($formula.context -eq 'algorithm') {
                if ([string]::IsNullOrWhiteSpace([string] $formula.anchor_text)) {
                    throw "Algorithm formula $($formula.formula_id) requires anchor_text."
                }
                $contextOk = $contextOk -and $paragraphText.Contains([string] $formula.anchor_text)
            }
            if (-not ($placementOk -and $contextOk)) {
                throw "Word placement/context mismatch for $($formula.formula_id)."
            }
            # The macro uses its MathType Full size; match the displayed object
            # to the source role. Native contents remain editable and unchanged.
            $targetSize = if ($formula.font_size_pt) { [double] $formula.font_size_pt } elseif ($formula.context -eq 'table') { 10.5 } else { 12.0 }
            if ($targetSize -le 0 -or $targetSize -gt 72) { throw 'Invalid source formula display size.' }
            $shape.LockAspectRatio = 0
            $naturalWidth = [double] $shape.Width
            $naturalHeight = [double] $shape.Height
            $shape.Width = [single] ($naturalWidth * $targetSize / $MathTypeFullSizePt)
            $shape.Height = [single] ($naturalHeight * $targetSize / $MathTypeFullSizePt)
            $shape.LockAspectRatio = -1
            $placementChecks.Add($true)
        }
        $doc.Save()
    }
    finally { $taskNoSave = 0; $doc.Close([ref] $taskNoSave) }
    $reopened = $word.Documents.Open($stage, $false, $true)
    try {
        $again = Get-EquationShapes $reopened
        if ($again.Count -ne $formulas.Count) { throw 'Native equation count changed on Word reopen.' }
    }
    finally { $taskNoSave = 0; $reopened.Close([ref] $taskNoSave) }
}
finally {
    if ($ownsWordSession -and $word.Documents.Count -eq 0) {
        $taskNoSave = 0
        try { $word.Quit([ref] $taskNoSave) } catch { Write-Warning ('Owned Word session cleanup failed: ' + $_.Exception.Message) }
    }
}

$zip = [System.IO.Compression.ZipFile]::OpenRead($stage)
try {
    $xml = Read-ZipXml $zip 'word/document.xml'
    $nodes = @($xml.SelectNodes("//*[local-name()='OLEObject']"))
    if ($nodes.Count -ne $formulas.Count) { throw 'OOXML OLE count differs from Word native count.' }
    $keys = @($nodes | ForEach-Object {
        'word/document.xml#' + $_.GetAttribute('id', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    })
    if ($keys | Where-Object { $_ -eq 'word/document.xml#' }) { throw 'OLE relationship ID is missing.' }
}
finally { $zip.Dispose() }

Move-Item -LiteralPath $stage -Destination $output
$records = [ordered] @{}
for ($i = 0; $i -lt $formulas.Count; $i++) {
    $formula = $formulas[$i]
    $records[$keys[$i]] = [ordered] @{
        formula_id = [string] $formula.formula_id
        expected_tex = [string] $formula.tex
        placement = [string] $formula.placement
        context = [string] $formula.context
        display_font_size_pt = if ($formula.font_size_pt) { [double] $formula.font_size_pt } elseif ($formula.context -eq 'table') { 10.5 } else { 12.0 }
        native_full_size_pt = $MathTypeFullSizePt
        word_placement_machine_checked = $placementChecks[$i]
        word_placement_checked = $false
        editable_after_reopen = $false
        expected_source = 'pending_independent_mathtype_conversion'
        expected_native_file = $null
        native_meaning_checked = $false
        preview_matches_native = $false
        word_render_checked = $false
        render_artifact = $null
    }
}
$evidenceDir = [System.IO.Path]::GetDirectoryName($evidencePath)
$record = [ordered] @{
    schema = 'senior_projectx.project.mathtype_conversion.v1'
    status = 'pending_native_and_visual_review'
    final_docx_sha256 = Get-Sha256 $output
    source_manifest_path = Get-RelativeFilePath $evidenceDir $manifestPath
    source_manifest_schema = [string] $manifest.schema
    source_manifest_sha256 = Get-Sha256 $manifestPath
    conversion_method = 'Word MathType Commands 2016.dotm MTCommand_TeXToggle'
    conversion_command_count = $conversionCommandCount
    conversion_strategy = 'single_main_story_toggle_with_temporary_table_context'
    temporary_table_context_count = [int] ($tableContextMarkers.Count / 2)
    native_ranges_retoggled = $false
    word_version = $wordVersion
    mathtype_template = $installedTemplate
    reopened_docx = $null
    equations = $records
    review_note = 'Native MTEF, independent expected conversion, Word page review and reopen editability are still required.'
}
$record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
Write-Output "MathType conversion completed; evidence pending review: $output"
