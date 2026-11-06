@echo off
chcp 65001 >nul
rem ============================================================
rem MaosLivres - teste de validacao (mede acertos e tempo)
rem Rode o iniciar.bat em outra janela antes, para testar no modo "rosto".
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
echo Teste de validacao do MaosLivres.
echo Os resultados sao gravados em resultados_validacao.csv
echo.

python teste_validacao.py
set CODIGO=%ERRORLEVEL%

if not "%CODIGO%"=="0" (
    echo.
    echo [ERRO] O teste terminou com codigo %CODIGO%.
    pause
)

exit /b %CODIGO%
