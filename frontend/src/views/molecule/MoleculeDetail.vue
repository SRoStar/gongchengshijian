<template>
  <div class="detail-page">
    <AppPageHeader />
    <el-card v-loading="loading">
      <template v-if="molecule">
        <el-row :gutter="20">
          <!-- Left: Structure Viewer -->
          <el-col :span="10">
            <div class="structure-viewer">
              <div ref="viewer" style="width:100%;height:350px;"></div>
              <div style="text-align:center;margin-top:8px">
                <el-button size="small" @click="downloadStructure">{{ $t('btn.download') }} {{ $t('molecule.formula') }}</el-button>
                <el-button size="small" type="primary" @click="copySMILES">Copy SMILES</el-button>
              </div>
            </div>
          </el-col>
          <!-- Right: Properties -->
          <el-col :span="14">
            <el-tabs v-model="activeTab">
              <el-tab-pane :label="$t('molecule.detail')" name="info">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item :label="$t('molecule.id')">{{ molecule.id }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('molecule.formula')"><strong>{{ molecule.formula }}</strong></el-descriptions-item>
                  <el-descriptions-item :label="$t('molecule.mass')">{{ molecule.mass }} g/mol</el-descriptions-item>
                  <el-descriptions-item :label="$t('molecule.volumeUnit')">{{ molecule.volume }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('molecule.type')"><el-tag size="small">{{ molecule.type }}</el-tag></el-descriptions-item>
                  <el-descriptions-item label="Charge"> {{ molecule.charge || 0 }}</el-descriptions-item>
                  <el-descriptions-item label="Spin">{{ molecule.spin || 1 }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('molecule.tags')">
                    <el-tag
                      v-for="tag in molecule.tags"
                      :key="tag"
                      size="mini"
                      style="margin-right:4px;cursor:pointer"
                      @click="$router.push({ path: '/molecule', query: { keyword: tag } })"
                    >{{ tag }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="SMILES" :span="2">{{ molecule.smiles }}</el-descriptions-item>
                  <el-descriptions-item label="InChI" :span="2"><span style="font-size:11px;word-break:break-all">{{ molecule.inchi }}</span></el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              <el-tab-pane label="Metadata" name="metadata">
                <el-empty description="元数据加载中..." v-if="!metadataLoaded"></el-empty>
                <el-form v-else label-width="120px" size="small">
                  <el-form-item label="计算方法">DFT-PBE</el-form-item>
                  <el-form-item label="基组">6-31G(d,p)</el-form-item>
                  <el-form-item label="温度">298.15 K</el-form-item>
                  <el-form-item label="压力">101325 Pa</el-form-item>
                </el-form>
              </el-tab-pane>
              <el-tab-pane label="Related" name="related">
                <el-empty description="暂无相关分子数据"></el-empty>
              </el-tab-pane>
              <el-tab-pane :label="$t('spectrum.spectroscopyData')" name="spectrum">
                <div v-loading="spectrumLoading">
                  <template v-if="spectrumData.length">
                    <el-form :inline="true" size="small" style="margin-bottom:12px">
                      <el-form-item :label="$t('spectrum.selectSpectrum')">
                        <el-select v-model="activeSpectrumId" @change="initSpectrumChart" style="width:260px">
                          <el-option v-for="s in spectrumData" :key="s.id" :label="s.name + ' (' + s.type + ')'" :value="s.id"></el-option>
                        </el-select>
                      </el-form-item>
                    </el-form>
                    <div ref="spectrumChart" style="width:100%;height:300px"></div>
                    <el-descriptions v-if="activeSpectrum" :column="2" border size="small" style="margin-top:16px">
                      <el-descriptions-item :label="$t('spectrum.instrument')">{{ activeSpectrum.instrument }}</el-descriptions-item>
                      <el-descriptions-item :label="$t('spectrum.spectrumType')">{{ activeSpectrum.type }}</el-descriptions-item>
                      <el-descriptions-item :label="$t('spectrum.conditions')" :span="2">{{ activeSpectrum.conditions }}</el-descriptions-item>
                    </el-descriptions>
                    <el-table v-if="activeSpectrum && activeSpectrum.peaks && activeSpectrum.peaks.length" :data="activeSpectrum.peaks" size="small" style="margin-top:12px">
                      <el-table-column prop="label" :label="$t('spectrum.peakPosition')" width="200"></el-table-column>
                      <el-table-column prop="x" :label="activeSpectrum.xLabel || 'Position'" width="180"></el-table-column>
                      <el-table-column prop="y" :label="$t('spectrum.peakIntensity')"></el-table-column>
                    </el-table>
                  </template>
                  <el-empty v-else :description="$t('spectrum.noSpectrumData')"></el-empty>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-col>
        </el-row>
      </template>
      <el-empty v-else :description="$t('common.noData')"></el-empty>
      <div style="margin-top:20px">
        <el-button @click="$router.push('/molecule')">{{ $t('btn.backToList') }}</el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import AppPageHeader from '@/components/AppPageHeader.vue'
import { getMoleculeDetail, getSpectrum } from '@/api'

export default {
  name: 'MoleculeDetail',
  components: { AppPageHeader },
  data() {
    return {
      molecule: null, loading: false, activeTab: 'info', metadataLoaded: false,
      // Spectrum data
      spectrumData: [], spectrumLoading: false,
      activeSpectrumId: '', spectrumChart: null
    }
  },
  computed: {
    activeSpectrum() {
      if (!this.activeSpectrumId || !this.spectrumData.length) return null
      return this.spectrumData.find(s => s.id === this.activeSpectrumId) || this.spectrumData[0]
    }
  },
  watch: {
    activeTab(val) {
      if (val === 'spectrum' && !this.spectrumData.length) {
        this.fetchSpectrumData()
      }
    }
  },
  mounted() { this.fetchDetail() },
  methods: {
    async fetchDetail() {
      this.loading = true
      try {
        const res = await getMoleculeDetail(this.$route.params.id)
        this.molecule = res.data
        this.$nextTick(() => {
          this.initViewer()
          setTimeout(() => { this.metadataLoaded = true }, 500)
        })
      } catch (_) {}
      this.loading = false
    },
    async fetchSpectrumData() {
      if (!this.molecule) return
      this.spectrumLoading = true
      try {
        const res = await getSpectrum(this.molecule.id)
        this.spectrumData = res.data || []
        if (this.spectrumData.length) {
          this.activeSpectrumId = this.spectrumData[0].id
          this.$nextTick(() => this.initSpectrumChart())
        }
      } catch (_) { this.spectrumData = [] }
      this.spectrumLoading = false
    },
    initSpectrumChart() {
      if (!this.$refs.spectrumChart) return
      if (this.spectrumChart) { this.spectrumChart.dispose(); this.spectrumChart = null }
      const spec = this.activeSpectrum
      if (!spec || !spec.dataPoints) return
      this.spectrumChart = echarts.init(this.$refs.spectrumChart)
      this.spectrumChart.setOption({
        title: { text: spec.name, left: 'center', top: 5, textStyle: { fontSize: 13, color: '#303133' } },
        tooltip: { trigger: 'axis' },
        grid: { top: 40, bottom: 40, left: 55, right: 15 },
        xAxis: {
          type: 'value',
          name: spec.xLabel || '',
          nameLocation: 'center',
          nameGap: 25,
          inverse: spec.type === 'NMR'
        },
        yAxis: {
          type: 'value',
          name: spec.yLabel || '',
          nameLocation: 'center',
          nameGap: 40
        },
        series: [{
          type: 'line',
          data: spec.dataPoints,
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#1a4a80', width: 1.5 },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(26,74,128,0.15)' },
            { offset: 1, color: 'rgba(26,74,128,0.02)' }
          ])},
          markPoint: {
            data: (spec.peaks || []).map(p => ({
              name: p.label,
              coord: [p.x, p.y],
              value: p.label
            })),
            symbol: 'pin',
            symbolSize: 28,
            label: { fontSize: 10 }
          }
        }]
      })
    },
    initViewer() {
      // 使用全局 ChemDoodle，兼容不同加载方式
      const ChemDoodleLib = window.ChemDoodle || (typeof ChemDoodle !== 'undefined' ? ChemDoodle : null)
      if (!this.$refs.viewer || !this.molecule || !ChemDoodleLib) return
      try {
        const mol = this.molecule
        this.$refs.viewer.innerHTML = ''

        // Check for MOL file data
        if (!mol.molFile) {
          this.$refs.viewer.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:350px;background:#f8f9fa;border:1px solid #ebeef5;border-radius:4px;color:#999;flex-direction:column">
              <div>No 3D structure data available</div>
              <div style="font-size:12px;margin-top:8px">MOL file required for visualization</div>
            </div>`
          return
        }

        // Create canvas element for ChemDoodle
        const canvasId = 'chemDoodle3DCanvas'
        const width = this.$refs.viewer.clientWidth
        const height = 350

        // Create canvas element directly
        const canvas = document.createElement('canvas')
        canvas.id = canvasId
        canvas.width = width
        canvas.height = height
        canvas.style.display = 'block'
        this.$refs.viewer.appendChild(canvas)

        // Use TransformCanvas3D for interactive 3D visualization
        let transform3D
        let canvasType = 'TransformCanvas3D'
        try {
          transform3D = new ChemDoodleLib.TransformCanvas3D(canvasId, width, height)
        } catch (e) {
          console.warn('TransformCanvas3D not available, trying ViewerCanvas3D:', e)
          canvasType = 'ViewerCanvas3D'
          try {
            transform3D = new ChemDoodleLib.ViewerCanvas3D(canvasId, width, height)
          } catch (e2) {
            console.warn('ViewerCanvas3D also failed, using 2D ViewerCanvas:', e2)
            canvasType = 'ViewerCanvas (2D)'
            transform3D = new ChemDoodleLib.ViewerCanvas(canvasId, width, height)
          }
        }

        // 在 viewer 上显示当前模式
        const infoDiv = document.createElement('div')
        infoDiv.style.cssText = 'position:absolute;top:5px;right:5px;font-size:11px;color:#666;background:rgba(255,255,255,0.8);padding:2px 6px;border-radius:3px;'
        infoDiv.textContent = canvasType === 'TransformCanvas3D' ? '3D Interactive' : (canvasType === 'ViewerCanvas3D' ? '3D View Only' : '2D View')
        this.$refs.viewer.appendChild(infoDiv)

        // 如果不是 TransformCanvas3D，添加操作提示
        if (canvasType !== 'TransformCanvas3D') {
          const hintDiv = document.createElement('div')
          hintDiv.style.cssText = 'position:absolute;bottom:5px;left:5px;font-size:11px;color:#999;background:rgba(255,255,255,0.8);padding:2px 6px;border-radius:3px;'
          hintDiv.textContent = canvasType === 'ViewerCanvas3D' ? '左键:平移 滚轮:缩放' : '2D 模式'
          this.$refs.viewer.appendChild(hintDiv)
        }

        // Set 3D representation style
        if (transform3D.styles) {
          transform3D.styles.set3DRepresentation && transform3D.styles.set3DRepresentation('Ball and Stick')
          transform3D.styles.backgroundColor = '#f8f9fa'
        }

        // Load molecule from MOL file
        // 处理可能被转义的换行符
        let molFileContent = mol.molFile
        if (molFileContent.includes('\\n')) {
          molFileContent = molFileContent.replace(/\\n/g, '\n')
        }

        const moleculeData = ChemDoodleLib.readMOL(molFileContent, 1)

        // Load molecule into 3D canvas
        transform3D.loadMolecule(moleculeData)

        // Store reference for cleanup
        this.chemDoodleViewer = transform3D

      } catch (e) {
        console.warn('ChemDoodle 3D init failed:', e)
        // Fallback to error message
        if (this.$refs.viewer) {
          this.$refs.viewer.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:350px;background:#f8f9fa;border:1px solid #ebeef5;border-radius:4px;color:#999;flex-direction:column">
              <div>Failed to load 3D structure</div>
              <div style="font-size:12px;margin-top:8px">${e.message}</div>
            </div>`
        }
      }
    },
    downloadStructure() {
      if (this.molecule) {
        this.$message.success('Structure download triggered (mock)')
      }
    },
    copySMILES() {
      if (this.molecule && this.molecule.smiles) {
        navigator.clipboard.writeText(this.molecule.smiles).then(() => {
          this.$message.success(this.$t('common.copySuccess'))
        }).catch(() => {})
      }
    }
  },
  beforeDestroy() {
    if (this.spectrumChart) { this.spectrumChart.dispose(); this.spectrumChart = null }
  }
}
</script>

<style scoped>
.structure-viewer {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  background: #fff;
}
</style>
