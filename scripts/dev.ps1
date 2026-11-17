$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" dev
exit $LASTEXITCODE
