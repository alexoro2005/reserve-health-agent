@echo off
REM Starts Reserve: the API (Python) and the dashboard (Next.js), then opens the browser.
cd /d "%~dp0"
start "Reserve API" cmd /k "call %USERPROFILE%\anaconda3\Scripts\activate.bat && uvicorn api:app --reload"
start "Reserve Dashboard" cmd /k "cd dashboard && npm run dev"
echo Starting Reserve... the dashboard will open in about 15 seconds.
timeout /t 15 >nul
start http://localhost:3000
