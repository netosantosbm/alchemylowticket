import React, { useState, useEffect } from 'react'
import * as Lucide from 'lucide-react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  BarChart, 
  Bar, 
  Cell 
} from 'recharts'

const API_BASE = '/api'

const KANBAN_COLUMNS = [
  { id: 'idea', label: 'Ideia / Rascunho', icon: '💡', border: 'border-purple-500/40', badge: 'bg-purple-950/80 text-purple-300 border-purple-700' },
  { id: 'in_production', label: 'Em Produção', icon: '✍️', border: 'border-amber-500/40', badge: 'bg-amber-950/80 text-amber-300 border-amber-700' },
  { id: 'ready', label: 'Pronto p/ Tráfego', icon: '🚀', border: 'border-blue-500/40', badge: 'bg-blue-950/80 text-blue-300 border-blue-700' },
  { id: 'active', label: 'Ativo (Vendendo)', icon: '💰', border: 'border-emerald-500/40', badge: 'bg-emerald-950/80 text-emerald-300 border-emerald-700' },
  { id: 'paused', label: 'Pausado', icon: '⏸️', border: 'border-slate-700', badge: 'bg-slate-800 text-slate-400 border-slate-600' }
]

const TREND_STATUS_LABELS = {
  new: { label: 'Recém-Minerado', color: 'bg-slate-800 text-slate-300 border-slate-600' },
  analyzing: { label: 'Em Análise', color: 'bg-amber-950 text-amber-300 border-amber-700' },
  approved: { label: 'Aprovado 🚀', color: 'bg-emerald-950 text-emerald-300 border-emerald-700' },
  rejected: { label: 'Inviável', color: 'bg-rose-950 text-rose-300 border-rose-700' }
}

const PLATFORM_COLORS = {
  kiwify: '#22c55e',
  hotmart: '#f97316',
  eduzz: '#3b82f6',
  braip: '#a855f7',
  other: '#64748b'
}

