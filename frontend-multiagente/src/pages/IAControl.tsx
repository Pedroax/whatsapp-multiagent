import React from 'react';
import { IAModeControl } from '../components/IAModeControl';
import { ApprovalQueue } from '../components/ApprovalQueue';
import { ScheduleManager } from '../components/ScheduleManager';

const IAControl: React.FC = () => {
  // TODO: Pegar empresa_id do contexto de autenticação
  const empresaId = 'sua-empresa-uuid';

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Controle da IA
          </h1>
          <p className="text-gray-600">
            Gerencie o comportamento da IA, aprove mensagens e configure horários automáticos
          </p>
        </div>

        {/* Grid principal */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Coluna esquerda - Controle e Agendamentos */}
          <div className="lg:col-span-1 space-y-6">
            <IAModeControl empresaId={empresaId} />
            <ScheduleManager empresaId={empresaId} />
          </div>

          {/* Coluna direita - Fila de Aprovação */}
          <div className="lg:col-span-2">
            <ApprovalQueue empresaId={empresaId} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default IAControl;
