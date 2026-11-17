$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" down
exit $LASTEXITCODE
