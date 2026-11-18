param([switch]$CheckOnly, [string]$PythonPath)
$ErrorActionPreference = 'Stop'
$sourceSkill = Join-Path $PSScriptRoot 'toy-demo-roughcut'
if (-not (Test-Path -LiteralPath (Join-Path $sourceSkill 'SKILL.md'))) { throw 'Skill folder is missing. Extract the entire package first.' }
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillsRoot = Join-Path $codexRoot 'skills'
$targetSkill = Join-Path $skillsRoot 'toy-demo-roughcut'
if (-not $CheckOnly) {
    if (Test-Path -LiteralPath $targetSkill) { throw "Already exists; no files were overwritten: $targetSkill" }
    New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
    Copy-Item -LiteralPath $sourceSkill -Destination $targetSkill -Recurse
    Write-Host "Skill files installed: $targetSkill"
}
$pythonExe = $null
$pythonArgs = @()
$candidates = if ($PythonPath) { @($PythonPath) } else { @('python', 'py', 'python3') }
foreach ($candidate in $candidates) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if (-not $command) { continue }
    $candidateArgs = if ($command.Name -match '^py(\.exe)?$') { @('-3') } else { @() }
    try {
        & $command.Source @candidateArgs -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $pythonExe = $command.Source; $pythonArgs = $candidateArgs; break }
    } catch { continue }
}
if (-not $pythonExe) {
    Write-Warning 'Python 3.10+ was not found. Dependencies are NOT verified. Ask Codex to locate/install Python, then rerun with -CheckOnly -PythonPath <python.exe>.'
    exit 1
}
& $pythonExe @pythonArgs (Join-Path $sourceSkill 'scripts/check_environment.py')
$checkResult = $LASTEXITCODE
if (-not $CheckOnly) {
    Write-Host 'On the next Codex turn, ask it to read toy-demo-roughcut/references/first-use.md for the introduction.'
    Write-Host 'Use: $toy-demo-roughcut + full video path + requirements. Reopen Codex only if discovery fails.'
}
if ($checkResult -ne 0) { Write-Warning 'Skill files may be installed, but ordinary SDR use is NOT READY. Resolve the missing items above; nothing was downloaded automatically.' }
exit $checkResult
