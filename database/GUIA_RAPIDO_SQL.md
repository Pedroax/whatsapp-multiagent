# 🚀 GUIA RÁPIDO: Como Executar SQL no Supabase

## ✅ PASSO A PASSO (3 minutos)

### 1️⃣ Acesse o Supabase
- Vá em: https://supabase.com/dashboard
- Faça login com sua conta

### 2️⃣ Selecione seu Projeto
- URL do seu projeto: `https://iexwyilovmxllfgggbvp.supabase.co`
- Clique no projeto da Alice

### 3️⃣ Abra o SQL Editor
```
No menu lateral esquerdo:
Database → SQL Editor
```

### 4️⃣ Crie Nova Query
```
Clique em: "+ New query"
```

### 5️⃣ Copie o SQL
- Abra o arquivo: `database/COPIE_ESTE_SQL.sql`
- Selecione TUDO (Ctrl+A)
- Copie (Ctrl+C)

### 6️⃣ Cole no SQL Editor
- Cole o SQL copiado na área de texto do Supabase
- O código já está 100% pronto para usar

### 7️⃣ Execute
```
Clique no botão verde: "RUN" (Ctrl+Enter)
```

### 8️⃣ Verificar Sucesso
Você deve ver mensagens como:
```
✅ CREATE TABLE
✅ CREATE INDEX
✅ ALTER PUBLICATION
✅ Success. No rows returned
```

### 9️⃣ Confirmar Tabelas Criadas
```
No menu lateral:
Database → Tables

Você deve ver 3 novas tabelas:
✅ mensagens_pendentes
✅ agendamentos_ia
✅ config_ia
```

---

## 🎯 PRONTO!

Agora instale as dependências Python:
```bash
pip install supabase==2.12.0 pytz==2025.1
```

E reinicie o backend:
```bash
# Pare o processo atual (Ctrl+C)
python main.py
```

---

## ❓ Problemas Comuns

### "permission denied"
- Use a aba "SQL Editor" (não tente criar via UI)
- Você tem permissão total via SQL

### "table already exists"
- Normal! O script usa `CREATE TABLE IF NOT EXISTS`
- Pode executar de novo sem problema

### "relation does not exist"
- Execute TODO o arquivo de uma vez
- Não execute linha por linha

---

## 📸 Visual Guide

**Menu onde clicar:**
```
Supabase Dashboard
├─ Database (ícone de banco de dados)
│  └─ SQL Editor (ícone de código)
│     └─ + New query
│        └─ [Cole o SQL aqui]
│           └─ Botão RUN (verde, canto superior direito)
```

**Onde verificar:**
```
Supabase Dashboard
├─ Database
│  └─ Tables (ícone de tabela)
│     ✅ agendamentos_ia
│     ✅ config_ia
│     ✅ mensagens_pendentes
```
