import React, { useState, useEffect } from 'react';
import { Check, X, Edit3, Clock, User, MessageSquare, Bot, Send } from 'lucide-react';

interface MensagemPendente {
  id: string;
  lead_nome: string;
  lead_telefone: string;
  mensagem_recebida: string;
  resposta_ia: string;
  confianca_ia: number;
  intencao_detectada: string;
  created_at: string;
  tempo_restante: string;
}

interface ApprovalQueueProps {
  empresaId: string;
}

export const ApprovalQueue: React.FC<ApprovalQueueProps> = ({ empresaId }) => {
  const [mensagens, setMensagens] = useState<MensagemPendente[]>([]);
  const [loading, setLoading] = useState(true);
  const [mensagemEditando, setMensagemEditando] = useState<string | null>(null);
  const [textoEditado, setTextoEditado] = useState<string>('');
  const [processando, setProcessando] = useState<string | null>(null);

  useEffect(() => {
    carregarFila();
    const interval = setInterval(carregarFila, 5000); // Atualiza a cada 5s
    return () => clearInterval(interval);
  }, [empresaId]);

  const carregarFila = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/ia-control/fila-aprovacao/${empresaId}`);
      const data = await response.json();
      if (data.success) {
        setMensagens(data.mensagens);
      }
    } catch (error) {
      console.error('Erro ao carregar fila:', error);
    } finally {
      setLoading(false);
    }
  };

  const aprovarMensagem = async (mensagemId: string, textoFinal?: string) => {
    setProcessando(mensagemId);
    try {
      const response = await fetch('${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/ia-control/aprovar-mensagem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensagem_id: mensagemId,
          usuario_id: 'usuario-temp', // TODO: pegar do contexto de autenticação
          texto_editado: textoFinal
        })
      });

      const data = await response.json();
      if (data.success) {
        // TODO: Enviar mensagem via WhatsApp aqui
        console.log('Enviar via WhatsApp:', data.texto_final, 'para', data.lead_telefone);

        // Remover da fila
        setMensagens(prev => prev.filter(m => m.id !== mensagemId));
        setMensagemEditando(null);
        setTextoEditado('');
      }
    } catch (error) {
      console.error('Erro ao aprovar:', error);
    } finally {
      setProcessando(null);
    }
  };

  const recusarMensagem = async (mensagemId: string) => {
    setProcessando(mensagemId);
    try {
      const response = await fetch('${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/ia-control/recusar-mensagem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensagem_id: mensagemId,
          usuario_id: 'usuario-temp',
          motivo: 'Recusado pelo operador'
        })
      });

      const data = await response.json();
      if (data.success) {
        setMensagens(prev => prev.filter(m => m.id !== mensagemId));
      }
    } catch (error) {
      console.error('Erro ao recusar:', error);
    } finally {
      setProcessando(null);
    }
  };

  const iniciarEdicao = (mensagem: MensagemPendente) => {
    setMensagemEditando(mensagem.id);
    setTextoEditado(mensagem.resposta_ia);
  };

  const cancelarEdicao = () => {
    setMensagemEditando(null);
    setTextoEditado('');
  };

  const formatarTempo = (created_at: string) => {
    const diff = Date.now() - new Date(created_at).getTime();
    const minutos = Math.floor(diff / 60000);
    if (minutos < 1) return 'Agora';
    if (minutos < 60) return `${minutos}min atrás`;
    const horas = Math.floor(minutos / 60);
    return `${horas}h atrás`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Fila de Aprovação
          </h3>
          <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
            {mensagens.length} pendente{mensagens.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
        {mensagens.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Bot className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="font-medium">Nenhuma mensagem pendente</p>
            <p className="text-sm">Quando a IA gerar respostas, elas aparecerão aqui para aprovação</p>
          </div>
        ) : (
          mensagens.map((mensagem) => (
            <div key={mensagem.id} className="p-4 hover:bg-gray-50 transition-colors">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{mensagem.lead_nome}</div>
                    <div className="text-xs text-gray-500 flex items-center gap-2">
                      <span>{mensagem.lead_telefone}</span>
                      <span>•</span>
                      <Clock className="w-3 h-3" />
                      <span>{formatarTempo(mensagem.created_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Confiança da IA */}
                {mensagem.confianca_ia && (
                  <div className="text-xs">
                    <span className="text-gray-500">Confiança: </span>
                    <span className={`font-semibold ${
                      mensagem.confianca_ia >= 0.8 ? 'text-green-600' :
                      mensagem.confianca_ia >= 0.5 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {(mensagem.confianca_ia * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Mensagem do Lead */}
              <div className="mb-3">
                <div className="text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
                  <User className="w-3 h-3" />
                  Mensagem do cliente:
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700">
                  {mensagem.mensagem_recebida}
                </div>
              </div>

              {/* Resposta da IA */}
              <div className="mb-3">
                <div className="text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
                  <Bot className="w-3 h-3" />
                  Resposta sugerida pela IA:
                  {mensagem.intencao_detectada && (
                    <span className="ml-2 bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs">
                      {mensagem.intencao_detectada}
                    </span>
                  )}
                </div>

                {mensagemEditando === mensagem.id ? (
                  <textarea
                    value={textoEditado}
                    onChange={(e) => setTextoEditado(e.target.value)}
                    className="w-full bg-white border border-blue-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                  />
                ) : (
                  <div className="bg-blue-50 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap">
                    {mensagem.resposta_ia}
                  </div>
                )}
              </div>

              {/* Ações */}
              <div className="flex gap-2">
                {mensagemEditando === mensagem.id ? (
                  <>
                    <button
                      onClick={() => aprovarMensagem(mensagem.id, textoEditado)}
                      disabled={processando === mensagem.id}
                      className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <Send className="w-4 h-4" />
                      Enviar Editada
                    </button>
                    <button
                      onClick={cancelarEdicao}
                      disabled={processando === mensagem.id}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      Cancelar
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => aprovarMensagem(mensagem.id)}
                      disabled={processando === mensagem.id}
                      className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <Check className="w-4 h-4" />
                      Aprovar e Enviar
                    </button>
                    <button
                      onClick={() => iniciarEdicao(mensagem)}
                      disabled={processando === mensagem.id}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2 disabled:opacity-50"
                    >
                      <Edit3 className="w-4 h-4" />
                      Editar
                    </button>
                    <button
                      onClick={() => recusarMensagem(mensagem.id)}
                      disabled={processando === mensagem.id}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors flex items-center gap-2 disabled:opacity-50"
                    >
                      <X className="w-4 h-4" />
                      Recusar
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
