"""Script para criar tabela chat_sessions no Supabase"""
from supabase import create_client
from config import settings

# SQL para criar tabela
SQL_CREATE_TABLE = """
-- Tabela de sessões de chat
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone TEXT UNIQUE NOT NULL,
  state JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_message_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_phone ON chat_sessions(phone);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated ON chat_sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_expires ON chat_sessions(expires_at) WHERE expires_at IS NOT NULL;

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_chat_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  NEW.last_message_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_chat_session_timestamp();

-- Função para limpar sessões expiradas
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM chat_sessions
  WHERE expires_at IS NOT NULL
    AND expires_at < NOW();

  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
"""

def main():
    print("Conectando ao Supabase...")
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)

    print("Executando SQL para criar tabela chat_sessions...")

    # Nota: O Supabase Python client não suporta execução direta de SQL complexo
    # Você precisa executar este SQL no SQL Editor do Supabase Dashboard
    # URL: https://iexwyilovmxllfgggbvp.supabase.co/project/_/sql

    print("\n" + "="*70)
    print("IMPORTANTE: Execute o SQL abaixo no Supabase SQL Editor:")
    print("URL: https://iexwyilovmxllfgggbvp.supabase.co/project/_/sql")
    print("="*70)
    print(SQL_CREATE_TABLE)
    print("="*70)

    # Verifica se a tabela existe
    try:
        result = supabase.table("chat_sessions").select("count", count="exact").limit(0).execute()
        print("\nTabela 'chat_sessions' ja existe!")
        print(f"Total de registros: {result.count}")
    except Exception as e:
        print(f"\nTabela 'chat_sessions' ainda nao existe.")
        print("Execute o SQL acima no Supabase Dashboard.")

if __name__ == "__main__":
    main()
