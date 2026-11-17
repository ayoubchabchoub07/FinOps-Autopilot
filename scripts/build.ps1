$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" build
exit $LASTEXITCODE
