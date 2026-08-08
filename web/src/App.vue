<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  Activity,
  ArrowRight,
  BookOpen,
  Braces,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Database,
  FileCode2,
  Filter,
  Layers3,
  RefreshCw,
  Search,
  Sparkles,
  TrendingUp,
} from '@lucide/vue'

import { checkHealth, searchKnowledge } from './api'

const categories = [
  { value: '', label: '全部知识', short: '全部' },
  { value: 'fixed_income', label: '固收知识', short: '固收' },
  { value: 'indicator', label: '指标因子', short: '指标' },
  { value: 'sdk', label: '量化 SDK', short: 'SDK' },
  { value: 'strategy', label: '策略案例', short: '策略' },
  { value: 'platform', label: '平台规范', short: '规范' },
]

const examples = [
  {
    title: 'T 和 TL 有什么区别？',
    description: '验证固收业务知识检索',
    category: 'fixed_income',
    icon: TrendingUp,
  },
  {
    title: 'MA 指标如何计算？',
    description: '验证结构化指标知识',
    category: 'indicator',
    icon: Activity,
  },
  {
    title: 'client.query 怎么用？',
    description: '验证 SDK 标识符检索',
    category: 'sdk',
    icon: Braces,
  },
  {
    title: '双均线策略如何回测？',
    description: '验证策略与回测知识',
    category: 'strategy',
    icon: FileCode2,
  },
]

const categoryMap = Object.fromEntries(categories.map((item) => [item.value, item]))
const query = ref('')
const selectedCategory = ref('')
const topK = ref(5)
const loading = ref(false)
const searched = ref(false)
const results = ref([])
const error = ref('')
const elapsed = ref(0)
const serviceStatus = ref('checking')
const serviceInfo = ref(null)
const currentQuery = ref('')
let searchController
let healthController

const canSearch = computed(() => query.value.trim().length > 0 && !loading.value)
const resultSummary = computed(() => {
  if (!searched.value) return '等待检索'
  return results.value.length ? `找到 ${results.value.length} 条相关知识` : '未找到相关知识'
})

function formatPercent(score) {
  const normalized = Math.max(0, Math.min(1, Number(score) || 0))
  return `${Math.round(normalized * 100)}%`
}

function categoryLabel(category) {
  return categoryMap[category]?.label || category
}

function categoryClass(category) {
  return `category-${category.replace('_', '-')}`
}

async function refreshHealth() {
  healthController?.abort()
  healthController = new AbortController()
  serviceStatus.value = 'checking'
  try {
    serviceInfo.value = await checkHealth(healthController.signal)
    serviceStatus.value = 'online'
  } catch (healthError) {
    if (healthError.name === 'AbortError') return
    serviceStatus.value = 'offline'
    serviceInfo.value = null
  }
}

async function handleSearch() {
  const normalizedQuery = query.value.trim()
  if (!normalizedQuery || loading.value) return

  searchController?.abort()
  searchController = new AbortController()
  loading.value = true
  searched.value = true
  error.value = ''
  currentQuery.value = normalizedQuery
  const startedAt = performance.now()

  try {
    const data = await searchKnowledge(
      {
        query: normalizedQuery,
        categories: selectedCategory.value ? [selectedCategory.value] : null,
        top_k: Number(topK.value),
      },
      searchController.signal,
    )
    results.value = data.results || []
    elapsed.value = Math.max(1, Math.round(performance.now() - startedAt))
    serviceStatus.value = 'online'
  } catch (searchError) {
    if (searchError.name === 'AbortError') return
    results.value = []
    error.value = searchError.message || '检索失败，请检查知识库服务'
    serviceStatus.value = 'offline'
    elapsed.value = Math.max(1, Math.round(performance.now() - startedAt))
  } finally {
    loading.value = false
  }
}

function useExample(example) {
  query.value = example.title
  selectedCategory.value = example.category
  handleSearch()
}

function handleShortcut(event) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSearch()
  }
}

