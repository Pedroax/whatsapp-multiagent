# 🚀 Deploy do Sistema de Pipeline - Instruções

## 📋 Resumo das Alterações

Sistema completo de **Pipeline de Leads** implementado com 10 estágios customizáveis.

---

## 🗄️ 1. BANCO DE DADOS (OBRIGATÓRIO)

### Execute no Supabase SQL Editor:

```sql
-- Adicionar coluna estagio_pipeline
ALTER TABLE paula_conversas
ADD COLUMN IF NOT EXISTS estagio_pipeline TEXT DEFAULT 'novo';

-- Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_paula_conversas_estagio_pipeline
ON paula_conversas(estagio_pipeline);

-- Comentário da coluna
COMMENT ON COLUMN paula_conversas.estagio_pipeline IS 'Estágio do lead no pipeline de vendas/atendimento';
```

**✅ Verificar se funcionou:**
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'paula_conversas'
AND column_name = 'estagio_pipeline';
```

---

## 📦 2. BACKEND (main.py)

### Alterações principais:

1. **Novo endpoint** `/api/conversas/{phone}/pipeline` (linhas 846-910)
   - PUT para atualizar estágio do pipeline
   - Validação de 10 estágios válidos

2. **Endpoint `/api/leads` atualizado** (linhas 913-1027)
   - Novo parâmetro `pipeline` para filtro
   - Campo `estagio_pipeline` no retorno

---

## 🎨 3. FRONTEND

### Novos arquivos:
- `frontend/src/components/PipelineStage.tsx` - Componente de Pipeline com 10 estágios

### Arquivos modificados:
- `frontend/src/components/ContactInfo.tsx` - Integração do Pipeline (linhas 8, 22-23, 35-40, 335-343)
- `frontend/src/components/LeadsManager.tsx` - Filtro e badges de Pipeline (linhas 7, 15, 30-35, 47, 196-213, 255-271)
- `frontend/src/types/index.ts` - Tipo `estagio_pipeline` (linha 47)
- `frontend/src/hooks/useConversas.ts` - Campo `estagio_pipeline` (linha 89)

---

## 🚀 4. DEPLOY NA VPS

### Opção A: Deploy Automático via Git

```bash
# 1. Conectar na VPS
ssh paulo@5.161.186.51

# 2. Ir para pasta do projeto
cd paula

# 3. Fazer backup
cp main.py main.py.backup

# 4. Atualizar código
git pull origin main

# 5. Atualizar frontend
cd frontend
npm run build
cd ..

# 6. Reiniciar serviços
sudo systemctl restart paula-backend
sudo systemctl restart nginx
```

### Opção B: Deploy Manual (se Git não funcionar)

1. **Fazer upload dos arquivos via SFTP/SCP:**
   - `main.py`
   - `frontend/dist/` (pasta completa)
   - `frontend/src/components/PipelineStage.tsx`
   - `frontend/src/components/ContactInfo.tsx`
   - `frontend/src/components/LeadsManager.tsx`
   - `frontend/src/types/index.ts`
   - `frontend/src/hooks/useConversas.ts`

2. **Conectar na VPS e reiniciar:**
```bash
ssh paulo@5.161.186.51
cd paula
sudo systemctl restart paula-backend
sudo systemctl restart nginx
```

---

## 🎯 5. ESTÁGIOS DO PIPELINE

| Estágio | Label | Cor | Descrição |
|---------|-------|-----|-----------|
| `novo` | Novo | Azul | Lead novo que acabou de chegar |
| `em_contato` | Em Contato | Verde | Primeira interação acontecendo |
| `aguardando_resposta` | Aguardando Resposta | Amarelo | Lead não respondeu ainda |
| `interessado` | Interessado | Roxo | Demonstrou interesse |
| `agendamento_solicitado` | Agendamento Solicitado | Laranja | Pediu para agendar |
| `agendado` | Agendado | Verde Escuro | Consulta já marcada |
| `compareceu` | Compareceu | Azul Claro | Passou na consulta |
| `nao_compareceu` | Não Compareceu | Vermelho Claro | Faltou à consulta |
| `convertido` | Convertido | Verde | Fechou tratamento/procedimento |
| `perdido` | Perdido | Vermelho | Desistiu/não tem interesse |

---

## ✅ 6. TESTAR APÓS DEPLOY

1. **Abrir Gerenciamento de Leads:**
   - Verificar se aparece filtro "Todos os estágios"
   - Verificar se badges de pipeline aparecem nos leads

2. **Abrir uma conversa:**
   - Verificar painel ContactInfo (lado direito)
   - Verificar seção "Estágio do Pipeline"
   - Testar alterar o estágio

3. **Filtrar por estágio:**
   - Selecionar estágio no dropdown
   - Verificar se filtra corretamente

---

## 🔥 IMPORTANTE

- ✅ SQL já foi executado no Supabase (confirmado)
- ✅ Frontend já foi buildado localmente
- ✅ Todos os arquivos estão prontos
- ⚠️ **Fazer backup do main.py antes de substituir**
- ⚠️ **Testar após deploy para garantir funcionamento**

---

## 📞 SUPORTE

Se algo der errado:
1. Verificar logs: `sudo journalctl -u paula-backend -f`
2. Verificar Nginx: `sudo nginx -t`
3. Verificar se coluna existe no banco (SQL acima)

---

**Data da implementação:** 2025-11-17
**Versão:** 1.0.0 - Sistema de Pipeline de Leads
