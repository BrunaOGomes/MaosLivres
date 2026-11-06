@echo off
chcp 65001 >nul
rem ============================================================
rem MaosLivres - inicia o controle do mouse e teclado pela webcam
rem ============================================================
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] O ambiente virtual "venv" nao foi encontrado.
    echo Crie com:  python -m venv venv
    echo E instale:  venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"

echo.
echo Iniciando o MaosLivres...
echo Olhe para a tela com os olhos abertos durante a calibracao (3 segundos).
echo Para sair: ESC na janela da camera, ou Ctrl+C aqui.
echo.

python controle_sem_toque.py
set CODIGO=%ERRORLEVEL%

if not "%CODIGO%"=="0" (
    echo.
    echo [ERRO] O programa terminou com codigo %CODIGO%.
    pause
)

exit /b %CODIGO%
