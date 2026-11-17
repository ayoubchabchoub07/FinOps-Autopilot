$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tasks.py" smoke
exit $LASTEXITCODE
