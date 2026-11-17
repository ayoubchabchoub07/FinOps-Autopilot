$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" test
exit $LASTEXITCODE
