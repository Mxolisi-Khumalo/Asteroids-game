@echo off
REM Launch Asteroids (Space Rocks). Run from the repo root.
cd /d "%~dp0"
if not exist venv (
    py -m venv venv
    venv\Scripts\python.exe -m pip install -r requirements.txt
)
venv\Scripts\python.exe space_rocks\__main__.py
