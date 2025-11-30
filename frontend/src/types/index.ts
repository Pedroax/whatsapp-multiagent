export interface Usuario {
  id: string
  empresa_id: string
  departamento_id: string
  nome_completo: string
  email: string
  role: 'admin' | 'gerente' | 'agente'
  status: 'online' | 'ausente' | 'ocupado' | 'offline'
  pode_ver_todos_departamentos: boolean
}

export interface Departamento {
  id: string
  empresa_id: string
  nome: string
  slug: string
  cor_primaria: string
  icone: string
  ordem: number
  ativo: boolean
}

export interface Lead {
  id: string
  empresa_id: string
  nome: string
  telefone: string
  email?: string
  avatar_url?: string
  tags: string[]
}

export interface Conversa {
  id: string
  empresa_id: string
  lead_id: string
  lead: Lead
  departamento_id?: string
  departamento?: Departamento
  departamento_slug?: string  // Slug do departamento para filtro
  usuario_atribuido_id?: string
  usuario_atribuido?: Usuario
  status: 'nova' | 'aberta' | 'pendente' | 'resolvida' | 'fechada'
  modo_ia: 'ativo' | 'pausado' | 'desligado' | 'ligado'  // Adicionar 'ligado'
  prioridade: 'baixa' | 'normal' | 'alta' | 'urgente'
  qualificacao?: 'frio' | 'quente' | null  // Qualificação do lead
  estagio_pipeline?: string  // 🎯 Estágio do pipeline (novo, em_contato, agendado, etc)
  tags?: string[]  // Tags da conversa
  nao_lidas: number
  ultima_mensagem?: Mensagem
  created_at: string
  updated_at: string
}

export interface Mensagem {
  id: string
  conversa_id: string
  tipo: 'entrada' | 'saida'
  conteudo: string
  tipo_midia?: 'texto' | 'audio' | 'imagem' | 'video' | 'documento'
  midia_url?: string
  enviado_por_ia: boolean
  enviado_por_usuario_id?: string
  enviado_por_usuario?: Usuario
  departamento_origem?: string // Departamento de onde a mensagem foi enviada (após transferência)
  lida: boolean
  created_at: string
}

export interface ConfigIA {
  id: string
  empresa_id: string
  modo_padrao: 'ativo' | 'atencao' | 'desligado'
  resposta_automatica: boolean
  tempo_espera_antes_responder: number
  usar_agendamento: boolean
  notificar_transferencias: boolean
  notificar_novas_mensagens: boolean
}
