#!/bin/bash

echo "Parando servidores Alice..."

if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Parando Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "Parando Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
fi

echo "Servidores parados!"
