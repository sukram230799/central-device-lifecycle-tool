@echo off

echo Check Python
python --version


echo Setup virtualenv
python -m virtualenv venv

echo Activate virtualenv
call venv/Scripts/activate

echo Install Packages
python -m pip install -r requirements.txt

echo.
echo Done
                                 


pause
