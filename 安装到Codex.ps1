$ErrorActionPreference = 'Stop'
$sourceSkill = Join-Path $PSScriptRoot 'toy-demo-roughcut'
if (-not (Test-Path -LiteralPath (Join-Path $sourceSkill 'SKILL.md'))) { throw 'Skill folder is missing. Extract the entire package first.' }
$skillsRoot = Join-Path $env:USERPROFILE '.codex\skills'
$targetSkill = Join-Path $skillsRoot 'toy-demo-roughcut'
if (Test-Path -LiteralPath $targetSkill) { throw "Already exists; no files were overwritten: $targetSkill" }
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
Copy-Item -LiteralPath $sourceSkill -Destination $targetSkill -Recurse
Write-Host "Installed: $targetSkill"
Write-Host 'Available on the next Codex turn; reopen Codex if it is not discovered.'
Write-Host 'Prerequisites: Python 3.10+, ffmpeg/ffprobe, Pillow for contact sheets.'
