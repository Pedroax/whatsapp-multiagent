@echo off
echo ========================================
echo    ALICE MULTIAGENTE - LC BATERIAS
echo    Iniciando Sistema Completo
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado! Instale Python 3.9+
    pause
    exit /b 1
)

REM Verificar se Node está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Node.js nao encontrado! Instale Node.js
    pause
    exit /b 1
)

echo [1/4] Verificando dependencias Python...
pip install -r requirements.txt --quiet

echo [2/4] Verificando dependencias Frontend...
cd frontend-multiagente
call npm install --silent
cd ..

echo [3/4] Iniciando Backend (porta 8000)...
start "Alice Backend" cmd /k "python main.py"
timeout /t 5 /nobreak >nul

echo [4/4] Iniciando Frontend (porta 5174)...
cd frontend-multiagente
start "Alice Frontend" cmd /k "npm run dev"
cd ..

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo    SISTEMA INICIADO COM SUCESSO!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5174
echo.
echo Credenciais de teste:
echo Email: admin@lcbaterias.com
echo Senha: admin123
echo.
echo Pressione Ctrl+C nas janelas abertas para parar os servidores
echo.
pause
