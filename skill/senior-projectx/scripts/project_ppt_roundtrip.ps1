param(
    [Parameter(Mandatory=$true)][string] $SourcePptx,
    [Parameter(Mandatory=$true)][string] $OutputDirectory
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $SourcePptx).Path
$sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$target = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $target) { throw 'OutputDirectory must be new; existing work is not overwritten.' }
New-Item -ItemType Directory -Path $target | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
$initial = [int] $ppt.Presentations.Count
$deck = $null
try {
    $copy = Join-Path $target 'briefing_reopened.pptx'
    Copy-Item -LiteralPath $source -Destination $copy
    $deck = $ppt.Presentations.Open($copy, $false, $false, $false)
    $deck.Save()
    $deck.Close(); $deck = $null
    $deck = $ppt.Presentations.Open($copy, $false, $false, $false)
    $pages = @()
    foreach ($slide in $deck.Slides) {
        $charts = 0; $tables = 0; $native = 0; $texts = 0
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasChart -eq -1) { $charts++ }
            if ($shape.HasTable -eq -1) { $tables++ }
            if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) { $texts++ }
            if ($shape.Type -eq 7) {
                try { if ($shape.OLEFormat.ProgID -eq 'Equation.DSMT4') { $native++ } } catch {}
            }
        }
        $image = Join-Path $target ('slide_{0:00}.png' -f $slide.SlideIndex)
        $slide.Export($image, 'PNG', 1600, 900)
        $pages += [ordered]@{ slide=[int]$slide.SlideIndex; charts=$charts; tables=$tables; mathtype=$native; text_shapes=$texts; image=[System.IO.Path]::GetFileName($image) }
    }
    # SaveAs PDF avoids optional-argument COM marshaling differences in PS 5.1.
    $deck.SaveAs((Join-Path $target 'briefing.pdf'), 32)
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $sourceHash) { throw 'Source file changed during the test.' }
    $result = [ordered]@{
        status='native_roundtrip_completed_visual_review_pending'
        office_version=[string]$ppt.Version
        source_sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
        output_sha256=(Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant()
        slide_count=[int]$deck.Slides.Count
        width_pt=[double]$deck.PageSetup.SlideWidth
        height_pt=[double]$deck.PageSetup.SlideHeight
        slides=$pages
    }
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $target 'ppt_roundtrip.json') -Encoding UTF8
    Write-Output ('PowerPoint save/reopen/export completed: {0} slides; visual review pending.' -f $deck.Slides.Count)
}
finally {
    if ($null -ne $deck) { $deck.Close() }
    if ($initial -eq 0 -and $ppt.Presentations.Count -eq 0) { $ppt.Quit() }
}
