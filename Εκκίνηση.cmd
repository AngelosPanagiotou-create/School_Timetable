@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
rem ---- γλώσσα: ό,τι διάλεξε ο χρήστης στην εφαρμογή (Έγγραφα\Ωρολόγιο\lang.txt), αλλιώς η γλώσσα των Windows
set "L="
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "$f=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Ωρολόγιο\lang.txt'; if(Test-Path $f){(Get-Content $f -Raw).Trim()}else{(Get-UICulture).TwoLetterISOLanguageName}" 2^>nul`) do set "L=%%A"
if not "%L%"=="el" if not "%L%"=="fr" if not "%L%"=="de" if not "%L%"=="es" set "L=en"
goto lang_%L%
:lang_el
set "M_T=Ωρολόγιο - εκκίνηση"
set "M_A1=Ωρολόγιο: δεν βρέθηκε Python σε αυτόν τον υπολογιστή."
set "M_A2=Η Python είναι ΥΠΟΧΡΕΩΤΙΚΗ για να τρέξει η εφαρμογή."
set "M_A3=Μπορεί να εγκατασταθεί τώρα αυτόματα από το python.org"
set "M_A4=(περίπου 25 MB, 1-3 λεπτά, χρειάζεται internet,"
set "M_A5=χωρίς κωδικό διαχειριστή)."
set "M_Q=  Να εγκατασταθεί τώρα η Python; [Y = Ναι / N = Όχι]: "
set "M_D=  Λήψη Python, περίμενε..."
set "M_DF=  Η λήψη απέτυχε. Δοκιμή με winget..."
set "M_I=  Εγκατάσταση Python, περίμενε..."
set "M_F1=  Δεν ολοκληρώθηκε η εγκατάσταση της Python."
set "M_F2=  Κατέβασέ τη από https://www.python.org/downloads/windows/"
set "M_F3=  και τσέκαρε «Add python.exe to PATH». Μετά ξαναπάτα αυτό το αρχείο."
set "M_OK=  Η Python εγκαταστάθηκε."
set "M_N1=  Χωρίς Python η εφαρμογή δεν μπορεί να ανοίξει."
set "M_N2=  - Για να την εγκαταστήσεις αργότερα: ξαναπάτα αυτό το αρχείο,"
set "M_N3=    ή κατέβασέ τη από https://www.python.org/downloads/windows/"
set "M_N4=    (τσέκαρε «Add python.exe to PATH»)."
goto lang_done
:lang_en
set "M_T=Timetable - start"
set "M_A1=Timetable: Python was not found on this computer."
set "M_A2=Python is REQUIRED to run the application."
set "M_A3=It can be installed automatically now from python.org"
set "M_A4=(about 25 MB, 1-3 minutes, internet required,"
set "M_A5=no administrator password)."
set "M_Q=  Install Python now? [Y = Yes / N = No]: "
set "M_D=  Downloading Python, please wait..."
set "M_DF=  Download failed. Trying winget..."
set "M_I=  Installing Python, please wait..."
set "M_F1=  The Python installation did not complete."
set "M_F2=  Download it from https://www.python.org/downloads/windows/"
set "M_F3=  and tick "Add python.exe to PATH". Then run this file again."
set "M_OK=  Python was installed."
set "M_N1=  Without Python the application cannot open."
set "M_N2=  - To install it later: run this file again,"
set "M_N3=    or download it from https://www.python.org/downloads/windows/"
set "M_N4=    (tick "Add python.exe to PATH")."
goto lang_done
:lang_fr
set "M_T=Emploi du temps - démarrage"
set "M_A1=Emploi du temps : Python est introuvable sur cet ordinateur."
set "M_A2=Python est OBLIGATOIRE pour lancer l’application."
set "M_A3=Elle peut être installée automatiquement depuis python.org"
set "M_A4=(environ 25 Mo, 1-3 minutes, internet nécessaire,"
set "M_A5=sans mot de passe administrateur)."
set "M_Q=  Installer Python maintenant ? [Y = Oui / N = Non] : "
set "M_D=  Téléchargement de Python, patiente..."
set "M_DF=  Échec du téléchargement. Essai avec winget..."
set "M_I=  Installation de Python, patiente..."
set "M_F1=  L’installation de Python n’a pas abouti."
set "M_F2=  Télécharge-la sur https://www.python.org/downloads/windows/"
set "M_F3=  et coche « Add python.exe to PATH ». Puis relance ce fichier."
set "M_OK=  Python est installé."
set "M_N1=  Sans Python, l’application ne peut pas s’ouvrir."
set "M_N2=  - Pour l’installer plus tard : relance ce fichier,"
set "M_N3=    ou télécharge-la sur https://www.python.org/downloads/windows/"
set "M_N4=    (coche « Add python.exe to PATH »)."
goto lang_done
:lang_de
set "M_T=Stundenplan - Start"
set "M_A1=Stundenplan: Python wurde auf diesem Computer nicht gefunden."
set "M_A2=Python ist für die Anwendung ERFORDERLICH."
set "M_A3=Es kann jetzt automatisch von python.org installiert werden"
set "M_A4=(ca. 25 MB, 1-3 Minuten, Internet erforderlich,"
set "M_A5=ohne Administratorkennwort)."
set "M_Q=  Python jetzt installieren? [Y = Ja / N = Nein]: "
set "M_D=  Python wird heruntergeladen, bitte warten..."
set "M_DF=  Download fehlgeschlagen. Versuch mit winget..."
set "M_I=  Python wird installiert, bitte warten..."
set "M_F1=  Die Python-Installation wurde nicht abgeschlossen."
set "M_F2=  Lade es von https://www.python.org/downloads/windows/ herunter"
set "M_F3=  und aktiviere „Add python.exe to PATH“. Dann starte diese Datei erneut."
set "M_OK=  Python wurde installiert."
set "M_N1=  Ohne Python kann die Anwendung nicht starten."
set "M_N2=  - Zum späteren Installieren: diese Datei erneut starten,"
set "M_N3=    oder von https://www.python.org/downloads/windows/ herunterladen"
set "M_N4=    („Add python.exe to PATH“ aktivieren)."
goto lang_done
:lang_es
set "M_T=Horario - inicio"
set "M_A1=Horario: no se encontró Python en este ordenador."
set "M_A2=Python es OBLIGATORIO para ejecutar la aplicación."
set "M_A3=Puede instalarse ahora automáticamente desde python.org"
set "M_A4=(unos 25 MB, 1-3 minutos, requiere internet,"
set "M_A5=sin contraseña de administrador)."
set "M_Q=  ¿Instalar Python ahora? [Y = Sí / N = No]: "
set "M_D=  Descargando Python, espera..."
set "M_DF=  La descarga falló. Probando con winget..."
set "M_I=  Instalando Python, espera..."
set "M_F1=  La instalación de Python no se completó."
set "M_F2=  Descárgalo de https://www.python.org/downloads/windows/"
set "M_F3=  y marca «Add python.exe to PATH». Luego vuelve a ejecutar este archivo."
set "M_OK=  Python se instaló."
set "M_N1=  Sin Python la aplicación no puede abrirse."
set "M_N2=  - Para instalarlo más tarde: vuelve a ejecutar este archivo,"
set "M_N3=    o descárgalo de https://www.python.org/downloads/windows/"
set "M_N4=    (marca «Add python.exe to PATH»)."
goto lang_done
:lang_done
title %M_T%

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
echo   %M_A1%
echo.
echo   %M_A2%
echo   %M_A3%
echo   %M_A4%
echo   %M_A5%
echo  ===========================================================
echo.
choice /c YN /n /m "%M_Q%"
if errorlevel 2 goto declined
echo.
echo %M_D%
set "SETUP=%TEMP%\python-3.12.10-amd64.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%SETUP%'"
if exist "%SETUP%" goto install
echo %M_DF%
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
goto after
:install
echo %M_I%
start "" /wait "%SETUP%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0 Include_doc=0
del "%SETUP%" >nul 2>&1
:after
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (set TRY="%LocalAppData%\Programs\Python\Python312\python.exe"& call :try)
if not defined PY (set "TRY=py -3" & call :try)
if defined PY goto installed
echo.
echo %M_F1%
echo %M_F2%
echo %M_F3%
echo.
pause
exit /b 1
:installed
echo %M_OK%
goto run

:declined
echo.
echo %M_N1%
echo %M_N2%
echo %M_N3%
echo %M_N4%
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
