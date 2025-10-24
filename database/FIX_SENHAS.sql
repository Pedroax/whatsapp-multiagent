-- Atualizar senhas dos usuários para "admin123" com hash bcrypt correto

UPDATE usuarios
SET senha_hash = '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2'
WHERE email IN (
    'admin@lcbaterias.com',
    'vendas@lcbaterias.com',
    'financeiro@lcbaterias.com',
    'assistencia@lcbaterias.com',
    'suporte@lcbaterias.com'
);

-- Verificar usuários atualizados
SELECT id, email, nome_completo, role, departamento_slug, status
FROM usuarios
WHERE email IN (
    'admin@lcbaterias.com',
    'vendas@lcbaterias.com',
    'financeiro@lcbaterias.com',
    'assistencia@lcbaterias.com',
    'suporte@lcbaterias.com'
);
