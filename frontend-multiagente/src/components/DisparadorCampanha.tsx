import { useState, useEffect } from 'react'
import { Send, Upload, Play, Pause, Trash2, Plus, Download, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface Campanha {
  id: string
  nome: string
  mensagem_promocao: string
  imagem_url?: string
  status: string
  total_contatos: number
  enviados: number
  falhas: number
  data_inicio?: string
  data_conclusao?: string
  intervalo_min_segundos: number
  intervalo_max_segundos: number
  variar_com_ia: boolean
}

interface Contato {
  nome: string
  telefone: string
}

export function DisparadorCampanha() {
  const [campanhas, setCampanhas] = useState<Campanha[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Wizard state
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3>(1)
  const [nome, setNome] = useState('')
  const [mensagemPromocao, setMensagemPromocao] = useState('')
  const [imagemUrl, setImagemUrl] = useState('')
  const [intervaloMin, setIntervaloMin] = useState(30)
  const [intervaloMax, setIntervaloMax] = useState(300)
  const [variarComIA, setVariarComIA] = useState(true)
  const [contatos, setContatos] = useState<Contato[]>([])
  const [contatoNome, setContatoNome] = useState('')
  const [contatoTelefone, setContatoTelefone] = useState('')

  useEffect(() => {
    carregarCampanhas()
  }, [])

  const carregarCampanhas = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://138.68.13.174:8000/api/disparador/campanhas')
      if (!response.ok) throw new Error('Erro ao carregar campanhas')
      const data = await response.json()
      setCampanhas(data)
    } catch (err) {
      console.error('Erro ao carregar campanhas:', err)
      setError('Erro ao carregar campanhas')
    } finally {
      setLoading(false)
    }
  }

  const criarCampanha = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('http://138.68.13.174:8000/api/disparador/campanhas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: 'emp1',
          nome,
          mensagem_promocao: mensagemPromocao,
          imagem_url: imagemUrl || null,
          intervalo_min: intervaloMin,
          intervalo_max: intervaloMax,
          variar_com_ia: variarComIA,
          contatos: contatos.map(c => ({
            nome: c.nome,
            telefone: c.telefone.replace(/\D/g, '')
          }))
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao criar campanha')
      }

      setSuccess('Campanha criada com sucesso!')
      resetWizard()
      await carregarCampanhas()
    } catch (err: any) {
      console.error('Erro ao criar campanha:', err)
      setError(err.message || 'Erro ao criar campanha')
    } finally {
      setLoading(false)
    }
  }

  const iniciarCampanha = async (campanhaId: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`http://138.68.13.174:8000/api/disparador/campanhas/${campanhaId}/iniciar`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao iniciar campanha')
      }

      setSuccess('Campanha iniciada! O disparo está sendo processado em background.')
      await carregarCampanhas()
    } catch (err: any) {
      console.error('Erro ao iniciar campanha:', err)
      setError(err.message || 'Erro ao iniciar campanha')
    } finally {
      setLoading(false)
    }
  }

  const pausarCampanha = async (campanhaId: string) => {
    try {
      setLoading(true)
      const response = await fetch(`http://138.68.13.174:8000/api/disparador/campanhas/${campanhaId}/pausar`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Erro ao pausar campanha')
      setSuccess('Campanha pausada')
      await carregarCampanhas()
    } catch (err) {
      console.error('Erro ao pausar campanha:', err)
      setError('Erro ao pausar campanha')
    } finally {
      setLoading(false)
    }
  }

  const deletarCampanha = async (campanhaId: string) => {
    if (!confirm('Tem certeza que deseja deletar esta campanha?')) return

    try {
      setLoading(true)
      const response = await fetch(`http://138.68.13.174:8000/api/disparador/campanhas/${campanhaId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Erro ao deletar campanha')
      setSuccess('Campanha deletada')
      await carregarCampanhas()
    } catch (err) {
      console.error('Erro ao deletar campanha:', err)
      setError('Erro ao deletar campanha')
    } finally {
      setLoading(false)
    }
  }

  const adicionarContato = () => {
    if (!contatoNome.trim() || !contatoTelefone.trim()) {
      setError('Nome e telefone são obrigatórios')
      return
    }

    const telefoneNumeros = contatoTelefone.replace(/\D/g, '')
    if (telefoneNumeros.length < 10 || telefoneNumeros.length > 15) {
      setError('Telefone inválido (deve ter entre 10 e 15 dígitos)')
      return
    }

    setContatos([...contatos, { nome: contatoNome, telefone: telefoneNumeros }])
    setContatoNome('')
    setContatoTelefone('')
    setError(null)
  }

  const removerContato = (index: number) => {
    setContatos(contatos.filter((_, i) => i !== index))
  }

  const resetWizard = () => {
    setWizardStep(1)
    setNome('')
    setMensagemPromocao('')
    setImagemUrl('')
    setIntervaloMin(30)
    setIntervaloMax(300)
    setVariarComIA(true)
    setContatos([])
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
      rascunho: { label: 'Rascunho', variant: 'secondary' },
      agendada: { label: 'Agendada', variant: 'default' },
      em_andamento: { label: 'Em Andamento', variant: 'default' },
      pausada: { label: 'Pausada', variant: 'outline' },
      concluida: { label: 'Concluída', variant: 'outline' },
      cancelada: { label: 'Cancelada', variant: 'destructive' }
    }
    const s = statusMap[status] || { label: status, variant: 'default' }
    return <Badge variant={s.variant}>{s.label}</Badge>
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="campanhas">
        <TabsList>
          <TabsTrigger value="campanhas">Minhas Campanhas</TabsTrigger>
          <TabsTrigger value="nova">Nova Campanha</TabsTrigger>
        </TabsList>

        {/* Lista de Campanhas */}
        <TabsContent value="campanhas" className="space-y-4">
          {loading && <p>Carregando...</p>}

          {!loading && campanhas.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">
                  Nenhuma campanha encontrada. Crie sua primeira campanha!
                </p>
              </CardContent>
            </Card>
          )}

          {campanhas.map(campanha => (
            <Card key={campanha.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{campanha.nome}</CardTitle>
                    <CardDescription className="mt-2">
                      {campanha.mensagem_promocao.substring(0, 100)}...
                    </CardDescription>
                  </div>
                  {getStatusBadge(campanha.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Estatísticas */}
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Total</p>
                      <p className="text-2xl font-bold">{campanha.total_contatos}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Enviados</p>
                      <p className="text-2xl font-bold text-green-600">{campanha.enviados}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Falhas</p>
                      <p className="text-2xl font-bold text-red-600">{campanha.falhas}</p>
                    </div>
                  </div>

                  {/* Progresso */}
                  {campanha.status === 'em_andamento' && (
                    <div>
                      <Progress
                        value={(campanha.enviados / campanha.total_contatos) * 100}
                        className="h-2"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {Math.round((campanha.enviados / campanha.total_contatos) * 100)}% concluído
                      </p>
                    </div>
                  )}

                  {/* Configurações */}
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p>Intervalo: {campanha.intervalo_min_segundos}s - {campanha.intervalo_max_segundos}s</p>
                    {campanha.variar_com_ia && <p>✓ Variação de mensagens com IA</p>}
                  </div>

                  {/* Ações */}
                  <div className="flex gap-2 pt-2">
                    {(campanha.status === 'rascunho' || campanha.status === 'pausada') && (
                      <Button size="sm" onClick={() => iniciarCampanha(campanha.id)}>
                        <Play className="w-4 h-4 mr-1" />
                        Iniciar
                      </Button>
                    )}

                    {campanha.status === 'em_andamento' && (
                      <Button size="sm" variant="outline" onClick={() => pausarCampanha(campanha.id)}>
                        <Pause className="w-4 h-4 mr-1" />
                        Pausar
                      </Button>
                    )}

                    {(campanha.status === 'rascunho' || campanha.status === 'cancelada') && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => deletarCampanha(campanha.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Deletar
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Nova Campanha (Wizard) */}
        <TabsContent value="nova">
          <Card>
            <CardHeader>
              <CardTitle>Criar Nova Campanha</CardTitle>
              <CardDescription>
                Passo {wizardStep} de 3
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Step 1: Configuração */}
              {wizardStep === 1 && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="nome">Nome da Campanha</Label>
                    <Input
                      id="nome"
                      value={nome}
                      onChange={e => setNome(e.target.value)}
                      placeholder="Ex: Promoção Baterias 60ah"
                    />
                  </div>

                  <div>
                    <Label htmlFor="mensagem">Mensagem de Promoção</Label>
                    <Textarea
                      id="mensagem"
                      value={mensagemPromocao}
                      onChange={e => setMensagemPromocao(e.target.value)}
                      placeholder="Use {nome} para personalizar com o nome do contato"
                      rows={6}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Dica: Use {'{nome}'} para personalizar (ex: "Olá {'{nome}'}, temos uma promoção especial...")
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="imagem">URL da Imagem (opcional)</Label>
                    <Input
                      id="imagem"
                      value={imagemUrl}
                      onChange={e => setImagemUrl(e.target.value)}
                      placeholder="https://exemplo.com/imagem.jpg"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="intervalo-min">Intervalo Mínimo (segundos)</Label>
                      <Input
                        id="intervalo-min"
                        type="number"
                        value={intervaloMin}
                        onChange={e => setIntervaloMin(parseInt(e.target.value))}
                        min={10}
                        max={300}
                      />
                    </div>
                    <div>
                      <Label htmlFor="intervalo-max">Intervalo Máximo (segundos)</Label>
                      <Input
                        id="intervalo-max"
                        type="number"
                        value={intervaloMax}
                        onChange={e => setIntervaloMax(parseInt(e.target.value))}
                        min={30}
                        max={600}
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="variar-ia"
                      checked={variarComIA}
                      onCheckedChange={setVariarComIA}
                    />
                    <Label htmlFor="variar-ia">Variar mensagem com IA (anti-bloqueio)</Label>
                  </div>

                  <Button
                    onClick={() => setWizardStep(2)}
                    disabled={!nome || !mensagemPromocao}
                  >
                    Próximo
                  </Button>
                </div>
              )}

              {/* Step 2: Contatos */}
              {wizardStep === 2 && (
                <div className="space-y-4">
                  <div>
                    <Label>Adicionar Contatos</Label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <Input
                        placeholder="Nome"
                        value={contatoNome}
                        onChange={e => setContatoNome(e.target.value)}
                      />
                      <Input
                        placeholder="Telefone (apenas números)"
                        value={contatoTelefone}
                        onChange={e => setContatoTelefone(e.target.value)}
                      />
                    </div>
                    <Button size="sm" onClick={adicionarContato} className="mt-2">
                      <Plus className="w-4 h-4 mr-1" />
                      Adicionar
                    </Button>
                  </div>

                  {contatos.length > 0 && (
                    <div>
                      <Label>Contatos Adicionados ({contatos.length})</Label>
                      <div className="space-y-2 mt-2 max-h-60 overflow-y-auto">
                        {contatos.map((contato, index) => (
                          <div key={index} className="flex items-center justify-between bg-muted p-2 rounded">
                            <span className="text-sm">
                              {contato.nome} - {contato.telefone}
                            </span>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removerContato(index)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setWizardStep(1)}>
                      Voltar
                    </Button>
                    <Button
                      onClick={() => setWizardStep(3)}
                      disabled={contatos.length === 0}
                    >
                      Próximo
                    </Button>
                  </div>
                </div>
              )}

              {/* Step 3: Confirmar */}
              {wizardStep === 3 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="font-semibold">Resumo da Campanha</h3>
                    <div className="bg-muted p-4 rounded space-y-2 text-sm">
                      <p><strong>Nome:</strong> {nome}</p>
                      <p><strong>Mensagem:</strong> {mensagemPromocao.substring(0, 100)}...</p>
                      {imagemUrl && <p><strong>Com imagem:</strong> Sim</p>}
                      <p><strong>Contatos:</strong> {contatos.length}</p>
                      <p><strong>Intervalo:</strong> {intervaloMin}s - {intervaloMax}s</p>
                      <p><strong>Variação IA:</strong> {variarComIA ? 'Sim' : 'Não'}</p>
                    </div>
                  </div>

                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      A campanha será criada como rascunho. Você poderá iniciá-la depois na lista de campanhas.
                    </AlertDescription>
                  </Alert>

                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setWizardStep(2)}>
                      Voltar
                    </Button>
                    <Button onClick={criarCampanha} disabled={loading}>
                      {loading ? 'Criando...' : 'Criar Campanha'}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
