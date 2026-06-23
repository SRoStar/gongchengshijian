<template>
  <div class="list-page">
    <AppPageHeader />

    <!-- ===== 数据集切换 ===== -->
    <el-card style="margin-bottom:16px">
      <el-radio-group v-model="compareMode" size="small">
        <el-radio-button label="single">单数据集</el-radio-button>
        <el-radio-button label="compare">双数据集对比</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- ===== Dataset A ===== -->
    <el-card>
      <div slot="header"><span style="font-weight:600">Dataset A</span></div>
      <el-tabs v-model="activeTab" type="card" class="xrd-tabs">
        <el-tab-pane label="粘贴数据" name="paste">
          <el-input
            v-model="textData"
            type="textarea"
            :rows="8"
            placeholder="每行格式：角度 强度（空格或制表符分隔）&#10;示例：&#10;25.5 100&#10;26.2 85&#10;38.1 120"
          ></el-input>
        </el-tab-pane>
        <el-tab-pane label="上传 NPY 文件" name="npy">
          <p style="color:#909399;font-size:13px;margin-bottom:12px">
            上传 NumPy 保存的 .npy 文件，数组形状需为 [N, 2]：第 0 列为 2θ 角度(度)，第 1 列为强度。支持 CoreMOF 格式。
          </p>
          <el-upload
            ref="npyUpload"
            :auto-upload="false"
            :limit="1"
            accept=".npy"
            :on-change="handleNpyChange"
            :on-remove="handleNpyRemove"
            :file-list="npyFileList"
            action="#"
          >
            <el-button size="small" type="primary">
              <i class="el-icon-folder-opened"></i> 选择 .npy 文件
            </el-button>
          </el-upload>
          <!-- NPY 分组选择（新功能） -->
          <div v-if="npyCacheInfo" style="margin-top:12px">
            <el-tag type="success" size="small">总组数: {{ npyCacheInfo.total_groups }}</el-tag>
            <el-tag type="info" size="small" style="margin-left:4px">网格点: {{ npyCacheInfo.grid_points }}</el-tag>
            <div style="margin-top:8px;display:flex;align-items:center;gap:8px">
              <span style="font-size:13px;color:#606266">选择组 (0-based):</span>
              <el-input-number
                v-model="groupIndex"
                :min="0"
                :max="npyCacheInfo.total_groups - 1"
                size="small"
                style="width:100px"
              ></el-input-number>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="示例数据" name="sample">
          <p style="color:#909399;font-size:13px;margin-bottom:12px">点击下方按钮加载示例 XRD 衍射峰数据</p>
          <el-button size="small" type="success" @click="loadSample('A')">加载示例数据</el-button>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ===== Dataset B（双数据集对比模式） ===== -->
    <el-card v-if="compareMode === 'compare'" style="margin-top:16px">
      <div slot="header"><span style="font-weight:600">Dataset B</span></div>
      <el-tabs v-model="activeTabB" type="card" class="xrd-tabs">
        <el-tab-pane label="粘贴数据" name="paste">
          <el-input
            v-model="textDataB"
            type="textarea"
            :rows="8"
            placeholder="每行格式：角度 强度（空格或制表符分隔）"
          ></el-input>
        </el-tab-pane>
        <el-tab-pane label="上传 NPY 文件" name="npy">
          <p style="color:#909399;font-size:13px;margin-bottom:12px">
            上传 NumPy 保存的 .npy 文件。支持 CoreMOF 格式，可选择不同数据组。
          </p>
          <el-upload
            ref="npyUploadB"
            :auto-upload="false"
            :limit="1"
            accept=".npy"
            :on-change="handleNpyChangeB"
            :on-remove="handleNpyRemoveB"
            :file-list="npyFileListB"
            action="#"
          >
            <el-button size="small" type="primary">
              <i class="el-icon-folder-opened"></i> 选择 .npy 文件
            </el-button>
          </el-upload>
          <div v-if="npyCacheInfoB" style="margin-top:12px">
            <el-tag type="success" size="small">总组数: {{ npyCacheInfoB.total_groups }}</el-tag>
            <el-tag type="info" size="small" style="margin-left:4px">网格点: {{ npyCacheInfoB.grid_points }}</el-tag>
            <div style="margin-top:8px;display:flex;align-items:center;gap:8px">
              <span style="font-size:13px;color:#606266">选择组 (0-based):</span>
              <el-input-number
                v-model="groupIndexB"
                :min="0"
                :max="npyCacheInfoB.total_groups - 1"
                size="small"
                style="width:100px"
              ></el-input-number>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="示例数据" name="sample">
          <p style="color:#909399;font-size:13px;margin-bottom:12px">点击下方按钮加载另一组示例数据</p>
          <el-button size="small" type="success" @click="loadSample('B')">加载示例数据</el-button>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ===== 处理参数（原有逻辑保留） ===== -->
    <el-card style="margin-top:16px">
      <el-divider content-position="left">处理参数</el-divider>
      <el-form :inline="true" size="small">
        <el-form-item label="最小角度 (°)">
          <el-input-number v-model="minAngle" :min="0" :max="90" :step="0.1" :precision="1" size="small"></el-input-number>
        </el-form-item>
        <el-form-item label="最大角度 (°)">
          <el-input-number v-model="maxAngle" :min="5" :max="180" :step="0.1" :precision="1" size="small"></el-input-number>
        </el-form-item>
        <el-form-item label="步长 (°)">
          <el-input-number v-model="step" :min="0.001" :step="0.001" :precision="3" size="small"></el-input-number>
        </el-form-item>
        <el-form-item label="Sigma (高斯展宽)">
          <el-input-number v-model="sigma" :min="0.01" :step="0.01" :precision="2" size="small"></el-input-number>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="processing" @click="handleProcess">{{ processing ? '处理中...' : '处理并可视化' }}</el-button>
        </el-form-item>
      </el-form>

      <!-- Y-axis Toggle（原有逻辑保留） -->
      <el-form v-if="chartResult" :inline="true" size="small" style="margin-top:8px">
        <el-form-item label="Y 轴显示">
          <el-radio-group v-model="yAxisMode" @change="renderAllCharts" size="small">
            <el-radio-button label="real">真实强度</el-radio-button>
            <el-radio-button label="normalized">归一化 (0–1)</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ===== 图谱（原有 A 图 + 新增 B 图） ===== -->
    <el-card v-if="chartResult" style="margin-top:16px">
      <el-divider content-position="left">XRD 图谱</el-divider>
      <el-row :gutter="16">
        <el-col :span="compareMode === 'compare' ? 12 : 24">
          <div ref="chartContainer" style="width:100%;height:420px;margin-top:8px"></div>
        </el-col>
        <el-col v-if="compareMode === 'compare' && chartResultB" :span="12">
          <div ref="chartContainerB" style="width:100%;height:420px;margin-top:8px"></div>
        </el-col>
      </el-row>
      <div class="chart-legend">
        <span><span class="legend-dot" style="background:#409EFF"></span> 高斯展宽后</span>
        <span><span class="legend-dot" style="background:#E6A23C"></span> 原始峰</span>
        <span><span class="legend-dot" style="background:#67C23A"></span> 最大值</span>
        <span><span class="legend-dot" style="background:#F56C6C"></span> 最小值</span>
      </div>
    </el-card>

    <!-- ===== 对比指标（新增） ===== -->
    <el-card v-if="comparisonMetrics" style="margin-top:16px">
      <el-divider content-position="left">对比指标</el-divider>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="metric-card">
            <div class="metric-title">余弦相似度</div>
            <div class="metric-value">{{ formatNum(comparisonMetrics.cosineSimilarity) }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="metric-card">
            <div class="metric-title">卡方检验</div>
            <div class="metric-value">{{ formatNum(comparisonMetrics.chiSquare) }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="metric-card">
            <div class="metric-title">均方误差 (MSE)</div>
            <div class="metric-value">{{ formatNum(comparisonMetrics.mse) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- ===== 数据统计（原有逻辑保留 + B 组统计） ===== -->
    <template v-if="chartResult">
      <el-divider content-position="left">数据统计</el-divider>
      <p style="color:#909399;font-size:13px;margin-bottom:12px">处理完成后将显示强度分布统计（最大值、最小值、四分位数）</p>
      <el-row :gutter="20">
        <el-col :span="compareMode === 'compare' ? 12 : 12">
          <el-card shadow="never" class="stats-card">
            <div slot="header"><span style="font-weight:600;color:#1a4a80">Dataset A — 原始数据（强度）</span></div>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="最大值">{{ statsDisplayA.original.max }}</el-descriptions-item>
              <el-descriptions-item label="最小值">{{ statsDisplayA.original.min }}</el-descriptions-item>
              <el-descriptions-item label="Q1 (25%)">{{ statsDisplayA.original.q1 }}</el-descriptions-item>
              <el-descriptions-item label="中位数 Q2 (50%)">{{ statsDisplayA.original.q2 }}</el-descriptions-item>
              <el-descriptions-item label="Q3 (75%)">{{ statsDisplayA.original.q3 }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="compareMode === 'compare' ? 12 : 12">
          <el-card shadow="never" class="stats-card">
            <div slot="header"><span style="font-weight:600;color:#67C23A">Dataset A — 展宽后数据（归一化强度）</span></div>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="最大值">{{ statsDisplayA.processed.max }}</el-descriptions-item>
              <el-descriptions-item label="最小值">{{ statsDisplayA.processed.min }}</el-descriptions-item>
              <el-descriptions-item label="Q1 (25%)">{{ statsDisplayA.processed.q1 }}</el-descriptions-item>
              <el-descriptions-item label="中位数 Q2 (50%)">{{ statsDisplayA.processed.q2 }}</el-descriptions-item>
              <el-descriptions-item label="Q3 (75%)">{{ statsDisplayA.processed.q3 }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
      <!-- B 组统计 -->
      <el-row v-if="compareMode === 'compare' && chartResultB" :gutter="20" style="margin-top:16px">
        <el-col :span="12">
          <el-card shadow="never" class="stats-card">
            <div slot="header"><span style="font-weight:600;color:#1a4a80">Dataset B — 原始数据（强度）</span></div>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="最大值">{{ statsDisplayB.original.max }}</el-descriptions-item>
              <el-descriptions-item label="最小值">{{ statsDisplayB.original.min }}</el-descriptions-item>
              <el-descriptions-item label="Q1 (25%)">{{ statsDisplayB.original.q1 }}</el-descriptions-item>
              <el-descriptions-item label="中位数 Q2 (50%)">{{ statsDisplayB.original.q2 }}</el-descriptions-item>
              <el-descriptions-item label="Q3 (75%)">{{ statsDisplayB.original.q3 }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" class="stats-card">
            <div slot="header"><span style="font-weight:600;color:#67C23A">Dataset B — 展宽后数据（归一化强度）</span></div>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="最大值">{{ statsDisplayB.processed.max }}</el-descriptions-item>
              <el-descriptions-item label="最小值">{{ statsDisplayB.processed.min }}</el-descriptions-item>
              <el-descriptions-item label="Q1 (25%)">{{ statsDisplayB.processed.q1 }}</el-descriptions-item>
              <el-descriptions-item label="中位数 Q2 (50%)">{{ statsDisplayB.processed.q2 }}</el-descriptions-item>
              <el-descriptions-item label="Q3 (75%)">{{ statsDisplayB.processed.q3 }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-empty v-if="!chartResult && !processing" description="请粘贴 XRD 数据或上传 .npy 文件，点击「处理并可视化」查看图谱"></el-empty>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import AppPageHeader from '@/components/AppPageHeader.vue'
import { xrdProcess, xrdProcessNpy, xrdUploadNpyCache, xrdProcessNpyGroup } from '@/api'

const SAMPLE_DATA_A = `25.5 100
26.2 85
38.1 120
44.2 95
51.8 110
64.2 78
77.4 65`

const SAMPLE_DATA_B = `25.8 95
26.5 90
38.4 115
44.5 90
52.1 105
64.5 75
77.7 60`

export default {
  name: 'XrdTool',
  components: { AppPageHeader },
  data() {
    return {
      compareMode: 'single',
      // Dataset A（原有字段保留）
      activeTab: 'paste',
      textData: '',
      npyFileList: [],
      npyFile: null,
      npyCacheInfo: null,
      groupIndex: 0,
      // Dataset B（新增）
      activeTabB: 'paste',
      textDataB: '',
      npyFileListB: [],
      npyFileB: null,
      npyCacheInfoB: null,
      groupIndexB: 0,
      // 参数（原有逻辑保留）
      minAngle: 5,
      maxAngle: 90,
      step: 0.01,
      sigma: 0.1,
      yAxisMode: 'real',
      processing: false,
      // 结果
      chartResult: null,
      chartResultB: null,
      chart: null,
      chartB: null,
      comparisonMetrics: null,
      // 统计（原有格式保留）
      statsA: { original: { min: null, max: null, q1: null, q2: null, q3: null }, processed: { min: null, max: null, q1: null, q2: null, q3: null } },
      statsB: { original: { min: null, max: null, q1: null, q2: null, q3: null }, processed: { min: null, max: null, q1: null, q2: null, q3: null } }
    }
  },
  computed: {
    statsDisplayA() {
      const s = this.statsA
      const fmt = this.formatNum
      return {
        original: { max: fmt(s.original.max), min: fmt(s.original.min), q1: fmt(s.original.q1), q2: fmt(s.original.q2), q3: fmt(s.original.q3) },
        processed: { max: fmt(s.processed.max), min: fmt(s.processed.min), q1: fmt(s.processed.q1), q2: fmt(s.processed.q2), q3: fmt(s.processed.q3) }
      }
    },
    statsDisplayB() {
      const s = this.statsB
      const fmt = this.formatNum
      return {
        original: { max: fmt(s.original.max), min: fmt(s.original.min), q1: fmt(s.original.q1), q2: fmt(s.original.q2), q3: fmt(s.original.q3) },
        processed: { max: fmt(s.processed.max), min: fmt(s.processed.min), q1: fmt(s.processed.q1), q2: fmt(s.processed.q2), q3: fmt(s.processed.q3) }
      }
    }
  },
  methods: {
    // ===== 原有方法保留 =====
    loadSample(ds) {
      if (ds === 'B') {
        this.textDataB = SAMPLE_DATA_B
        this.activeTabB = 'paste'
      } else {
        this.textData = SAMPLE_DATA_A
        this.activeTab = 'paste'
      }
    },
    handleNpyChange(file, fileList) {
      this.npyFile = file.raw
      this.npyFileList = fileList
      // 同时上传到缓存以支持分组选择
      this.cacheNpyFile(file.raw, 'A')
    },
    handleNpyRemove() {
      this.npyFile = null
      this.npyFileList = []
      this.npyCacheInfo = null
    },
    handleNpyChangeB(file, fileList) {
      this.npyFileB = file.raw
      this.npyFileListB = fileList
      this.cacheNpyFile(file.raw, 'B')
    },
    handleNpyRemoveB() {
      this.npyFileB = null
      this.npyFileListB = []
      this.npyCacheInfoB = null
    },
    async cacheNpyFile(file, ds) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const res = await xrdUploadNpyCache(formData)
        if (ds === 'A') {
          this.npyCacheInfo = res.data
          this.groupIndex = 0
        } else {
          this.npyCacheInfoB = res.data
          this.groupIndexB = 0
        }
      } catch (_) { /* cache failed silently, direct upload still works */ }
    },
    parseTextData(text) {
      const lines = text.trim().split(/\r?\n/).filter(Boolean)
      const data = []
      for (const line of lines) {
        const parts = line.trim().split(/[\s\t,;]+/)
        if (parts.length >= 2) {
          const angle = parseFloat(parts[0])
          const intensity = parseFloat(parts[1])
          if (!isNaN(angle) && !isNaN(intensity)) {
            data.push({ angle, intensity })
          }
        }
      }
      return data
    },
    computeStats(arr) {
      if (!arr || arr.length === 0) {
        return { min: null, max: null, q1: null, q2: null, q3: null }
      }
      const sorted = [...arr].sort((a, b) => a - b)
      const n = sorted.length
      const percentile = (p) => {
        const idx = p * (n - 1)
        const lo = Math.floor(idx)
        const hi = Math.ceil(idx)
        if (lo === hi) return sorted[lo]
        return sorted[lo] + (idx - lo) * (sorted[hi] - sorted[lo])
      }
      return {
        min: sorted[0],
        max: sorted[n - 1],
        q1: percentile(0.25),
        q2: percentile(0.5),
        q3: percentile(0.75)
      }
    },
    formatNum(v) {
      if (v == null) return '—'
      if (Math.abs(v) < 1e-4 || Math.abs(v) >= 1e4) return v.toExponential(4)
      return v.toFixed(4)
    },

    // ===== 核心处理 =====
    async handleProcess() {
      this.processing = true
      try {
        // Dataset A（原有逻辑）
        await this.processDataset({
          tab: this.activeTab,
          textData: this.textData,
          npyFile: this.npyFile,
          npyCacheInfo: this.npyCacheInfo,
          groupIndex: this.groupIndex,
          resultKey: 'A'
        })

        // Dataset B（仅对比模式）
        if (this.compareMode === 'compare') {
          await this.processDataset({
            tab: this.activeTabB,
            textData: this.textDataB,
            npyFile: this.npyFileB,
            npyCacheInfo: this.npyCacheInfoB,
            groupIndex: this.groupIndexB,
            resultKey: 'B'
          })
          this.updateComparison()
        }
      } finally {
        this.processing = false
      }
    },

    async processDataset({ tab, textData, npyFile, npyCacheInfo, groupIndex, resultKey }) {
      // NPY 分组模式（新功能）
      if (tab === 'npy' && npyCacheInfo) {
        try {
          const res = await xrdProcessNpyGroup({
            filename: npyCacheInfo.filename,
            group_index: groupIndex,
            min_angle: this.minAngle,
            max_angle: this.maxAngle,
            step: this.step,
            sigma: this.sigma
          })
          this.applyResult(resultKey, res.data)
          return
        } catch (_) { /* fall through to legacy mode */ }
      }

      // NPY 直接处理模式（原有逻辑）
      if (tab === 'npy' && npyFile) {
        const formData = new FormData()
        formData.append('file', npyFile)
        formData.append('min_angle', String(this.minAngle))
        formData.append('max_angle', String(this.maxAngle))
        formData.append('step', String(this.step))
        formData.append('sigma', String(this.sigma))
        try {
          const res = await xrdProcessNpy(formData)
          this.applyResult(resultKey, res.data)
          return
        } catch (_) { return }
      }

      // 文本数据处理（原有逻辑）
      const text = textData.trim()
      if (!text) {
        if (resultKey === 'A') this.$message.warning('请输入 XRD 数据')
        return
      }
      const data = this.parseTextData(text)
      if (!data.length) {
        this.$message.error(`Dataset ${resultKey}: 无法解析有效数据`)
        return
      }
      try {
        const res = await xrdProcess({
          data,
          min_angle: this.minAngle,
          max_angle: this.maxAngle,
          step: this.step,
          sigma: this.sigma
        })
        this.applyResult(resultKey, res.data)
      } catch (_) {}
    },

    applyResult(key, result) {
      if (key === 'A') {
        this.chartResult = result
        this.statsA.original = this.computeStats(result.original.intensities)
        this.statsA.processed = this.computeStats(result.processed.intensities)
        this.$nextTick(() => this.renderChart('A'))
      } else {
        this.chartResultB = result
        this.statsB.original = this.computeStats(result.original.intensities)
        this.statsB.processed = this.computeStats(result.processed.intensities)
        this.$nextTick(() => this.renderChart('B'))
      }
    },

    // ===== 对比指标计算（新增） =====
    updateComparison() {
      if (!this.chartResult || !this.chartResultB) {
        this.comparisonMetrics = null
        return
      }
      const pA = this.chartResult.processed
      const pB = this.chartResultB.processed
      const minA = Math.max(Math.min(...pA.angles), Math.min(...pB.angles))
      const maxA = Math.min(Math.max(...pA.angles), Math.max(...pB.angles))
      const common = []
      for (let a = minA; a <= maxA; a += this.step) common.push(a)

      const interp = (angles, intensities, targets) => {
        return targets.map(t => {
          if (t <= angles[0]) return intensities[0]
          if (t >= angles[angles.length - 1]) return intensities[intensities.length - 1]
          for (let i = 0; i < angles.length - 1; i++) {
            if (angles[i] <= t && t <= angles[i + 1]) {
              const f = (t - angles[i]) / (angles[i + 1] - angles[i])
              return intensities[i] + f * (intensities[i + 1] - intensities[i])
            }
          }
          return 0
        })
      }
      const iA = interp(pA.angles, pA.intensities, common)
      const iB = interp(pB.angles, pB.intensities, common)

      const dot = iA.reduce((s, v, i) => s + v * iB[i], 0)
      const nA = Math.sqrt(iA.reduce((s, v) => s + v * v, 0))
      const nB = Math.sqrt(iB.reduce((s, v) => s + v * v, 0))
      const cosine = nA && nB ? dot / (nA * nB) : 0

      let chi = 0
      for (let i = 0; i < iA.length; i++) {
        if (iB[i] > 1e-10) chi += Math.pow(iA[i] - iB[i], 2) / iB[i]
      }
      const mseVal = iA.reduce((s, v, i) => s + Math.pow(v - iB[i], 2), 0) / iA.length
      this.comparisonMetrics = { cosineSimilarity: cosine, chiSquare: chi, mse: mseVal }
    },

    // ===== 图表渲染（原有逻辑保留 + B图） =====
    renderAllCharts() {
      if (this.chartResult) {
        this.$nextTick(() => this.renderChart('A'))
      }
      if (this.chartResultB) {
        this.$nextTick(() => this.renderChart('B'))
      }
    },

    renderChart(ds) {
      const refKey = ds === 'A' ? 'chartContainer' : 'chartContainerB'
      const instKey = ds === 'A' ? 'chart' : 'chartB'
      const result = ds === 'A' ? this.chartResult : this.chartResultB
      const container = this.$refs[refKey]
      if (!container || !result) return

      if (this[instKey]) { this[instKey].dispose(); this[instKey] = null }

      const original = result.original
      const processed = result.processed
      const useNormalized = this.yAxisMode === 'normalized'

      let processedY, originalY
      if (useNormalized) {
        const maxOrig = Math.max(...original.intensities, 1)
        originalY = original.intensities.map(v => v / maxOrig)
        processedY = [...processed.intensities]
      } else {
        const maxOrig = Math.max(...original.intensities, 1)
        originalY = [...original.intensities]
        processedY = processed.intensities.map(v => v * maxOrig)
      }

      const combined = []
      processed.angles.forEach((a, i) => combined.push({ x: a, y: processedY[i], type: 'processed' }))
      original.angles.forEach((a, i) => combined.push({ x: a, y: originalY[i], type: 'original' }))
      const maxPt = combined.reduce((a, b) => (a.y >= b.y ? a : b))
      const minPt = combined.reduce((a, b) => (a.y <= b.y ? a : b))

      this[instKey] = echarts.init(container)
      this[instKey].setOption({
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            let html = ''
            params.forEach(p => {
              html += `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};margin-right:5px"></span>`
              html += `${p.seriesName}: ${Number(p.value[1]).toFixed(4)}<br/>`
            })
            return html
          }
        },
        legend: { show: false },
        grid: { top: 20, bottom: 50, left: 60, right: 30 },
        xAxis: {
          type: 'value',
          name: '2θ (度)',
          nameLocation: 'center',
          nameGap: 30,
          min: 'dataMin',
          max: 'dataMax',
          minorTick: { show: true },
          minorSplitLine: { show: true, lineStyle: { color: '#f0f0f0' } }
        },
        yAxis: {
          type: 'value',
          name: useNormalized ? '强度 (归一化)' : '强度',
          nameLocation: 'center',
          nameGap: 45,
          min: 'dataMin',
          max: 'dataMax'
        },
        series: [
          {
            name: '高斯展宽后',
            type: 'line',
            data: processed.angles.map((a, i) => [a, processedY[i]]),
            smooth: true,
            showSymbol: false,
            lineStyle: { color: '#409EFF', width: 1.5 },
            areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,158,255,0.15)' },
              { offset: 1, color: 'rgba(64,158,255,0.02)' }
            ])}
          },
          {
            name: '原始峰',
            type: 'scatter',
            data: original.angles.map((a, i) => [a, originalY[i]]),
            symbolSize: 8,
            itemStyle: { color: '#E6A23C', borderColor: '#fff', borderWidth: 1 },
            emphasis: { scale: 1.5 }
          },
          {
            name: '最大值',
            type: 'scatter',
            data: [[maxPt.x, maxPt.y]],
            symbol: 'triangle',
            symbolSize: 16,
            itemStyle: { color: '#67C23A' },
            label: {
              show: true,
              position: 'top',
              distance: 8,
              formatter: `最大值 ${maxPt.y.toFixed(2)} @ ${maxPt.x.toFixed(2)}°`,
              fontSize: 11
            }
          },
          {
            name: '最小值',
            type: 'scatter',
            data: [[minPt.x, minPt.y]],
            symbol: 'triangle',
            symbolSize: 16,
            symbolRotate: 180,
            itemStyle: { color: '#F56C6C' },
            label: {
              show: true,
              position: 'bottom',
              distance: 8,
              formatter: `最小值 ${minPt.y.toFixed(2)} @ ${minPt.x.toFixed(2)}°`,
              fontSize: 11
            }
          }
        ]
      })
    }
  },
  beforeDestroy() {
    if (this.chart) { this.chart.dispose(); this.chart = null }
    if (this.chartB) { this.chartB.dispose(); this.chartB = null }
  }
}
</script>

<style scoped>
.xrd-tabs { margin-bottom: 8px; }
.chart-legend {
  display: flex;
  gap: 20px;
  justify-content: center;
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}
.legend-dot {
  display: inline-block;
  width: 12px;
  height: 4px;
  border-radius: 2px;
  margin-right: 6px;
  vertical-align: middle;
}
.stats-card {
  border: 1px solid #ebeef5;
}
.metric-card {
  text-align: center;
  padding: 20px;
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}
.metric-title { font-size: 13px; color: #909399; margin-bottom: 8px; }
.metric-value { font-size: 24px; font-weight: bold; color: #1a4a80; }
</style>
