@echo off

IF EXIST automation_web.exe (
    echo Compiled
    IF EXIST out (
        echo Setup okay
    ) ELSE (
        mkdir out
    )
    automation_web.exe --web
) ELSE (
    echo Script
    call venv/Scripts/activate.bat
    python automation_web.py --web
)

pause
