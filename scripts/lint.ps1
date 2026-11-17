$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" lint
exit $LASTEXITCODE
