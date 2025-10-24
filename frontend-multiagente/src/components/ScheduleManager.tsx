import React, { useState, useEffect } from 'react';
import { Clock, Plus, Edit, Trash2, Save, X, Calendar } from 'lucide-react';

interface Agendamento {
  id?: string;
  nome: string;
  hora_ligar: string;
  hora_desligar: string;
  dias_semana: number[];
  modo_dentro_horario: string;
  modo_fora_horario: string;
  mensagem_auto_fora_horario: string;
  ativo: boolean;
}

interface ScheduleManagerProps {
  empresaId: string;
}

const DIAS_SEMANA = [
  { num: 1, label: 'Seg' },
  { num: 2, label: 'Ter' },
  { num: 3, label: 'Qua' },
  { num: 4, label: 'Qui' },
  { num: 5, label: 'Sex' },
  { num: 6, label: 'Sáb' },
  { num: 7, label: 'Dom' }
];

export const ScheduleManager: React.FC<ScheduleManagerProps> = ({ empresaId }) => {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [agendamentoEditando, setAgendamentoEditando] = useState<Agendamento | null>(null);
  const [loading, setLoading] = useState(true);

  const agendamentoVazio: Agendamento = {
    nome: '',
    hora_ligar: '08:00',
    hora_desligar: '18:00',
    dias_semana: [1, 2, 3, 4, 5],
    modo_dentro_horario: 'atencao',
    modo_fora_horario: 'desligado',
    mensagem_auto_fora_horario: 'Olá! Nosso horário de atendimento é de segunda a sexta, das 8h às 18h. Retornaremos em breve!',
    ativo: true
  };

  const [formData, setFormData] = useState<Agendamento>(agendamentoVazio);

  useEffect(() => {
    carregarAgendamentos();
  }, [empresaId]);

  const carregarAgendamentos = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/ia-control/agendamentos/${empresaId}`);
      const data = await response.json();
      if (data.success) {
        setAgendamentos(data.agendamentos);
      }
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const salvarAgendamento = async () => {
    try {
      const url = agendamentoEditando?.id
        ? `http://localhost:8000/api/ia-control/agendamentos/${agendamentoEditando.id}`
        : 'http://localhost:8000/api/ia-control/agendamentos';

      const method = agendamentoEditando?.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: empresaId,
          ...formData
        })
      });

      const data = await response.json();
      if (data.success) {
        carregarAgendamentos();
        fecharForm();
      }
    } catch (error) {
      console.error('Erro ao salvar agendamento:', error);
    }
  };

  const deletarAgendamento = async (id: string) => {
    if (!confirm('Deseja realmente deletar este agendamento?')) return;

    try {
      const response = await fetch(`http://localhost:8000/api/ia-control/agendamentos/${id}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        carregarAgendamentos();
      }
    } catch (error) {
      console.error('Erro ao deletar agendamento:', error);
    }
  };

  const toggleDia = (dia: number) => {
    setFormData(prev => ({
      ...prev,
      dias_semana: prev.dias_semana.includes(dia)
        ? prev.dias_semana.filter(d => d !== dia)
        : [...prev.dias_semana, dia].sort()
    }));
  };

  const editarAgendamento = (agendamento: Agendamento) => {
    setAgendamentoEditando(agendamento);
    setFormData(agendamento);
    setMostrarForm(true);
  };

  const novoAgendamento = () => {
    setAgendamentoEditando(null);
    setFormData(agendamentoVazio);
    setMostrarForm(true);
  };

  const fecharForm = () => {
    setMostrarForm(false);
    setAgendamentoEditando(null);
    setFormData(agendamentoVazio);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2].map(i => (
              <div key={i} className="h-24 bg-gray-100 rounded"></div>
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
            <Calendar className="w-5 h-5" />
            Agendamentos de Horários
          </h3>
          <button
            onClick={novoAgendamento}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Novo Agendamento
          </button>
        </div>
      </div>

      {/* Lista de Agendamentos */}
      <div className="p-4 space-y-3">
        {agendamentos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="font-medium">Nenhum agendamento criado</p>
            <p className="text-sm">Crie um agendamento para controlar a IA automaticamente por horário</p>
          </div>
        ) : (
          agendamentos.map((agendamento) => (
            <div key={agendamento.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-gray-900">{agendamento.nome}</h4>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      agendamento.ativo
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {agendamento.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>{agendamento.hora_ligar} - {agendamento.hora_desligar}</span>
                    </div>
                    <div className="flex gap-1">
                      {DIAS_SEMANA.map(dia => (
                        <span
                          key={dia.num}
                          className={`px-2 py-0.5 rounded text-xs ${
                            agendamento.dias_semana.includes(dia.num)
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-400'
                          }`}
                        >
                          {dia.label}
                        </span>
                      ))}
                    </div>
                    <div className="text-xs">
                      <span className="text-gray-500">Dentro do horário:</span>{' '}
                      <span className="font-medium">{agendamento.modo_dentro_horario}</span>
                      {' • '}
                      <span className="text-gray-500">Fora:</span>{' '}
                      <span className="font-medium">{agendamento.modo_fora_horario}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => editarAgendamento(agendamento)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Editar"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deletarAgendamento(agendamento.id!)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Deletar"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Formulário Modal */}
      {mostrarForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {agendamentoEditando ? 'Editar Agendamento' : 'Novo Agendamento'}
                </h3>
                <button
                  onClick={fecharForm}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome do Agendamento
                </label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: Horário Comercial"
                />
              </div>

              {/* Horários */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hora de Ligar
                  </label>
                  <input
                    type="time"
                    value={formData.hora_ligar}
                    onChange={(e) => setFormData({ ...formData, hora_ligar: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hora de Desligar
                  </label>
                  <input
                    type="time"
                    value={formData.hora_desligar}
                    onChange={(e) => setFormData({ ...formData, hora_desligar: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Dias da Semana */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dias da Semana
                </label>
                <div className="flex gap-2">
                  {DIAS_SEMANA.map(dia => (
                    <button
                      key={dia.num}
                      onClick={() => toggleDia(dia.num)}
                      className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                        formData.dias_semana.includes(dia.num)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {dia.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Modos */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Modo Dentro do Horário
                  </label>
                  <select
                    value={formData.modo_dentro_horario}
                    onChange={(e) => setFormData({ ...formData, modo_dentro_horario: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ligado">Ligado</option>
                    <option value="atencao">Atenção</option>
                    <option value="desligado">Desligado</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Modo Fora do Horário
                  </label>
                  <select
                    value={formData.modo_fora_horario}
                    onChange={(e) => setFormData({ ...formData, modo_fora_horario: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ligado">Ligado</option>
                    <option value="atencao">Atenção</option>
                    <option value="desligado">Desligado</option>
                  </select>
                </div>
              </div>

              {/* Mensagem Automática */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mensagem Automática Fora do Horário (opcional)
                </label>
                <textarea
                  value={formData.mensagem_auto_fora_horario}
                  onChange={(e) => setFormData({ ...formData, mensagem_auto_fora_horario: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Ex: Olá! Estamos fora do horário de atendimento..."
                />
              </div>

              {/* Ativo */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="ativo"
                  checked={formData.ativo}
                  onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="ativo" className="text-sm font-medium text-gray-700">
                  Agendamento ativo
                </label>
              </div>
            </div>

            {/* Botões */}
            <div className="p-6 border-t border-gray-200 flex gap-3">
              <button
                onClick={salvarAgendamento}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                Salvar Agendamento
              </button>
              <button
                onClick={fecharForm}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
