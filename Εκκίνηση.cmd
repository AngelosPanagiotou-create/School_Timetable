@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Ωρολόγιο - εκκίνηση
cd /d "%~dp0"

rem ---- 1. ψάχνει Python 3: py launcher, python στο PATH, συνηθισμένοι φάκελοι
set "PY="
set "TRY=py -3" & call :try
if not defined PY (set "TRY=python" & call :try)
for %%V in (314 313 312 311 310) do if not defined PY if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (set TRY="%LocalAppData%\Programs\Python\Python%%V\python.exe"& call :try)
for %%V in (314 313 312 311 310) do if not defined PY if exist "%ProgramFiles%\Python%%V\python.exe" (set TRY="%ProgramFiles%\Python%%V\python.exe"& call :try)
if defined PY goto run

rem ---- 2. δεν υπάρχει: εγκατάσταση Python 3.12 μόνο για αυτόν τον χρήστη (χωρίς κωδικό διαχειριστή)
echo.
echo  ===========================================================
echo   Ωρολόγιο: δεν βρέθηκε Python σε αυτόν τον υπολογιστή.
echo.
echo   Η Python είναι ΥΠΟΧΡΕΩΤΙΚΗ για να τρέξει η εφαρμογή.
echo   Μπορεί να εγκατασταθεί τώρα αυτόματα από το python.org
echo   (περίπου 25 MB, 1-3 λεπτά, χρειάζεται internet,
echo   χωρίς κωδικό διαχειριστή).
echo  ===========================================================
echo.
choice /c YN /n /m "  Να εγκατασταθεί τώρα η Python; [Y = Ναι / N = Όχι]: "
if errorlevel 2 goto declined
echo.
echo  Λήψη Python, περίμενε...
set "SETUP=%TEMP%\python-3.12.10-amd64.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%SETUP%'"
if exist "%SETUP%" goto install
echo  Η λήψη απέτυχε. Δοκιμή με winget...
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
goto after
:install
echo  Εγκατάσταση Python, περίμενε...
start "" /wait "%SETUP%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0 Include_doc=0
del "%SETUP%" >nul 2>&1
:after
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (set TRY="%LocalAppData%\Programs\Python\Python312\python.exe"& call :try)
if not defined PY (set "TRY=py -3" & call :try)
if defined PY goto installed
echo.
echo  Δεν ολοκληρώθηκε η εγκατάσταση της Python.
echo  Κατέβασέ τη από https://www.python.org/downloads/windows/
echo  και τσέκαρε «Add python.exe to PATH». Μετά ξαναπάτα αυτό το αρχείο.
echo.
pause
exit /b 1
:installed
echo  Η Python εγκαταστάθηκε.
goto run

:declined
echo.
echo  Χωρίς Python η εφαρμογή δεν μπορεί να ανοίξει.
echo  - Για να την εγκαταστήσεις αργότερα: ξαναπάτα αυτό το αρχείο,
echo    ή κατέβασέ τη από https://www.python.org/downloads/windows/
echo    (τσέκαρε «Add python.exe to PATH»).
echo.
pause
exit /b 1

:run
rem ---- 3. ανοίγει την εφαρμογή (την πρώτη φορά εγκαθιστά μόνη της PySide6 και OR-Tools)
set "PYW="
for /f "usebackq delims=" %%W in (`call %PY% -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"`) do set "PYW=%%W"
if defined PYW if exist "%PYW%" (start "" "%PYW%" "%~dp0Ωρολόγιο.pyw" & exit /b 0)
start "" %PY% "%~dp0Ωρολόγιο.pyw"
exit /b 0

:try
rem κρατά την πρώτη Python που δουλεύει (όχι το «ψεύτικο» python του Microsoft Store)
set "OUT="
for /f "usebackq delims=" %%O in (`call %TRY% -c "import sys;print(sys.version_info[0])" 2^>nul`) do set "OUT=%%O"
if "%OUT%"=="3" set PY=%TRY%
exit /b 0
