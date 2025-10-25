import React, { useState, useEffect } from 'react';
import { Power, AlertCircle, Check, Clock } from 'lucide-react';

interface IAModeControlProps {
  empresaId: string;
}

type ModoIA = 'ligado' | 'atencao' | 'desligado';

export const IAModeControl: React.FC<IAModeControlProps> = ({ empresaId }) => {
  const [modoAtual, setModoAtual] = useState<ModoIA>('atencao');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    carregarModo();
  }, [empresaId]);

  const carregarModo = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "${API_URL}"}/api/ia-control/modo/${empresaId}`);
      const data = await response.json();
      if (data.success) {
        setModoAtual(data.modo);
      }
    } catch (error) {
      console.error('Erro ao carregar modo da IA:', error);
    }
  };

  const alterarModo = async (novoModo: ModoIA) => {
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "${API_URL}"}/api/ia-control/modo/${empresaId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modo: novoModo })
      });

      const data = await response.json();
      if (data.success) {
        setModoAtual(novoModo);
      }
    } catch (error) {
      console.error('Erro ao alterar modo:', error);
    } finally {
      setLoading(false);
    }
  };

  const getModoConfig = (modo: ModoIA) => {
    const configs = {
      ligado: {
        label: 'Ligado',
        icon: '🟢',
        description: 'IA responde automaticamente',
        color: 'green',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        textColor: 'text-green-700'
      },
      atencao: {
        label: 'Atenção',
        icon: '🟡',
        description: 'IA sugere respostas para aprovação',
        color: 'yellow',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        textColor: 'text-yellow-700'
      },
      desligado: {
        label: 'Desligado',
        icon: '🔴',
        description: 'IA não processa mensagens',
        color: 'red',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        textColor: 'text-red-700'
      }
    };
    return configs[modo];
  };

  const config = getModoConfig(modoAtual);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Power className="w-5 h-5" />
          Controle da IA
        </h3>
      </div>

      {/* Status Atual */}
      <div className={`${config.bgColor} ${config.borderColor} border-2 rounded-lg p-4 mb-4`}>
        <div className="flex items-center gap-3">
          <span className="text-3xl">{config.icon}</span>
          <div>
            <div className={`font-semibold ${config.textColor}`}>{config.label}</div>
            <div className="text-sm text-gray-600">{config.description}</div>
          </div>
        </div>
      </div>

      {/* Botões de Controle */}
      <div className="grid grid-cols-3 gap-2">
        {(['ligado', 'atencao', 'desligado'] as ModoIA[]).map((modo) => {
          const modoConfig = getModoConfig(modo);
          const isAtivo = modoAtual === modo;

          return (
            <button
              key={modo}
              onClick={() => alterarModo(modo)}
              disabled={loading || isAtivo}
              className={`
                relative p-3 rounded-lg border-2 transition-all
                ${isAtivo
                  ? `${modoConfig.bgColor} ${modoConfig.borderColor} ${modoConfig.textColor}`
                  : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }
                ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                disabled:cursor-not-allowed
              `}
            >
              <div className="text-center">
                <div className="text-2xl mb-1">{modoConfig.icon}</div>
                <div className="text-xs font-medium">{modoConfig.label}</div>
              </div>

              {isAtivo && (
                <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Explicação dos Modos */}
      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Como funcionam os modos:
        </h4>
        <div className="space-y-2 text-xs text-blue-800">
          <div className="flex gap-2">
            <span>🟢</span>
            <div>
              <strong>Ligado:</strong> A IA processa e gera respostas automaticamente.
              Mensagens ainda precisam de aprovação no modo Atenção.
            </div>
          </div>
          <div className="flex gap-2">
            <span>🟡</span>
            <div>
              <strong>Atenção:</strong> Modo recomendado. A IA sugere respostas,
              mas você SEMPRE aprova, edita ou recusa antes de enviar.
            </div>
          </div>
          <div className="flex gap-2">
            <span>🔴</span>
            <div>
              <strong>Desligado:</strong> A IA para de processar novas mensagens.
              Use para pausas ou atendimento 100% manual.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
