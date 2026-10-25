param(
    [Parameter(Mandatory=$true)][string] $SourceDocx,
    [Parameter(Mandatory=$true)][string] $SourceManifest,
    [Parameter(Mandatory=$true)][string] $OutputDirectory,
    [string] $Python = 'python',
    [string] $Pptx,
    [string] $MathTypeTemplate,
    [ValidateRange(1,72)] [double] $MathTypeFullSizePt = 12
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $SourceDocx).Path
$manifest = (Resolve-Path -LiteralPath $SourceManifest).Path
$target = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $target) { throw 'OutputDirectory must be new; existing work is not overwritten.' }
$before = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
New-Item -ItemType Directory -Path $target | Out-Null
$scripts = Split-Path -Parent $PSCommandPath
$native = Join-Path $target 'report_native.docx'
$numbered = Join-Path $target 'report_numbered.docx'
$final = Join-Path $target 'report_reopened.docx'
$receipt = Join-Path $target 'conversion.json'
$arguments = @{SourceDocx=$source; OutputDocx=$native; SourceManifest=$manifest; EvidenceJson=$receipt; MathTypeFullSizePt=$MathTypeFullSizePt}
if ($MathTypeTemplate) { $arguments.MathTypeTemplate = $MathTypeTemplate }
& (Join-Path $scripts 'project_mathtype_convert.ps1') @arguments
& $Python -B (Join-Path $scripts 'project_equation_layout.py') --docx $native --manifest $manifest --output $numbered
if ($LASTEXITCODE -ne 0) { throw 'Equation layout failed.' }
& (Join-Path $scripts 'project_word_roundtrip.ps1') -SourceDocx $numbered -OutputDocx $final -OutputPdf (Join-Path $target 'report.pdf') -InspectionJson (Join-Path $target 'word_roundtrip.json')
if ($Pptx) { & (Join-Path $scripts 'project_ppt_roundtrip.ps1') -SourcePptx $Pptx -OutputDirectory (Join-Path $target 'presentation') }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $before) { throw 'Source DOCX changed during smoke test.' }
Write-Output 'Native Office flow completed. Inspect all rendered pages and formula meaning before recording a pass.'
