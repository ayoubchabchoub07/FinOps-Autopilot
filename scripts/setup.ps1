$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" setup
exit $LASTEXITCODE
