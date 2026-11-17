$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" format-check
exit $LASTEXITCODE