onMounted(refreshHealth)
onBeforeUnmount(() => {
  searchController?.abort()
  healthController?.abort()
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark"><Layers3 :size="21" stroke-width="2.3" /></div>
        <div>
          <div class="brand-title">量化平台知识库</div>
          <div class="brand-subtitle">Hybrid RAG 检索测试台</div>
        </div>
      </div>

      <button class="status-pill" type="button" @click="refreshHealth">
        <span class="status-dot" :class="serviceStatus" />
        <span v-if="serviceStatus === 'online'">知识服务正常</span>
        <span v-else-if="serviceStatus === 'checking'">正在检测服务</span>
        <span v-else>知识服务未连接</span>
        <RefreshCw :size="14" :class="{ spinning: serviceStatus === 'checking' }" />
      </button>
    </header>

    <main class="page-container">
      <section class="hero">
        <div class="eyebrow"><Sparkles :size="15" /> KNOWLEDGE SEARCH</div>
        <h1>检索你的量化知识</h1>
        <p>输入固收、指标、SDK 或策略问题，查看混合检索与重排结果。</p>

        <form class="search-panel" @submit.prevent="handleSearch">
          <div class="search-box">
            <Search :size="22" class="search-icon" />
            <input
              v-model="query"
              type="text"
              maxlength="2000"
              autocomplete="off"
              placeholder="例如：为 250220.IB 创建双均线策略，需要哪些知识？"
              aria-label="知识库查询内容"
              @keydown="handleShortcut"
            />
            <span class="shortcut">⌘ Enter</span>
            <button class="primary-button" type="submit" :disabled="!canSearch">
              <RefreshCw v-if="loading" :size="17" class="spinning" />
              <Search v-else :size="17" />
              {{ loading ? '检索中' : '开始检索' }}
            </button>
          </div>

          <div class="search-options">
            <div class="category-tabs" aria-label="知识分类">
              <button
                v-for="category in categories"
                :key="category.value"
                type="button"
                :class="{ active: selectedCategory === category.value }"
                @click="selectedCategory = category.value"
              >
                {{ category.label }}
              </button>
            </div>
            <label class="top-k-select">
              <Filter :size="15" />
              返回
              <select v-model="topK" aria-label="返回结果数量">
                <option :value="3">3 条</option>
                <option :value="5">5 条</option>
                <option :value="10">10 条</option>
              </select>
              <ChevronDown :size="14" class="select-arrow" />
            </label>
          </div>
        </form>
      </section>

      <section class="workspace-grid">
        <aside class="examples-card">
          <div class="section-heading">
            <div>
              <span class="section-kicker">快速开始</span>
              <h2>示例问题</h2>
            </div>
            <BookOpen :size="20" />
          </div>
          <div class="example-list">
            <button
              v-for="example in examples"
              :key="example.title"
              type="button"
              class="example-item"
              @click="useExample(example)"
            >
              <span class="example-icon"><component :is="example.icon" :size="18" /></span>
              <span class="example-copy">
                <strong>{{ example.title }}</strong>
                <small>{{ example.description }}</small>
              </span>
              <ArrowRight :size="16" class="example-arrow" />
            </button>
          </div>

          <div class="pipeline-card">
            <div class="pipeline-title"><Database :size="16" /> 当前检索链路</div>
            <div class="pipeline-steps">
              <span>BM25</span><i />
              <span>Vector</span><i />
              <span>Reranker</span>
            </div>
            <p>关键词与向量召回候选，再经过重排输出最终结果。</p>
          </div>
        </aside>

        <section class="results-panel">
          <div class="results-toolbar">
            <div>
              <span class="section-kicker">检索结果</span>
              <h2>{{ resultSummary }}</h2>
            </div>
            <div v-if="searched && !error" class="result-meta">
              <span><Clock3 :size="15" /> {{ elapsed }} ms</span>
              <span v-if="selectedCategory">{{ categoryLabel(selectedCategory) }}</span>
            </div>
          </div>

          <div v-if="loading" class="skeleton-list" aria-label="正在加载检索结果">
            <div v-for="item in 3" :key="item" class="result-card skeleton-card">
              <div class="skeleton-line short" />
              <div class="skeleton-line medium" />
              <div class="skeleton-line" />
              <div class="skeleton-line" />
            </div>
          </div>

          <div v-else-if="error" class="state-card error-state">
            <span class="state-icon error"><Database :size="26" /></span>
            <h3>暂时无法完成检索</h3>
            <p>{{ error }}</p>
            <button type="button" class="secondary-button" @click="refreshHealth">
              <RefreshCw :size="16" /> 重新检查服务
            </button>
          </div>

          <div v-else-if="!searched" class="state-card welcome-state">
            <span class="state-icon"><Search :size="27" /></span>
            <h3>开始你的第一次知识检索</h3>
            <p>可以输入问题，也可以从左侧选择一个示例。结果会显示来源、片段及各阶段相关度。</p>
            <div class="welcome-tags">
              <span><CheckCircle2 :size="14" /> 分类过滤</span>
              <span><CheckCircle2 :size="14" /> 混合召回</span>
              <span><CheckCircle2 :size="14" /> 结果重排</span>
            </div>
          </div>

          <div v-else-if="results.length === 0" class="state-card">
            <span class="state-icon"><BookOpen :size="26" /></span>
            <h3>没有找到匹配的知识</h3>
            <p>可以减少限定词、切换到“全部知识”，或者换一个更具体的关键词。</p>
          </div>

          <div v-else class="results-list">
            <article v-for="(result, index) in results" :key="result.id" class="result-card">
              <div class="result-head">
                <div class="result-rank">{{ String(index + 1).padStart(2, '0') }}</div>
                <div class="result-title-group">
                  <div class="result-badges">
                    <span class="category-badge" :class="categoryClass(result.category)">
                      {{ categoryLabel(result.category) }}
                    </span>
                    <span class="source-path">{{ result.source }}</span>
                  </div>
                  <h3>{{ result.title }}</h3>
                </div>
                <div class="score-circle" :style="{ '--score': formatPercent(result.score) }">
                  <strong>{{ formatPercent(result.score) }}</strong>
                  <small>综合相关度</small>
                </div>
              </div>

              <p class="result-snippet">{{ result.snippet }}</p>

              <div class="score-breakdown">
                <div class="score-item">
                  <span><i class="dot bm25" />BM25</span>
                  <div class="score-bar"><i :style="{ width: formatPercent(result.scores?.bm25) }" /></div>
                  <strong>{{ formatPercent(result.scores?.bm25) }}</strong>
                </div>
                <div class="score-item">
                  <span><i class="dot vector" />向量召回</span>
                  <div class="score-bar vector"><i :style="{ width: formatPercent(result.scores?.vector) }" /></div>
                  <strong>{{ formatPercent(result.scores?.vector) }}</strong>
                </div>
                <div class="score-item">
                  <span><i class="dot rerank" />重排得分</span>
                  <div class="score-bar rerank"><i :style="{ width: formatPercent(result.scores?.rerank) }" /></div>
                  <strong>{{ formatPercent(result.scores?.rerank) }}</strong>
                </div>
              </div>
            </article>
          </div>
        </section>
      </section>
    </main>

    <footer>
      <span>Quant Platform Knowledge</span>
      <span v-if="serviceInfo?.knowledge_dir">知识目录：{{ serviceInfo.knowledge_dir }}</span>
      <span v-else>RAG · Skills · Structured Metadata</span>
    </footer>
  </div>
</template>
