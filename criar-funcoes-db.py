#!/usr/bin/env python3
"""
Cria funções SQL necessárias no Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ler script SQL
with open("criar-funcao-aprovar.sql", "r", encoding="utf-8") as f:
    sql = f.read()

print("🔧 Criando funções SQL no Supabase...")

try:
    # Executar SQL via RPC (precisa criar função temporária)
    # Como não podemos executar SQL direto, vamos fazer via API REST
    import requests

    # Endpoint do Supabase para executar SQL
    db_url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    # Dividir em múltiplos comandos
    comandos = sql.split("-- ====")

    for i, cmd in enumerate(comandos):
        cmd = cmd.strip()
        if not cmd or cmd.startswith("="):
            continue

        print(f"\n📝 Executando comando {i+1}...")
        print(f"   {cmd[:80]}...")

        # Tentar via supabase-py
        # Como não há método direto, vamos usar psycopg2
        break

    # Melhor solução: usar psycopg2
    import psycopg2

    # Connection string do Supabase
    # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    project_ref = SUPABASE_URL.split("//")[1].split(".")[0]

    print(f"\n⚠️  Para executar SQL no Supabase, você precisa:")
    print(f"1. Ir para: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}/editor")
    print(f"2. Ir para SQL Editor")
    print(f"3. Colar o conteúdo de 'criar-funcao-aprovar.sql'")
    print(f"4. Clicar em 'Run'")
    print(f"\nOu use este comando psql:")
    print(f"psql postgresql://postgres:[YOUR_PASSWORD]@db.{project_ref}.supabase.co:5432/postgres < criar-funcao-aprovar.sql")

except Exception as e:
    print(f"❌ Erro: {e}")
    print("\n💡 Solução: Execute o SQL manualmente no Supabase Dashboard")
    print(f"   URL: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}/editor")
