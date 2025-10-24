# 📁 Pasta Onboarding

Esta pasta contém toda a documentação e templates para onboarding de novos clientes distribuidoras de baterias.

---

## 📂 Estrutura

```
onboarding/
├── README.md (este arquivo)
└── clientes/
    └── lc-baterias/          ← Cliente piloto (referência)
        ├── info.md           ← Checklist preenchida
        ├── prompt.txt        ← Prompt final da Alice
        ├── setup.sql         ← SQL executado
        └── testes.md         ← Resultados dos testes
```

---

## 🎯 Como Usar

### Para Onboarding de Novo Cliente:

1. **Copie a pasta template:**
   ```bash
   cp -r clientes/lc-baterias clientes/[nome-novo-cliente]
   ```

2. **Preencha o checklist:**
   - Abra `templates/TEMPLATE_ONBOARDING_CHECKLIST.md`
   - Preencha com informações do novo cliente
   - Salve em `clientes/[nome-novo-cliente]/info.md`

3. **Crie o prompt personalizado:**
   - Abra Claude Code
   - Diga: *"Preciso criar prompt para [EMPRESA], distribuidora de baterias"*
   - Cole o checklist preenchido
   - Salve o prompt gerado em `clientes/[nome-novo-cliente]/prompt.txt`

4. **Configure no banco:**
   - Abra `templates/TEMPLATE_SQL_NOVO_CLIENTE.sql`
   - Substitua os `[PLACEHOLDERS]`
   - Cole o prompt criado
   - Execute no Supabase
   - Salve uma cópia em `clientes/[nome-novo-cliente]/setup.sql`

5. **Teste e documente:**
   - Execute bateria de testes (use `clientes/lc-baterias/testes.md` como guia)
   - Documente resultados em `clientes/[nome-novo-cliente]/testes.md`

---

## 📋 Checklist Rápido

- [ ] Criar pasta do cliente
- [ ] Preencher info.md
- [ ] Gerar prompt.txt com Claude Code
- [ ] Executar setup.sql no Supabase
- [ ] Configurar Evolution API
- [ ] Executar bateria de testes
- [ ] Documentar em testes.md
- [ ] Go-live

---

## 📚 Documentação Relacionada

- **Processo completo:** [docs/ONBOARDING.md](../docs/ONBOARDING.md)
- **Template checklist:** [templates/TEMPLATE_ONBOARDING_CHECKLIST.md](../templates/TEMPLATE_ONBOARDING_CHECKLIST.md)
- **Template SQL:** [templates/TEMPLATE_SQL_NOVO_CLIENTE.sql](../templates/TEMPLATE_SQL_NOVO_CLIENTE.sql)
- **Prompt base:** [templates/PROMPT_BASE_DISTRIBUIDORA.md](../templates/PROMPT_BASE_DISTRIBUIDORA.md)

---

## 🔍 Exemplo de Referência

A pasta `clientes/lc-baterias/` contém um exemplo **completo e real** de onboarding do cliente piloto. Use como referência para entender:

- Como preencher o checklist
- Como estruturar o prompt
- Como escrever o SQL
- Quais testes executar

---

## 📞 Suporte

Se tiver dúvidas durante o onboarding:

1. Consulte o cliente piloto: `clientes/lc-baterias/`
2. Leia o guia completo: `docs/ONBOARDING.md`
3. Abra Claude Code com contexto do projeto
4. Use o prompt base como referência: `templates/PROMPT_BASE_DISTRIBUIDORA.md`

---

**Última atualização:** 2025-10-24
**Mantido por:** Equipe Alice LC
