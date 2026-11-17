$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" typecheck
exit $LASTEXITCODE