export default function App() {
  const [activeTab, setActiveTab] = useState('radar') // 'radar' | 'products' | 'orders' | 'meta_spy' | 'simulator'
  const [viewMode, setViewMode] = useState('kanban') // 'kanban' | 'grid'
  const [loading, setLoading] = useState(false)
  const [apiConnected, setApiConnected] = useState(false)
  const [notification, setNotification] = useState(null)

  // Data states
  const [trends, setTrends] = useState([])
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [chartData, setChartData] = useState([])
  const [metrics, setMetrics] = useState({
    total_revenue: 0,
    net_revenue: 0,
    total_orders: 0,
    today_revenue: 0,
    today_orders: 0,
    average_ticket: 0,
    orders_by_platform: {},
    orders_by_status: {}
  })

  // Filters
  const [trendNiche, setTrendNiche] = useState('Todos')
  const [trendSearch, setTrendSearch] = useState('')
  const [miningLoading, setMiningLoading] = useState(false)

  // Meta Ads Modal & Spy State
  const [spyModal, setSpyModal] = useState({ isOpen: false, loading: false, data: null })
  const [customSpyQuery, setCustomSpyQuery] = useState('')
  const [customSpyNiche, setCustomSpyNiche] = useState('Concursos')
  const [customSpyResult, setCustomSpyResult] = useState(null)
  const [customSpyLoading, setCustomSpyLoading] = useState(false)

  // New Product Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newProd, setNewProd] = useState({
    title: '',
    description: '',
    niche: 'Concursos',
    price: 27.00,
    checkout_url: '',
    delivery_url: '',
    status: 'idea'
  })

  // Webhook Simulator State
  const [simForm, setSimForm] = useState({
    platform: 'kiwify',
    amount: 27.90,
    product_title: 'Planner Financeiro Definitivo Notion + Planilha',
    customer_name: 'Mariana Silva',
    customer_email: 'mariana.silva@email.com'
  })
  const [simResponse, setSimResponse] = useState(null)

  // Kiwify Integration State
  const [kiwifyConfig, setKiwifyConfig] = useState({
    client_id: '',
    client_secret: 'e9dd2a7ae973fc5fc1cb5b8cd71ffe98a2de73fb41b037993dff47763bd8ccc4',
    account_id: '',
    configured: false,
    masked_secret: '',
    updated_at: null
  })
  const [showKiwifySecret, setShowKiwifySecret] = useState(false)
  const [kiwifySyncLoading, setKiwifySyncLoading] = useState(false)
  const [kiwifyTestLoading, setKiwifyTestLoading] = useState(false)
  const [kiwifySaveLoading, setKiwifySaveLoading] = useState(false)

  // AI Ads Generator State
  const [aiAdsModal, setAiAdsModal] = useState({
    isOpen: false,
    loading: false,
    product: null,
    customTitle: '',
    competitorOffer: '',
    targetAudience: '',
    tone: 'Direto ao ponto, empático e de alta conversão',
    result: null,
    activeAngleTab: 0,
    saveLoading: false
  })

  // AI Settings State (OpenAI / Gemini)
  const [aiSettings, setAiSettings] = useState({
    has_openai_key: false,
    has_gemini_key: false,
    active_engine: 'Motor Neural Nativo de Direct Response (Ativo)'
  })
  const [openaiKeyInput, setOpenaiKeyInput] = useState('')
  const [geminiKeyInput, setGeminiKeyInput] = useState('')
  const [aiKeySaveLoading, setAiKeySaveLoading] = useState(false)

  const showToast = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 4000)
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const rootRes = await fetch('/')
      if (rootRes.ok) setApiConnected(true)

      const trendsRes = await fetch(`${API_BASE}/trends?niche=${trendNiche}`)
      if (trendsRes.ok) {
        const data = await trendsRes.json()
        setTrends(data)
      }

      const prodRes = await fetch(`${API_BASE}/products`)
      if (prodRes.ok) {
        const data = await prodRes.json()
        setProducts(data)
      }

      const ordersRes = await fetch(`${API_BASE}/orders?limit=30`)
      if (ordersRes.ok) {
        const data = await ordersRes.json()
        setOrders(data)
      }

      const metricsRes = await fetch(`${API_BASE}/orders/metrics`)
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data)
      }

      const chartRes = await fetch(`${API_BASE}/orders/chart`)
      if (chartRes.ok) {
        const data = await chartRes.json()
        setChartData(data)
      }

    } catch (err) {
      console.error('Erro ao conectar com API:', err)
      setApiConnected(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    fetchKiwifyConfig()
    fetchAiSettings()
  }, [trendNiche])

  const fetchAiSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/ai-ads/settings`)
      if (res.ok) {
        const data = await res.json()
        setAiSettings(data)
      }
    } catch (e) {
      console.error('Erro ao carregar status de IA:', e)
    }
  }

  const handleSaveAiKey = async (provider, key) => {
    if (!key.trim()) {
      showToast('Por favor, informe a chave de API', 'error')
      return
    }
    setAiKeySaveLoading(true)
    try {
      const res = await fetch(`${API_BASE}/ai-ads/settings/key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: key })
      })
      if (res.ok) {
        showToast(`Chave de API ${provider.toUpperCase()} salva com sucesso!`)
        fetchAiSettings()
        if (provider === 'openai') setOpenaiKeyInput('')
        if (provider === 'gemini') setGeminiKeyInput('')
      } else {
        showToast('Erro ao salvar chave de API', 'error')
      }
    } catch (e) {
      showToast('Falha na comunicação com o servidor', 'error')
    } finally {
      setAiKeySaveLoading(false)
    }
  }

  const handleOpenAiAdsModal = (product = null, defaultOffer = '') => {
    setAiAdsModal({
      isOpen: true,
      loading: false,
      product: product,
      customTitle: product?.title || '',
      competitorOffer: defaultOffer || '',
      targetAudience: '',
      tone: 'Direto ao ponto, empático e de alta conversão',
      result: product?.ad_copies || null,
      activeAngleTab: 0,
      saveLoading: false
    })
  }

  const handleGenerateAiAds = async () => {
    const title = aiAdsModal.product?.title || aiAdsModal.customTitle
    if (!title) {
      showToast('Informe o título do produto ou selecione um do Kanban', 'error')
      return
    }
    setAiAdsModal(prev => ({ ...prev, loading: true }))
    try {
      const res = await fetch(`${API_BASE}/ai-ads/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: aiAdsModal.product?.id || null,
          product_title: title,
          niche: aiAdsModal.product?.niche || 'Geral',
          price: aiAdsModal.product?.price || 27.0,
          competitor_offer: aiAdsModal.competitorOffer,
          target_audience: aiAdsModal.targetAudience,
          tone: aiAdsModal.tone,
          save_to_product: !!aiAdsModal.product?.id
        })
      })
      if (res.ok) {
        const data = await res.json()
        setAiAdsModal(prev => ({
          ...prev,
          loading: false,
          result: data,
          activeAngleTab: 0
        }))
        showToast('🚀 3 Variações de anúncios geradas com sucesso!')
        fetchData()
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err.detail || 'Erro ao gerar anúncios com IA', 'error')
        setAiAdsModal(prev => ({ ...prev, loading: false }))
      }
    } catch (e) {
      showToast('Falha na comunicação com a API de IA', 'error')
      setAiAdsModal(prev => ({ ...prev, loading: false }))
    }
  }

  const handleSaveAdsToProduct = async (productId, adsData) => {
    if (!productId || !adsData) return
    setAiAdsModal(prev => ({ ...prev, saveLoading: true }))
    try {
      const res = await fetch(`${API_BASE}/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ad_copies: adsData })
      })
      if (res.ok) {
        showToast('💾 Anúncios salvos no produto!')
        fetchData()
      } else {
        showToast('Erro ao salvar anúncios no produto', 'error')
      }
    } catch (e) {
      showToast('Falha ao salvar', 'error')
    } finally {
      setAiAdsModal(prev => ({ ...prev, saveLoading: false }))
    }
  }

  const handleCopyText = (text, label) => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text)
      showToast(`📋 ${label} copiado!`)
    } else {
      showToast('Selecione o texto para copiar', 'info')
    }
  }

  const fetchKiwifyConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/integrations/kiwify`)
      if (res.ok) {
        const data = await res.json()
        if (data.configured) {
          setKiwifyConfig(prev => ({
            ...prev,
            client_id: data.client_id || '',
            account_id: data.account_id || '',
            configured: true,
            masked_secret: data.masked_secret || '',
            updated_at: data.updated_at
          }))
        }
      }
    } catch (e) {
      console.error('Erro ao carregar configs da Kiwify:', e)
    }
  }

  const handleSaveKiwify = async (e) => {
    if (e) e.preventDefault()
    if (!kiwifyConfig.client_id || !kiwifyConfig.client_secret) {
      showToast('Client ID e Client Secret são obrigatórios', 'error')
      return
    }
    setKiwifySaveLoading(true)
    try {
      const res = await fetch(`${API_BASE}/integrations/kiwify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: kiwifyConfig.client_id,
          client_secret: kiwifyConfig.client_secret,
          account_id: kiwifyConfig.account_id || kiwifyConfig.client_id
        })
      })
      const data = await res.json()
      if (res.ok) {
        showToast('Configurações da Kiwify salvas com sucesso!')
        fetchKiwifyConfig()
      } else {
        showToast(data.detail || 'Erro ao salvar credenciais', 'error')
      }
    } catch (err) {
      showToast('Erro de comunicação com o servidor', 'error')
    } finally {
      setKiwifySaveLoading(false)
    }
  }

  const handleTestKiwify = async () => {
    if (!kiwifyConfig.client_id || !kiwifyConfig.client_secret) {
      showToast('Preencha o Client ID e Client Secret para testar', 'error')
      return
    }
    setKiwifyTestLoading(true)
    try {
      const res = await fetch(`${API_BASE}/integrations/kiwify/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: kiwifyConfig.client_id,
          client_secret: kiwifyConfig.client_secret,
          account_id: kiwifyConfig.account_id
        })
      })
      const data = await res.json()
      if (data.connected) {
        showToast(data.message, 'success')
      } else {
        showToast(data.message || 'Falha ao conectar com a Kiwify', 'error')
      }
    } catch (e) {
      showToast('Erro ao testar conexão com Kiwify', 'error')
    } finally {
      setKiwifyTestLoading(false)
    }
  }

  const handleSyncKiwify = async () => {
    setKiwifySyncLoading(true)
    try {
      const res = await fetch(`${API_BASE}/integrations/kiwify/sync`, {
        method: 'POST'
      })
      const data = await res.json()
      if (res.ok) {
        showToast(`Sincronização concluída! ${data.total_found} produtos encontrados na Kiwify (${data.created_count} novos cadastrados, ${data.updated_count} atualizados).`, 'success')
        fetchData()
      } else {
        showToast(data.detail || 'Erro ao sincronizar produtos da Kiwify', 'error')
      }
    } catch (e) {
      showToast('Erro ao conectar com API da Kiwify', 'error')
    } finally {
      setKiwifySyncLoading(false)
    }
  }

  const handleMineTrends = async (niche = null) => {
    setMiningLoading(true)
    try {
      const payload = niche && niche !== 'Todos' ? { niche } : {}
      const res = await fetch(`${API_BASE}/trends/mine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (res.ok) {
        showToast(`⚡ ${data.message}`)
        fetchData()
      } else {
        showToast('Falha ao minerar dados do Google Trends', 'error')
      }
    } catch (err) {
      showToast('Erro ao conectar com serviço de mineração', 'error')
    } finally {
      setMiningLoading(false)
    }
  }

  const handleInspectAds = async (keyword, niche, trendId = null) => {
    setSpyModal({ isOpen: true, loading: true, data: null })
    try {
      const url = `${API_BASE}/competitors/analyze?keyword=${encodeURIComponent(keyword)}&niche=${encodeURIComponent(niche)}`
      const res = await fetch(url)
      const data = await res.json()
      setSpyModal({ isOpen: true, loading: false, data })

      // Persist to Supabase if trendId is supplied
      if (trendId) {
        fetch(`${API_BASE}/competitors/analyze-trend/${trendId}`, { method: 'POST' }).catch(() => {})
      }
    } catch (e) {
      showToast('Erro ao analisar concorrência na Meta', 'error')
      setSpyModal({ isOpen: false, loading: false, data: null })
    }
  }

  const handleCustomSpySearch = async (e) => {
    e.preventDefault()
    if (!customSpyQuery.trim()) return
    setCustomSpyLoading(true)
    try {
      const url = `${API_BASE}/competitors/analyze?keyword=${encodeURIComponent(customSpyQuery)}&niche=${encodeURIComponent(customSpyNiche)}`
      const res = await fetch(url)
      const data = await res.json()
      setCustomSpyResult(data)
    } catch (e) {
      showToast('Erro ao buscar dados na Meta', 'error')
    } finally {
      setCustomSpyLoading(false)
    }
  }

  const handleConvertToProduct = async (trend) => {
    try {
      const res = await fetch(`${API_BASE}/trends/${trend.id}/convert-to-product`, {
        method: 'POST'
      })
      if (res.ok) {
        const product = await res.json()
        const alreadyInList = products.some(p => p.id === product.id)
        if (alreadyInList) {
          showToast(`ℹ️ "${product.title}" já está no seu Kanban!`)
        } else {
          showToast(`💡 Sucesso! "${product.title}" adicionado ao Kanban`)
        }
        await fetchData()
        setActiveTab('products')
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err.detail || 'Erro ao converter tendência em produto', 'error')
      }
    } catch (e) {
      showToast('Falha na requisição', 'error')
    }
  }

  const handleStatusChange = async (productId, nextStatus) => {
    try {
      const res = await fetch(`${API_BASE}/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus })
      })
      if (res.ok) {
        const col = KANBAN_COLUMNS.find(c => c.id === nextStatus)
        showToast(`Status atualizado para: ${col?.label || nextStatus}`)
        fetchData()
      }
    } catch (e) {
      showToast('Erro ao atualizar status', 'error')
    }
  }

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Deseja realmente remover este produto do catálogo?')) return
    try {
      const res = await fetch(`${API_BASE}/products/${productId}`, { method: 'DELETE' })
      if (res.ok) {
        showToast('Produto removido com sucesso')
        fetchData()
      }
    } catch (e) {
      showToast('Erro ao remover produto', 'error')
    }
  }

  const handleCreateProduct = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch(`${API_BASE}/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProd)
      })
      if (res.ok) {
        showToast('Novo infoproduto gravado no Supabase!')
        setIsModalOpen(false)
        setNewProd({ title: '', description: '', niche: 'Concursos', price: 27.0, checkout_url: '', delivery_url: '', status: 'idea' })
        fetchData()
      }
    } catch (e) {
      showToast('Erro ao cadastrar produto', 'error')
    }
  }

  const handleSimulateWebhook = async (e) => {
    e.preventDefault()
    try {
      const url = `${API_BASE}/webhooks/simulate?platform=${simForm.platform}&amount=${simForm.amount}&product_title=${encodeURIComponent(simForm.product_title)}&customer_name=${encodeURIComponent(simForm.customer_name)}&customer_email=${encodeURIComponent(simForm.customer_email)}`
      const res = await fetch(url, { method: 'POST' })
      const data = await res.json()
      setSimResponse(data)
      if (res.ok) {
        showToast(`💰 Venda simulada gravada no Supabase via ${simForm.platform.toUpperCase()}!`)
        fetchData()
      }
    } catch (e) {
      showToast('Erro na simulação do webhook', 'error')
    }
  }

  const handleClearTestOrders = async () => {
    if (!window.confirm('Tem certeza que deseja apagar os pedidos de teste para iniciar com dados reais limpos?')) return
    try {
      const res = await fetch(`${API_BASE}/orders/test-data`, { method: 'DELETE' })
      const data = await res.json()
      if (res.ok) {
        showToast(data.message)
        fetchData()
      }
    } catch (e) {
      showToast('Erro ao limpar pedidos de teste', 'error')
    }
  }

  const filteredTrends = trends.filter(t => 
    t.keyword.toLowerCase().includes(trendSearch.toLowerCase()) ||
    t.niche.toLowerCase().includes(trendSearch.toLowerCase())
  )

  const platformChartData = Object.entries(metrics.orders_by_platform || {}).map(([key, count]) => ({
    name: key.toUpperCase(),
    orders: count,
    color: PLATFORM_COLORS[key] || '#64748b'
  }))

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl border text-sm font-medium transition-all duration-300 ${
          notification.type === 'error' 
            ? 'bg-rose-950/90 text-rose-200 border-rose-800' 
            : 'bg-emerald-950/90 text-emerald-200 border-emerald-700/60'
        }`}>
          {notification.type === 'error' ? <Lucide.AlertCircle className="w-5 h-5 text-rose-400" /> : <Lucide.CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Header */}
      <header className="border-b border-slate-800/80 bg-[#0e1626]/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Lucide.Sparkles className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <span className="font-heading font-bold text-lg text-white tracking-tight flex items-center gap-2">
                alchemylow<span className="text-emerald-400 font-normal">.shop</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Supabase Live
                </span>
              </span>
              <p className="text-xs text-slate-400">Inteligência de Mercado & Backoffice de Low Tickets</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-slate-700/70 bg-slate-900/60">
              <span className={`w-2 h-2 rounded-full ${apiConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-slate-300">{apiConnected ? 'Supabase Online' : 'Conectando...'}</span>
            </div>

            <button 
              onClick={fetchData}
              disabled={loading}
              className="p-2 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title="Atualizar Dados"
            >
              <Lucide.RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Tab Navigation Menu */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 border-t border-slate-800/40 overflow-x-auto">
          <button
            onClick={() => setActiveTab('radar')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 whitespace-nowrap transition ${
              activeTab === 'radar'
                ? 'border-emerald-400 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lucide.TrendingUp className="w-4 h-4" />
            Radar de Tendências
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {trends.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('products')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 whitespace-nowrap transition ${
              activeTab === 'products'
                ? 'border-emerald-400 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lucide.Package className="w-4 h-4" />
            Kanban de Infoprodutos
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {products.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('meta_spy')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 whitespace-nowrap transition ${
              activeTab === 'meta_spy'
                ? 'border-emerald-400 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lucide.Eye className="w-4 h-4 text-teal-400" />
            Espião Meta Ads
            <span className="ml-1 px-1.5 py-0.5 text-[10px] rounded bg-teal-950 text-teal-300 border border-teal-800">
              NOVO
            </span>
          </button>

          <button
            onClick={() => setActiveTab('orders')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 whitespace-nowrap transition ${
              activeTab === 'orders'
                ? 'border-emerald-400 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lucide.DollarSign className="w-4 h-4" />
            Métricas & Vendas
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {metrics.total_orders}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 whitespace-nowrap transition ${
              activeTab === 'simulator'
                ? 'border-emerald-400 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lucide.Webhook className="w-4 h-4" />
            Simulador de Webhook
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 whitespace-nowrap transition ${
              activeTab === 'settings'
                ? 'border-emerald-400 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lucide.Settings className="w-4 h-4 text-amber-400" />
            Configurações & APIs
            {kiwifyConfig.configured ? (
              <span className="ml-1 w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            ) : null}
          </button>

          <button
            onClick={() => handleOpenAiAdsModal()}
            className="ml-auto my-auto flex items-center gap-1.5 py-1.5 px-3.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md shadow-purple-600/30 transition active:scale-95 whitespace-nowrap"
            title="Gerar anúncios a partir de ofertas concorrentes com IA e blindagem contra copyright"
          >
            <Lucide.Sparkles className="w-3.5 h-3.5 text-yellow-300" />
            <span>Criar Anúncios IA</span>
            <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-white/20 text-white uppercase tracking-wider">Anti-Plágio</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Metric Cards Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-card p-5 rounded-2xl border border-slate-800 hover:border-emerald-500/30 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Faturamento Bruto</span>
              <Lucide.DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-heading text-white">
              R$ {metrics.total_revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-400">{metrics.total_orders} compras registradas</div>
          </div>

          <div className="glass-card p-5 rounded-2xl border border-slate-800 hover:border-emerald-500/30 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Lucro Líquido Real</span>
              <Lucide.Coins className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-2xl font-bold font-heading text-emerald-400">
              R$ {metrics.net_revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-400">Pós-taxas Kiwify/Hotmart</div>
          </div>

          <div className="glass-card p-5 rounded-2xl border border-slate-800 hover:border-emerald-500/30 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Ticket Médio</span>
              <Lucide.ArrowUpRight className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-heading text-white">
              R$ {metrics.average_ticket.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-400">Padrão Low Ticket</div>
          </div>

          <div className="glass-card p-5 rounded-2xl border border-slate-800 hover:border-emerald-500/30 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Radar no Supabase</span>
              <Lucide.Flame className="w-4 h-4 text-orange-400" />
            </div>
            <div className="text-2xl font-bold font-heading text-white">
              {trends.length} <span className="text-xs font-normal text-slate-400">termos ativos</span>
            </div>
            <div className="mt-1 text-xs text-slate-400">Google Trends BR + Meta</div>
          </div>
        </div>

        {/* TAB 1: RADAR DE DEMANDA (MARKET INTELLIGENCE) */}
        {activeTab === 'radar' && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-heading font-bold text-white flex items-center gap-2">
                  <Lucide.TrendingUp className="w-5 h-5 text-emerald-400" />
                  Mineração de Tendências & Demandas Validadas
                </h2>
                <p className="text-sm text-slate-400">
                  Termos e palavras-chave monitoradas na tabela <code className="text-emerald-400 font-mono">market_trends</code> do Supabase.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300">
                  <Lucide.Search className="w-3.5 h-3.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Buscar termo..."
                    value={trendSearch}
                    onChange={(e) => setTrendSearch(e.target.value)}
                    className="bg-transparent text-white outline-none w-28 md:w-36 text-xs"
                  />
                </div>

                <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300">
                  <Lucide.Filter className="w-3.5 h-3.5 text-slate-400" />
                  <span>Nicho:</span>
                  <select 
                    value={trendNiche}
                    onChange={(e) => setTrendNiche(e.target.value)}
                    className="bg-transparent text-white outline-none cursor-pointer text-xs"
                  >
                    <option value="Todos" className="bg-slate-900">Todos</option>
                    <option value="Concursos" className="bg-slate-900">Concursos</option>
                    <option value="Finanças" className="bg-slate-900">Finanças</option>
                    <option value="Artesanato" className="bg-slate-900">Artesanato</option>
                    <option value="Saúde & Fitness" className="bg-slate-900">Saúde & Fitness</option>
                    <option value="Carreira & Habilidades" className="bg-slate-900">Carreira & Habilidades</option>
                  </select>
                </div>

                <button
                  onClick={() => handleMineTrends(trendNiche)}
                  disabled={miningLoading}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-600/20 transition active:scale-95 disabled:opacity-50"
                  title="Busca automatizada de termos com pytrends no Brasil"
                >
                  <Lucide.Flame className={`w-4 h-4 ${miningLoading ? 'animate-bounce text-amber-300' : 'text-amber-300'}`} />
                  {miningLoading ? 'Minerando no Google...' : 'Minerar Google Trends BR'}
                </button>
              </div>
            </div>

            <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/60 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      <th className="py-4 px-6">Palavra-Chave / Termo</th>
                      <th className="py-4 px-6">Nicho</th>
                      <th className="py-4 px-6">Interesse Relativo</th>
                      <th className="py-4 px-6">Crescimento</th>
                      <th className="py-4 px-6">Status</th>
                      <th className="py-4 px-6 text-right">Ações Estratégicas</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-sm">
                    {filteredTrends.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="text-center py-10 text-slate-400">
                          Nenhum termo encontrado. Clique em "Minerar Google Trends BR" para rodar a varredura ao vivo!
                        </td>
                      </tr>
                    ) : (
                      filteredTrends.map((item) => (
                        <tr key={item.id} className="hover:bg-slate-800/40 transition">
                          <td className="py-4 px-6 font-medium text-white">
                            <div className="flex items-center gap-2">
                              <Lucide.Flame className="w-4 h-4 text-orange-400 flex-shrink-0" />
                              <span className="font-semibold">{item.keyword}</span>
                            </div>
                            {item.raw_metadata?.rising_queries && item.raw_metadata.rising_queries.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1.5 ml-6">
                                {item.raw_metadata.rising_queries.map((rq, idx) => (
                                  <span key={idx} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700">
                                    ↗ {rq}
                                  </span>
                                ))}
                              </div>
                            )}
                          </td>
                          <td className="py-4 px-6 text-slate-300">
                            <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 border border-slate-700/60 text-slate-300">
                              {item.niche}
                            </span>
                          </td>
                          <td className="py-4 px-6">
                            <div className="flex items-center gap-2">
                              <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                                <div 
                                  className="bg-emerald-500 h-2 rounded-full" 
                                  style={{ width: `${item.relative_interest}%` }}
                                />
                              </div>
                              <span className="text-xs text-slate-400 font-semibold">{item.relative_interest}/100</span>
                            </div>
                          </td>
                          <td className="py-4 px-6">
                            <span className={`font-bold flex items-center gap-1 ${item.trend_growth_pct > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                              +{item.trend_growth_pct}%
                            </span>
                          </td>
                          <td className="py-4 px-6">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                              TREND_STATUS_LABELS[item.status]?.color || 'bg-slate-800 text-slate-300'
                            }`}>
                              {TREND_STATUS_LABELS[item.status]?.label || item.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-right space-x-2">
                            <button
                              onClick={() => handleInspectAds(item.keyword, item.niche, item.id)}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-teal-300 border border-slate-700 transition"
                              title="Espionar anúncios ativos desta palavra-chave no Facebook e Instagram"
                            >
                              <Lucide.Eye className="w-3.5 h-3.5" />
                              Espiar Anúncios
                            </button>
                            {products.some(p => p.trend_id === item.id) ? (
                              <button
                                onClick={() => {
                                  setActiveTab('products')
                                  showToast(`Visualizando produto no Kanban: "${item.keyword}"`)
                                }}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/50 transition active:scale-95 shadow-sm"
                                title="Este produto já foi gerado e está no Kanban. Clique para gerenciar."
                              >
                                <Lucide.PackageCheck className="w-3.5 h-3.5 text-indigo-400" />
                                Ver no Kanban
                              </button>
                            ) : (
                              <button
                                onClick={() => handleConvertToProduct(item)}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-700/20 transition active:scale-95"
                              >
                                <Lucide.Sparkles className="w-3.5 h-3.5" />
                                Criar Produto
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: BACKOFFICE DE PRODUTOS (KANBAN BOARD & LIST) */}
        {activeTab === 'products' && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-heading font-bold text-white flex items-center gap-2">
                  <Lucide.Package className="w-5 h-5 text-teal-400" />
                  Gestão do Ciclo de Vida dos Infoprodutos
                </h2>
                <p className="text-sm text-slate-400">
                  Mova os materiais entre as fases do Kanban conforme avançam na esteira de produção e tráfego.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center bg-slate-900 border border-slate-700/80 rounded-xl p-1 text-xs">
                  <button
                    onClick={() => setViewMode('kanban')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                      viewMode === 'kanban' ? 'bg-slate-800 text-emerald-400 font-semibold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Lucide.Kanban className="w-3.5 h-3.5" />
                    Kanban
                  </button>
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                      viewMode === 'grid' ? 'bg-slate-800 text-emerald-400 font-semibold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Lucide.LayoutGrid className="w-3.5 h-3.5" />
                    Grade
                  </button>
                </div>

                <button
                  onClick={handleSyncKiwify}
                  disabled={kiwifySyncLoading}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-600/50 shadow-lg shadow-emerald-950/30 transition"
                  title="Sincronizar produtos e links de checkout da Kiwify automaticamente"
                >
                  <Lucide.RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${kiwifySyncLoading ? 'animate-spin' : ''}`} />
                  {kiwifySyncLoading ? 'Sincronizando...' : 'Puxar da Kiwify'}
                </button>

                <button
                  onClick={() => handleOpenAiAdsModal()}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/30 transition active:scale-95"
                  title="Gerar anúncios a partir de ofertas concorrentes com IA e blindagem contra copyright"
                >
                  <Lucide.Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                  Gerar Anúncios IA
                </button>

                <button
                  onClick={() => setIsModalOpen(true)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 transition"
                >
                  <Lucide.Plus className="w-4 h-4" />
                  Novo Infoproduto
                </button>
              </div>
            </div>

            {/* KANBAN BOARD VIEW */}
            {viewMode === 'kanban' ? (
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 overflow-x-auto pb-4">
                {KANBAN_COLUMNS.map((column) => {
                  const colProducts = products.filter(p => p.status === column.id)
                  return (
                    <div 
                      key={column.id} 
                      className={`glass-card rounded-2xl border ${column.border} p-4 flex flex-col min-h-[500px] bg-slate-900/40`}
                    >
                      <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{column.icon}</span>
                          <span className="font-heading font-bold text-sm text-white">{column.label}</span>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                          {colProducts.length}
                        </span>
                      </div>

                      <div className="space-y-3 flex-1 overflow-y-auto">
                        {colProducts.length === 0 ? (
                          <div className="text-center py-8 text-slate-500 text-xs italic">
                            Nenhum item nesta etapa
                          </div>
                        ) : (
                          colProducts.map((prod) => (
                            <div 
                              key={prod.id} 
                              className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700/80 hover:border-slate-600 shadow-md transition flex flex-col justify-between"
                            >
                              <div>
                                <div className="flex items-center justify-between gap-2 mb-2">
                                  <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700">
                                    {prod.niche}
                                  </span>
                                  <span className="text-xs font-bold text-emerald-400 font-heading">
                                    R$ {prod.price.toFixed(2)}
                                  </span>
                                </div>

                                <h4 className="font-heading font-semibold text-sm text-white mb-1 leading-snug">
                                  {prod.title}
                                </h4>

                                <div className="text-[10px] font-mono text-emerald-400/80 mb-2 truncate">
                                  /{prod.slug}
                                </div>

                                {prod.delivery_url && (
                                  <div className="flex items-center gap-1 text-[11px] text-teal-300 bg-teal-950/40 px-2 py-1 rounded border border-teal-800/40 mb-2">
                                    <Lucide.DownloadCloud className="w-3 h-3 flex-shrink-0" />
                                    <span className="truncate">Entrega ativa</span>
                                  </div>
                                )}

                                <button
                                  onClick={() => handleInspectAds(prod.title, prod.niche)}
                                  className="w-full flex items-center justify-center gap-1.5 py-1 px-2 mb-1.5 text-[10px] font-semibold rounded bg-slate-900/80 text-teal-300 border border-teal-900/50 hover:bg-slate-900 transition"
                                >
                                  <Lucide.Eye className="w-3 h-3" />
                                  Espiar Anúncios Concorrentes
                                </button>

                                <button
                                  onClick={() => handleOpenAiAdsModal(prod)}
                                  className="w-full flex items-center justify-center gap-1.5 py-1 px-2 mb-2 text-[10px] font-semibold rounded bg-purple-950/70 hover:bg-purple-900/80 text-purple-200 border border-purple-800/60 transition shadow-sm"
                                  title="Gerar ou visualizar anúncios e copys com IA sem risco de copyright"
                                >
                                  <Lucide.Sparkles className="w-3 h-3 text-purple-400" />
                                  {prod.ad_copies ? '📢 Ver 3 Anúncios IA' : '⚡ Criar Anúncios com IA'}
                                </button>
                              </div>

                              <div className="border-t border-slate-700/60 pt-2.5 mt-2 flex items-center justify-between text-[11px] text-slate-400">
                                <div>
                                  Vendas: <span className="font-bold text-white">{prod.total_sales || 0}</span>
                                </div>

                                <div className="flex items-center gap-1">
                                  {column.id !== 'idea' && (
                                    <button
                                      onClick={() => {
                                        const prevIdx = KANBAN_COLUMNS.findIndex(c => c.id === column.id) - 1
                                        if (prevIdx >= 0) handleStatusChange(prod.id, KANBAN_COLUMNS[prevIdx].id)
                                      }}
                                      className="p-1 rounded bg-slate-700/60 hover:bg-slate-700 text-slate-300"
                                      title="Mover para etapa anterior"
                                    >
                                      ←
                                    </button>
                                  )}
                                  {column.id !== 'paused' && (
                                    <button
                                      onClick={() => {
                                        const nextIdx = KANBAN_COLUMNS.findIndex(c => c.id === column.id) + 1
                                        if (nextIdx < KANBAN_COLUMNS.length) handleStatusChange(prod.id, KANBAN_COLUMNS[nextIdx].id)
                                      }}
                                      className="p-1 rounded bg-emerald-700/60 hover:bg-emerald-600 text-white font-bold"
                                      title="Avançar etapa"
                                    >
                                      →
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleDeleteProduct(prod.id)}
                                    className="p-1 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300"
                                    title="Excluir"
                                  >
                                    <Lucide.Trash2 className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {products.map((prod) => (
                  <div key={prod.id} className="glass-card rounded-2xl border border-slate-800 p-6 flex flex-col justify-between hover:border-slate-700 transition">
                    <div>
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                          {prod.niche}
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                          KANBAN_COLUMNS.find(c => c.id === prod.status)?.badge || 'bg-slate-800 text-slate-300'
                        }`}>
                          {KANBAN_COLUMNS.find(c => c.id === prod.status)?.label || prod.status}
                        </span>
                      </div>

                      <h3 className="font-heading font-bold text-lg text-white mb-1 leading-snug">
                        {prod.title}
                      </h3>
                      
                      <div className="text-[11px] font-mono text-emerald-400/80 mb-3 truncate">
                        /{prod.slug}
                      </div>

                      <p className="text-xs text-slate-400 mb-4 line-clamp-2">
                        {prod.description || 'Sem descrição cadastrada.'}
                      </p>

                      {prod.delivery_url && (
                        <div className="flex items-center gap-1.5 text-xs text-teal-300 bg-teal-950/40 p-2 rounded-lg border border-teal-800/40 mb-4">
                          <Lucide.DownloadCloud className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="truncate">Entrega: {prod.delivery_url}</span>
                        </div>
                      )}
                    </div>

                    <div className="border-t border-slate-800/80 pt-4 space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Preço de Venda:</span>
                        <span className="font-bold text-emerald-400 font-heading text-base">
                          R$ {prod.price.toFixed(2)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-400 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                        <div>
                          Vendas: <span className="font-semibold text-white">{prod.total_sales || 0}</span>
                        </div>
                        <div>
                          Receita: <span className="font-semibold text-emerald-400">R$ {(prod.total_revenue || 0).toFixed(2)}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between gap-1 pt-1">
                        <span className="text-[11px] text-slate-400">Mudar status:</span>
                        <div className="flex gap-1">
                          {['idea', 'in_production', 'ready', 'active'].map((st) => (
                            <button
                              key={st}
                              onClick={() => handleStatusChange(prod.id, st)}
                              disabled={prod.status === st}
                              className={`px-2 py-0.5 text-[10px] rounded font-medium transition ${
                                prod.status === st 
                                  ? 'bg-slate-700 text-slate-300 opacity-50 cursor-default'
                                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                              }`}
                            >
                              {KANBAN_COLUMNS.find(c => c.id === st)?.label.split(' ')[0] || st}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ESPIÃO DE ANÚNCIOS (META ADS SPY) */}
        {activeTab === 'meta_spy' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-heading font-bold text-white flex items-center gap-2">
                <Lucide.Eye className="w-5 h-5 text-teal-400" />
                Espião de Anúncios da Meta (Facebook & Instagram)
              </h2>
              <p className="text-sm text-slate-400">
                Pesquise qualquer palavra-chave ou produto para identificar criativos concorrentes, preços praticados e saturação no Brasil.
              </p>
            </div>

            {/* Search form */}
            <form onSubmit={handleCustomSpySearch} className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-300 mb-1">Palavra-Chave ou Tipo de Infoproduto</label>
                <div className="relative">
                  <Lucide.Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    placeholder="Ex: apostila concurso caixa, planner financeiro notion, receita amigurumi..."
                    value={customSpyQuery}
                    onChange={(e) => setCustomSpyQuery(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="w-full md:w-56">
                <label className="block text-xs font-semibold text-slate-300 mb-1">Nicho</label>
                <select
                  value={customSpyNiche}
                  onChange={(e) => setCustomSpyNiche(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none cursor-pointer"
                >
                  <option value="Concursos">Concursos & OAB</option>
                  <option value="Finanças">Finanças & Investimentos</option>
                  <option value="Artesanato">Artesanato & Hobbies</option>
                  <option value="Saúde & Fitness">Saúde & Fitness</option>
                  <option value="Carreira & Habilidades">Carreira & Habilidades</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={customSpyLoading}
                  className="w-full md:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-semibold text-sm shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2"
                >
                  <Lucide.Eye className={`w-4 h-4 ${customSpyLoading ? 'animate-spin' : ''}`} />
                  {customSpyLoading ? 'Analisando...' : 'Espionar Anúncios'}
                </button>
              </div>
            </form>

            {/* Results Display */}
            {customSpyResult && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="glass-card p-6 rounded-2xl border border-slate-800 lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                      <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">{customSpyResult.niche}</span>
                      <h3 className="font-heading font-bold text-xl text-white mt-0.5">{customSpyResult.keyword}</h3>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-700">
                      {customSpyResult.competition_level}
                    </span>
                  </div>

                  <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    💡 <strong className="text-white">Diagnóstico Estratégico:</strong> {customSpyResult.verdict}
                  </p>

                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ângulos de Copy Mais Eficazes:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {customSpyResult.recommended_angles?.map((angle, idx) => (
                        <div key={idx} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-teal-300 flex items-center gap-2">
                          <Lucide.Target className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                          <span>{angle}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Quick actions box */}
                <div className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Ticket Médio Praticado</h4>
                    <div className="text-2xl font-bold font-heading text-emerald-400 mb-4">
                      {customSpyResult.recommended_ticket}
                    </div>

                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Anúncios Estimados</h4>
                    <div className="text-lg font-bold text-white mb-6">
                      ~{customSpyResult.active_ads_count} campanhas ativas no BR
                    </div>
                  </div>

                  <a
                    href={customSpyResult.ads_library_url}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs text-center shadow-lg shadow-blue-600/30 transition flex items-center justify-center gap-2"
                  >
                    <span>Abrir na Meta Ads Library (BR)</span>
                    <Lucide.ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: MÉTRICAS & VENDAS */}
        {activeTab === 'orders' && (
          <div className="space-y-8">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-heading font-bold text-white flex items-center gap-2">
                  <Lucide.DollarSign className="w-5 h-5 text-emerald-400" />
                  Métricas de Vendas & Ingestão em Tempo Real
                </h2>
                <p className="text-sm text-slate-400">
                  Transações recebidas via Webhook gravadas diretamente no seu PostgreSQL do Supabase.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleClearTestOrders}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-rose-300 border border-slate-700 transition"
                  title="Apaga apenas os pedidos iniciados com TEST- ou SIM-"
                >
                  <Lucide.Trash2 className="w-3.5 h-3.5" />
                  Limpar Pedidos de Teste
                </button>
              </div>
            </div>

            {/* CHARTS ROW */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="glass-card p-6 rounded-2xl border border-slate-800 lg:col-span-2">
                <h3 className="font-heading font-bold text-base text-white mb-1 flex items-center gap-2">
                  <Lucide.BarChart2 className="w-4 h-4 text-emerald-400" />
                  Evolução do Faturamento (Últimos 14 Dias)
                </h3>
                <p className="text-xs text-slate-400 mb-6">Receita bruta (R$) e líquida computadas</p>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="grossGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#22c55e" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                        formatter={(val) => [`R$ ${Number(val).toFixed(2)}`, 'Valor']}
                      />
                      <Area type="monotone" dataKey="gross" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#grossGradient)" name="Faturamento Bruto" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
                <div>
                  <h3 className="font-heading font-bold text-base text-white mb-1">
                    Vendas por Plataforma
                  </h3>
                  <p className="text-xs text-slate-400 mb-6">Checkouts integrados via Webhook</p>

                  <div className="h-52 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={platformChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                        <YAxis stroke="#64748b" fontSize={10} allowDecimals={false} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                        />
                        <Bar dataKey="orders" radius={[6, 6, 0, 0]} name="Pedidos">
                          {platformChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-800 text-xs text-slate-400 flex justify-between">
                  <span>Total confirmado:</span>
                  <span className="font-bold text-white">{metrics.total_orders} pedidos</span>
                </div>
              </div>
            </div>

            {/* TRANSACTIONS TABLE */}
            <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
              <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
                <span className="font-heading font-bold text-sm text-white">Últimas Transações Recebidas</span>
                <span className="text-xs text-slate-400 font-mono">Tabela orders (Supabase)</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/40 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      <th className="py-4 px-6">ID da Transação</th>
                      <th className="py-4 px-6">Infoproduto</th>
                      <th className="py-4 px-6">Cliente</th>
                      <th className="py-4 px-6">Plataforma</th>
                      <th className="py-4 px-6">Valor Bruto</th>
                      <th className="py-4 px-6">Valor Líquido</th>
                      <th className="py-4 px-6">Status</th>
                      <th className="py-4 px-6">Data</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-sm">
                    {orders.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="text-center py-8 text-slate-400">
                          Nenhum pedido recebido ainda. Use a aba "Simulador de Webhook" para testar!
                        </td>
                      </tr>
                    ) : (
                      orders.map((ord) => (
                        <tr key={ord.id} className="hover:bg-slate-800/40 transition">
                          <td className="py-4 px-6 font-mono text-xs text-slate-300">
                            {ord.external_order_id}
                          </td>
                          <td className="py-4 px-6 font-medium text-white">
                            {ord.product_title || 'Infoproduto'}
                          </td>
                          <td className="py-4 px-6 text-slate-300 text-xs">
                            <div className="font-semibold text-slate-200">{ord.customer_name || 'Cliente'}</div>
                            <div className="text-slate-500">{ord.customer_email || '—'}</div>
                          </td>
                          <td className="py-4 px-6">
                            <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-800 text-teal-300 border border-slate-700 uppercase">
                              {ord.platform}
                            </span>
                          </td>
                          <td className="py-4 px-6 font-bold text-white">
                            R$ {ord.gross_amount.toFixed(2)}
                          </td>
                          <td className="py-4 px-6 font-bold text-emerald-400">
                            R$ {(ord.net_amount || ord.gross_amount * 0.9).toFixed(2)}
                          </td>
                          <td className="py-4 px-6">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                              ord.status === 'paid' ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' : 'bg-amber-950 text-amber-300'
                            }`}>
                              {ord.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-xs text-slate-400">
                            {ord.created_at ? new Date(ord.created_at).toLocaleString('pt-BR') : 'Agora'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: SIMULADOR DE WEBHOOK & DOCS */}
        {activeTab === 'simulator' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="glass-card p-6 rounded-2xl border border-slate-800">
              <h2 className="text-lg font-heading font-bold text-white flex items-center gap-2 mb-2">
                <Lucide.Webhook className="w-5 h-5 text-emerald-400" />
                Simulador de Eventos de Compra
              </h2>
              <p className="text-xs text-slate-400 mb-6">
                Teste o pipeline de webhooks enviando compras simuladas para a Kiwify, Hotmart, Eduzz ou Braip.
              </p>

              <form onSubmit={handleSimulateWebhook} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Plataforma</label>
                  <select
                    value={simForm.platform}
                    onChange={(e) => setSimForm({ ...simForm, platform: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                  >
                    <option value="kiwify">Kiwify</option>
                    <option value="hotmart">Hotmart</option>
                    <option value="eduzz">Eduzz</option>
                    <option value="braip">Braip</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Infoproduto</label>
                  <select
                    value={simForm.product_title}
                    onChange={(e) => setSimForm({ ...simForm, product_title: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                  >
                    {products.map((p) => (
                      <option key={p.id} value={p.title}>{p.title} (R$ {p.price.toFixed(2)})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Valor Bruto da Venda (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={simForm.amount}
                    onChange={(e) => setSimForm({ ...simForm, amount: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Nome do Comprador</label>
                    <input
                      type="text"
                      value={simForm.customer_name}
                      onChange={(e) => setSimForm({ ...simForm, customer_name: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">E-mail do Comprador</label>
                    <input
                      type="email"
                      value={simForm.customer_email}
                      onChange={(e) => setSimForm({ ...simForm, customer_email: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2 mt-4"
                >
                  <Lucide.Send className="w-4 h-4" />
                  Disparar Webhook para o Supabase
                </button>
              </form>
            </div>

            <div className="space-y-6">
              <div className="glass-card p-6 rounded-2xl border border-slate-800">
                <h3 className="text-base font-heading font-bold text-white flex items-center gap-2 mb-2">
                  <Lucide.ShieldCheck className="w-5 h-5 text-teal-400" />
                  Endpoint Real de Produção
                </h3>
                <p className="text-xs text-slate-400 mb-4">
                  Cadastre esta URL nas configurações de Webhook das suas plataformas (Kiwify, Hotmart, Eduzz, Braip):
                </p>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400 break-all select-all flex items-center justify-between gap-2 mb-4">
                  <span>POST https://alchemylow.shop/api/webhooks/order</span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  As transações são processadas com idempotência (evitando duplicar pedidos), calculando o lucro líquido real e salvando na tabela <code className="text-emerald-400 font-mono">orders</code> do Supabase.
                </p>
              </div>

              {simResponse && (
                <div className="glass-card p-6 rounded-2xl border border-emerald-800/60 bg-emerald-950/20">
                  <h4 className="text-xs font-semibold uppercase text-emerald-400 tracking-wider mb-2">
                    Retorno da Ingestão no Supabase:
                  </h4>
                  <pre className="bg-slate-950 p-4 rounded-xl text-xs text-slate-200 overflow-x-auto font-mono">
                    {JSON.stringify(simResponse, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* SETTINGS & API INTEGRATIONS TAB */}
        {activeTab === 'settings' && (
          <div className="space-y-8 animate-fadeIn">
            {/* Header Description */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-heading font-bold text-white flex items-center gap-2">
                  <Lucide.Cpu className="w-5 h-5 text-emerald-400" />
                  Integrações de API e Conexão de Checkouts
                </h2>
                <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                  Configure suas credenciais para que a plataforma sincronize automaticamente seus produtos, puxe links de checkout oficiais e processe vendas sem necessidade de cadastros manuais.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Status Geral:</span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  API Pronta
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* KIWIFY API CARD */}
              <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-bold text-emerald-400 text-lg">
                        K
                      </div>
                      <div>
                        <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
                          Kiwify (API Oficial OAuth 2.0)
                        </h3>
                        <p className="text-xs text-slate-400">Sincronização direta de produtos e checkouts</p>
                      </div>
                    </div>

                    {kiwifyConfig.configured ? (
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1.5">
                        <Lucide.CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        Conectado
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1.5">
                        <Lucide.AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                        Aguardando Chaves
                      </span>
                    )}
                  </div>

                  <form onSubmit={handleSaveKiwify} className="space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                        <span>Client ID (ID da API Key da Kiwify) *</span>
                        <span className="text-[10px] text-slate-500">Exibido na tela de API da Kiwify</span>
                      </label>
                      <input
                        type="text"
                        placeholder="Ex: 8a7b9c6d-5e4f-3a2b-1c0d-..."
                        value={kiwifyConfig.client_id}
                        onChange={(e) => setKiwifyConfig({ ...kiwifyConfig, client_id: e.target.value })}
                        className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                        <span>Client Secret (Chave Secreta) *</span>
                        <button
                          type="button"
                          onClick={() => setShowKiwifySecret(!showKiwifySecret)}
                          className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                        >
                          {showKiwifySecret ? <Lucide.EyeOff className="w-3 h-3" /> : <Lucide.Eye className="w-3 h-3" />}
                          {showKiwifySecret ? 'Ocultar' : 'Mostrar'}
                        </button>
                      </label>
                      <input
                        type={showKiwifySecret ? "text" : "password"}
                        placeholder="Cole o Client Secret (64 caracteres)..."
                        value={kiwifyConfig.client_secret}
                        onChange={(e) => setKiwifyConfig({ ...kiwifyConfig, client_secret: e.target.value })}
                        className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                        <span>Account ID (Opcional)</span>
                        <span className="text-[10px] text-slate-500">Geralmente idêntico ao Client ID</span>
                      </label>
                      <input
                        type="text"
                        placeholder="Opcional (preenchido automaticamente)"
                        value={kiwifyConfig.account_id}
                        onChange={(e) => setKiwifyConfig({ ...kiwifyConfig, account_id: e.target.value })}
                        className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono transition"
                      />
                    </div>

                    <div className="pt-2 flex flex-wrap items-center gap-3">
                      <button
                        type="submit"
                        disabled={kiwifySaveLoading}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-600/30 transition"
                      >
                        <Lucide.Save className="w-4 h-4" />
                        {kiwifySaveLoading ? 'Salvando...' : 'Salvar Credenciais'}
                      </button>

                      <button
                        type="button"
                        onClick={handleTestKiwify}
                        disabled={kiwifyTestLoading}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
                      >
                        <Lucide.Plug className={`w-4 h-4 ${kiwifyTestLoading ? 'animate-spin' : 'text-emerald-400'}`} />
                        {kiwifyTestLoading ? 'Testando...' : 'Testar Conexão'}
                      </button>

                      <button
                        type="button"
                        onClick={handleSyncKiwify}
                        disabled={kiwifySyncLoading}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-600/40 text-xs font-semibold ml-auto transition"
                      >
                        <Lucide.RefreshCw className={`w-4 h-4 text-emerald-400 ${kiwifySyncLoading ? 'animate-spin' : ''}`} />
                        {kiwifySyncLoading ? 'Sincronizando...' : 'Sincronizar Produtos Agora'}
                      </button>
                    </div>
                  </form>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>As credenciais são gravadas de forma criptografada na tabela de configurações.</span>
                  {kiwifyConfig.updated_at && (
                    <span className="text-slate-500">Última atualização: {new Date(kiwifyConfig.updated_at).toLocaleDateString('pt-BR')}</span>
                  )}
                </div>
              </div>

              {/* TUTORIAL & HELP CARD */}
              <div className="space-y-6">
                <div className="glass-card p-6 rounded-2xl border border-slate-800 bg-slate-900/60">
                  <h4 className="font-heading font-bold text-sm text-white flex items-center gap-2 mb-3">
                    <Lucide.HelpCircle className="w-4 h-4 text-emerald-400" />
                    Onde achar na Kiwify:
                  </h4>
                  <ol className="space-y-2.5 text-xs text-slate-300 leading-relaxed list-decimal list-inside">
                    <li>Acesse seu painel em <strong className="text-white">dashboard.kiwify.com.br</strong></li>
                    <li>No menu lateral esquerdo, clique em <strong className="text-emerald-400">Apps ➔ API</strong></li>
                    <li>Clique no botão verde <strong className="text-white">Criar API Key</strong></li>
                    <li>Copie o <strong className="text-white">Client ID</strong> e o <strong className="text-white">Client Secret</strong></li>
                    <li>Cole aqui nos campos e clique em Salvar!</li>
                  </ol>
                </div>

                <div className="glass-card p-6 rounded-2xl border border-slate-800">
                  <h4 className="font-heading font-bold text-sm text-white flex items-center gap-2 mb-2">
                    <Lucide.ShieldCheck className="w-4 h-4 text-teal-400" />
                    Webhooks das Plataformas
                  </h4>
                  <p className="text-xs text-slate-400 mb-3">
                    URL universal para Kiwify, Hotmart, Eduzz e Braip:
                  </p>
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-emerald-400 break-all select-all">
                    https://alchemylow.shop/api/webhooks/order
                  </div>
                </div>

                {/* AI ENGINE & COPYRIGHT SHIELD CARD */}
                <div className="glass-card p-6 rounded-2xl border border-purple-900/40 bg-gradient-to-b from-purple-950/20 to-slate-900/60 shadow-xl">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-heading font-bold text-sm text-white flex items-center gap-2">
                      <Lucide.Sparkles className="w-4 h-4 text-purple-400" />
                      Motor de IA & Anti-Copyright
                    </h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-950 text-purple-300 border border-purple-800">
                      {aiSettings.active_engine}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                    O gerador já inclui o <strong className="text-white">Motor Neural Nativo</strong> (100% gratuito e pronto).
                    Para usar modelos LLM avançados (<strong className="text-purple-300">GPT-4o-mini</strong> ou <strong className="text-purple-300">Gemini 1.5</strong>), adicione sua chave abaixo:
                  </p>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 mb-1 flex items-center justify-between">
                        <span>OpenAI API Key (Opcional)</span>
                        {aiSettings.has_openai_key && <span className="text-[10px] text-emerald-400 font-bold">✓ Conectada</span>}
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="password"
                          placeholder={aiSettings.has_openai_key ? "••••••••••••••••••••••••" : "sk-..."}
                          value={openaiKeyInput}
                          onChange={(e) => setOpenaiKeyInput(e.target.value)}
                          className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 font-mono focus:border-purple-500 focus:outline-none"
                        />
                        <button
                          type="button"
                          disabled={aiKeySaveLoading || !openaiKeyInput}
                          onClick={() => handleSaveAiKey('openai', openaiKeyInput)}
                          className="px-3 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold text-xs transition"
                        >
                          Salvar
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 mb-1 flex items-center justify-between">
                        <span>Google Gemini API Key (Opcional)</span>
                        {aiSettings.has_gemini_key && <span className="text-[10px] text-emerald-400 font-bold">✓ Conectada</span>}
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="password"
                          placeholder={aiSettings.has_gemini_key ? "••••••••••••••••••••••••" : "AIzaSy..."}
                          value={geminiKeyInput}
                          onChange={(e) => setGeminiKeyInput(e.target.value)}
                          className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 font-mono focus:border-purple-500 focus:outline-none"
                        />
                        <button
                          type="button"
                          disabled={aiKeySaveLoading || !geminiKeyInput}
                          onClick={() => handleSaveAiKey('gemini', geminiKeyInput)}
                          className="px-3 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold text-xs transition"
                        >
                          Salvar
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* MODAL: ESPIÃO DE ANÚNCIOS (POPUP) */}
      {spyModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-xl w-full p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Lucide.Eye className="w-5 h-5 text-teal-400" />
                <h3 className="font-heading font-bold text-lg text-white">Espião de Anúncios na Meta</h3>
              </div>
              <button 
                onClick={() => setSpyModal({ isOpen: false, loading: false, data: null })}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            {spyModal.loading ? (
              <div className="py-12 text-center space-y-3">
                <Lucide.RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto" />
                <p className="text-xs text-slate-400">Consultando Biblioteca de Anúncios da Meta no Brasil...</p>
              </div>
            ) : spyModal.data ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-base">{spyModal.data.keyword}</span>
                  <span className="px-3 py-0.5 rounded-full text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-700">
                    {spyModal.data.competition_level}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  💡 <strong className="text-white">Diagnóstico:</strong> {spyModal.data.verdict}
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block mb-1">Ticket Médio Sugerido</span>
                    <span className="font-bold text-emerald-400 text-sm font-heading">{spyModal.data.recommended_ticket}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block mb-1">Campanhas Ativas</span>
                    <span className="font-bold text-white text-sm">~{spyModal.data.active_ads_count} anunciantes</span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-400">Ângulos de Copy Sugeridos:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {spyModal.data.recommended_angles?.map((angle, idx) => (
                      <span key={idx} className="text-xs px-2.5 py-1 rounded-lg bg-slate-900 text-teal-300 border border-slate-800">
                        🎯 {angle}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-2 flex flex-col sm:flex-row gap-2">
                  <a
                    href={spyModal.data.ads_library_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs text-center transition flex items-center justify-center gap-1.5"
                  >
                    <span>Ver na Meta Ads Library</span>
                    <Lucide.ExternalLink className="w-3.5 h-3.5 text-blue-400" />
                  </a>

                  <button
                    onClick={() => {
                      const kw = spyModal.data.keyword
                      const niche = spyModal.data.niche
                      setSpyModal({ isOpen: false, loading: false, data: null })
                      handleOpenAiAdsModal({ title: kw, niche: niche, price: 27.0 }, `Oferta de referência no nicho de ${niche} para o termo "${kw}".`)
                    }}
                    className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs text-center shadow-lg shadow-purple-600/30 transition flex items-center justify-center gap-1.5 active:scale-95"
                  >
                    <Lucide.Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                    <span>Gerar Anúncios sem Copyright</span>
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Modal: Novo Infoproduto */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-lg w-full p-6 rounded-2xl border border-slate-700 shadow-2xl">
            <h3 className="font-heading font-bold text-lg text-white mb-1">Cadastrar Infoproduto</h3>
            <p className="text-xs text-slate-400 mb-4">Adicione um novo material ao catálogo do Supabase.</p>

            <form onSubmit={handleCreateProduct} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Título do Infoproduto</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Apostila Concurso Banco do Brasil 2026"
                  value={newProd.title}
                  onChange={(e) => setNewProd({ ...newProd, title: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Descrição</label>
                <textarea
                  rows="2"
                  placeholder="Resumo, proposta de valor e diferenciais..."
                  value={newProd.description}
                  onChange={(e) => setNewProd({ ...newProd, description: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Nicho</label>
                  <input
                    type="text"
                    value={newProd.niche}
                    onChange={(e) => setNewProd({ ...newProd, niche: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Preço de Venda (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newProd.price}
                    onChange={(e) => setNewProd({ ...newProd, price: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Link de Entrega do Material (PDF / Drive)</label>
                <input
                  type="url"
                  placeholder="https://drive.google.com/... ou link de download"
                  value={newProd.delivery_url}
                  onChange={(e) => setNewProd({ ...newProd, delivery_url: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Status Inicial</label>
                <select
                  value={newProd.status}
                  onChange={(e) => setNewProd({ ...newProd, status: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
                >
                  <option value="idea">💡 Ideia (Rascunho)</option>
                  <option value="in_production">✍️ Em Produção (Escrevendo)</option>
                  <option value="ready">🚀 Pronto p/ Tráfego</option>
                  <option value="active">💰 Ativo (Vendendo)</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 transition"
                >
                  Salvar Produto no Supabase
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* MODAL: GERADOR DE ANÚNCIOS COM IA (ANTI-COPYRIGHT) */}
      {aiAdsModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="glass-card max-w-4xl w-full p-6 sm:p-7 rounded-3xl border border-purple-700/50 shadow-2xl bg-slate-900/95 space-y-5 my-auto max-h-[92vh] flex flex-col">
            
            {/* Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-purple-950/80 border border-purple-700/50 text-purple-300">
                    <Lucide.Sparkles className="w-5 h-5 text-yellow-300 animate-pulse" />
                  </div>
                  <div>
                    <h3 className="font-heading font-bold text-lg sm:text-xl text-white flex items-center gap-2">
                      Gerador de Anúncios com IA (Anti-Copyright)
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Crie campanhas de alta conversão para o Meta Ads reescrevendo ofertas de concorrentes sem risco de plágio.
                    </p>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => setAiAdsModal(prev => ({ ...prev, isOpen: false }))}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Body (Scrollable) */}
            <div className="space-y-5 overflow-y-auto pr-1 flex-1">
              
              {/* Product & Inputs Form */}
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Infoproduto de Destino:
                    </label>
                    <select
                      value={aiAdsModal.product?.id || ''}
                      onChange={(e) => {
                        const selectedId = parseInt(e.target.value)
                        const prod = products.find(p => p.id === selectedId) || null
                        setAiAdsModal(prev => ({
                          ...prev,
                          product: prod,
                          customTitle: prod?.title || prev.customTitle,
                          result: prod?.ad_copies || prev.result
                        }))
                      }}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
                    >
                      <option value="">-- Usar Título Personalizado / Sem Vínculo --</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.title} (R$ {p.price.toFixed(2)} - {p.niche})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Preço da Oferta (R$):
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aiAdsModal.product?.price || 27.00}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 27.00
                        if (aiAdsModal.product) {
                          setAiAdsModal(prev => ({
                            ...prev,
                            product: { ...prev.product, price: val }
                          }))
                        }
                      }}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
                    />
                  </div>
                </div>

                {!aiAdsModal.product && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Título do Produto / Assunto:
                    </label>
                    <input
                      type="text"
                      placeholder="Ex: Guia Prático: Como Sair das Dívidas em 2026"
                      value={aiAdsModal.customTitle}
                      onChange={(e) => setAiAdsModal(prev => ({ ...prev, customTitle: e.target.value }))}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center justify-between">
                    <span>Oferta ou Texto do Concorrente (Referência para Reformulação):</span>
                    <span className="text-[10px] text-purple-300 font-mono">Modificação Anti-Copyright Ativa</span>
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Cole aqui o texto do anúncio concorrente que você viu na Biblioteca da Meta, a promessa da página de vendas ou o gancho... A IA irá desconstruir a dor e criar 3 anúncios 100% inéditos e seguros para o Meta Ads."
                    value={aiAdsModal.competitorOffer}
                    onChange={(e) => setAiAdsModal(prev => ({ ...prev, competitorOffer: e.target.value }))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none leading-relaxed"
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Lucide.ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>Compliance Meta Ads: <strong className="text-white">Sem promessas proibidas</strong></span>
                  </div>

                  <button
                    type="button"
                    disabled={aiAdsModal.loading}
                    onClick={handleGenerateAiAds}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-purple-600/30 transition active:scale-95 disabled:opacity-50 ml-auto"
                  >
                    <Lucide.Sparkles className={`w-4 h-4 text-yellow-300 ${aiAdsModal.loading ? 'animate-spin' : ''}`} />
                    {aiAdsModal.loading ? 'Gerando Anúncios com IA...' : 'Gerar 3 Anúncios Anti-Copyright'}
                  </button>
                </div>
              </div>

              {/* Loading State */}
              {aiAdsModal.loading && (
                <div className="py-12 text-center space-y-3">
                  <Lucide.RefreshCw className="w-8 h-8 text-purple-400 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-white">Analisando oferta e desconstruindo padrões de copyright...</p>
                  <p className="text-xs text-slate-400">Criando ganchos magnéticos, legendas completas e roteiros de Stories.</p>
                </div>
              )}

              {/* Generated Result Section */}
              {!aiAdsModal.loading && aiAdsModal.result && (
                <div className="space-y-4">
                  
                  {/* Copyright Shield Banner */}
                  <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-purple-950/40 to-slate-900 border border-emerald-500/40 text-xs text-slate-300 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-emerald-400 font-bold">
                        <Lucide.ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span>Escudo Anti-Plágio & Proteção de Copyright</span>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700">
                        ✓ 100% Inédito & Seguro
                      </span>
                    </div>
                    <p className="text-slate-300 leading-relaxed text-[11px]">
                      {aiAdsModal.result.copyright_shield?.analyzed_elements}
                    </p>
                    <div className="text-[10px] text-slate-400 border-t border-slate-800/80 pt-2 whitespace-pre-line">
                      {aiAdsModal.result.copyright_shield?.modifications_applied}
                    </div>
                  </div>

                  {/* Variations Tabs */}
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
                    {aiAdsModal.result.variations?.map((variant, idx) => (
                      <button
                        key={variant.id || idx}
                        onClick={() => setAiAdsModal(prev => ({ ...prev, activeAngleTab: idx }))}
                        className={`px-3 py-2 rounded-xl text-xs font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                          aiAdsModal.activeAngleTab === idx
                            ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                            : 'bg-slate-800/80 text-slate-400 hover:text-white'
                        }`}
                      >
                        <span>{variant.angle_name?.split(':')[0] || `Variação ${idx + 1}`}</span>
                      </button>
                    ))}
                  </div>

                  {/* Active Variation Content */}
                  {(() => {
                    const activeVariant = aiAdsModal.result.variations?.[aiAdsModal.activeAngleTab] || aiAdsModal.result.variations?.[0]
                    if (!activeVariant) return null
                    return (
                      <div className="space-y-4 p-5 rounded-2xl bg-slate-950/90 border border-slate-800">
                        <div className="flex items-center justify-between">
                          <h4 className="font-heading font-bold text-sm text-purple-300 flex items-center gap-2">
                            <span>🎯 {activeVariant.angle_name}</span>
                          </h4>
                          <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            CTA: {activeVariant.cta_button || 'Saiba Mais'}
                          </span>
                        </div>

                        {/* Hooks */}
                        <div className="space-y-1.5">
                          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                            Ganchos de Imagem / Topo do Criativo:
                          </span>
                          <div className="grid grid-cols-1 gap-2">
                            {activeVariant.hooks?.map((hook, hIdx) => (
                              <div key={hIdx} className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white">
                                <span>"{hook}"</span>
                                <button
                                  type="button"
                                  onClick={() => handleCopyText(hook, 'Gancho')}
                                  className="text-[10px] text-purple-400 hover:text-purple-300 flex items-center gap-1 flex-shrink-0"
                                >
                                  <Lucide.Copy className="w-3 h-3" />
                                  Copiar
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Primary Text (Feed Copy) */}
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                              Texto Principal (Legenda do Anúncio):
                            </span>
                            <button
                              type="button"
                              onClick={() => handleCopyText(activeVariant.primary_text, 'Legenda')}
                              className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
                            >
                              <Lucide.Copy className="w-3.5 h-3.5" />
                              Copiar Legenda Completa
                            </button>
                          </div>
                          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-line font-sans select-all">
                            {activeVariant.primary_text}
                          </div>
                        </div>

                        {/* Stories Script */}
                        {activeVariant.stories_script && (
                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                                Roteiro para Stories / Vídeo Curto (15s):
                              </span>
                              <button
                                type="button"
                                onClick={() => handleCopyText(activeVariant.stories_script, 'Roteiro de Stories')}
                                className="text-xs text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1"
                              >
                                <Lucide.Copy className="w-3.5 h-3.5" />
                                Copiar Roteiro
                              </button>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                              {activeVariant.stories_script}
                            </div>
                          </div>
                        )}

                        {/* Creative Concept */}
                        {activeVariant.creative_concept && (
                          <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-800/40 text-xs text-slate-300">
                            <strong className="text-purple-300 block mb-1">💡 Sugestão Visual do Criativo:</strong>
                            {activeVariant.creative_concept}
                          </div>
                        )}
                      </div>
                    )
                  })()}

                  {/* Modal Footer Actions */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
                    <span className="text-xs text-slate-400">
                      Anúncios prontos para rodar no Gerenciador da Meta.
                    </span>

                    <div className="flex items-center gap-2">
                      {aiAdsModal.product?.id && (
                        <button
                          type="button"
                          disabled={aiAdsModal.saveLoading}
                          onClick={() => handleSaveAdsToProduct(aiAdsModal.product.id, aiAdsModal.result)}
                          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/30 transition active:scale-95 disabled:opacity-50"
                        >
                          <Lucide.Save className="w-3.5 h-3.5" />
                          {aiAdsModal.saveLoading ? 'Salvando...' : 'Salvar no Produto'}
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => setAiAdsModal(prev => ({ ...prev, isOpen: false }))}
                        className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      >
                        Fechar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
