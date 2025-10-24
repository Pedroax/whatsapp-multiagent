#!/bin/bash

echo "========================================"
echo "   ALICE MULTIAGENTE - LC BATERIAS"
echo "   Iniciando Sistema Completo"
echo "========================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERRO: Python3 não encontrado! Instale Python 3.9+${NC}"
    exit 1
fi

# Verificar se Node está instalado
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERRO: Node.js não encontrado! Instale Node.js${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/4] Verificando dependências Python...${NC}"
pip3 install -r requirements.txt --quiet

echo -e "${YELLOW}[2/4] Verificando dependências Frontend...${NC}"
cd frontend-multiagente
npm install --silent
cd ..

echo -e "${YELLOW}[3/4] Iniciando Backend (porta 8000)...${NC}"
python3 main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 5

echo -e "${YELLOW}[4/4] Iniciando Frontend (porta 5174)...${NC}"
cd frontend-multiagente
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

sleep 3

echo ""
echo "========================================"
echo -e "   ${GREEN}SISTEMA INICIADO COM SUCESSO!${NC}"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5174"
echo ""
echo "Credenciais de teste:"
echo "Email: admin@lcbaterias.com"
echo "Senha: admin123"
echo ""
echo "PIDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "Para parar os servidores:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""

# Salvar PIDs para fácil parada
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "PIDs salvos em .backend.pid e .frontend.pid"
echo ""
