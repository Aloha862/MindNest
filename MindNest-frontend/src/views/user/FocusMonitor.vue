<template>
  <main class="page-shell focus-page">
    <section class="focus-top">
      <div>
        <p class="eyebrow">学习状态监督</p>
        <h1>专注监督</h1>
        <span>端侧姿态实时运行；学习中每 1 秒上传压缩帧识别物品，原始视频流不上传。</span>
      </div>
      <div class="session-actions">
        <el-button v-if="!isSessionActive && cameraReady" size="large" @click="stopCamera"><VideoOff />关闭预览</el-button>
        <el-button v-if="!isSessionActive && !cameraReady" size="large" @click="initCamera"><Camera />开启预览</el-button>
        <el-button v-if="!isSessionActive" type="primary" size="large" @click="startSession"><Play />开始学习</el-button>
        <el-button v-else type="danger" size="large" :loading="endingSession" @click="finishSession"><Square />结束学习</el-button>
      </div>
    </section>

    <section class="monitor-grid">
      <article class="camera-panel panel">
        <header>
          <div>
            <h2>本地实时检测</h2>
            <p>{{ statusMessage }}</p>
          </div>
          <el-tag :type="healthTag.type">{{ healthTag.text }}</el-tag>
        </header>
        <div class="video-box">
          <video v-show="cameraReady" ref="videoRef" autoplay muted playsinline />
          <canvas v-show="cameraReady" ref="overlayRef" />
          <div v-if="!cameraReady" class="camera-fallback">
            <Camera />
            <strong>{{ cameraError || '摄像头未开启' }}</strong>
            <span>允许摄像头权限后，系统会自动开始识别；拒绝权限时不会伪造状态。</span>
          </div>
        </div>
      </article>

      <article class="state-panel panel">
        <header>
          <h2>自动状态</h2>
          <strong :class="displayState.state">{{ displayState.label }}</strong>
        </header>
        <div class="score-ring">
          <span>{{ focusScore }}</span>
          <small>专注分</small>
        </div>
        <div class="metric-grid">
          <p><span>FPS</span><strong>{{ vision.fps }}</strong></p>
          <p><span>置信度</span><strong>{{ Math.round(vision.confidence * 100) }}%</strong></p>
          <p><span>姿态</span><strong>{{ postureText }}</strong></p>
          <p><span>端侧人体</span><strong>{{ objectText }}</strong></p>
        </div>
        <div class="server-vision">
          <div class="server-vision-head">
            <span>后端对象识别</span>
            <el-tag size="small" :type="yoloeTag.type">{{ yoloeTag.text }}</el-tag>
          </div>
          <p>{{ yoloeMessage }}</p>
          <div v-if="yoloe.detectedObjects.length" class="object-tags">
            <el-tag v-for="item in yoloe.detectedObjects" :key="item" effect="plain" size="small">{{ labelObject(item) }}</el-tag>
          </div>
          <small v-if="yoloe.available">{{ yoloe.modelName }} · {{ yoloe.device || '自动设备' }} · {{ yoloe.latencyMs }} ms · 每 1 秒抽帧</small>
        </div>
      </article>
    </section>

    <section class="stats-grid">
      <StatCard label="学习时长" :value="formatDuration(liveStats.totalDuration)" hint="本次 session" :icon="Clock" />
      <StatCard label="有效专注" :value="formatDuration(liveStats.effectiveDuration)" hint="自动识别计时" color="#22c55e" :icon="BadgeCheck" />
      <StatCard label="手机分心" :value="liveStats.distractionCount" hint="YOLOE 抽帧辅助识别" color="#ef4444" :icon="Smartphone" />
      <StatCard label="离座次数" :value="liveStats.awayCount" hint="人体检测丢失后记录" color="#f59e0b" :icon="DoorOpen" />
    </section>

    <section class="detail-grid">
      <article class="panel timeline-panel">
        <header>
          <h2>自动采样时间线</h2>
          <span>{{ isSessionActive ? '约每 1 秒写入一次稳定状态' : '开始学习后自动采样' }}</span>
        </header>
        <div v-if="logs.length" class="timeline">
          <div v-for="log in logs" :key="log.id" class="timeline-row">
            <span :class="log.state" />
            <div>
              <strong>{{ log.stateLabel }}</strong>
              <small>{{ log.timestamp }} · 专注分 {{ log.focusScore }}</small>
            </div>
            <em>{{ log.effective ? '计入' : '暂停' }}</em>
          </div>
        </div>
        <EmptyState v-else title="暂无状态记录" description="识别模型稳定输出后，会自动生成采样记录。" />
      </article>

      <article class="panel advice-panel">
        <h2>实时提醒</h2>
        <p v-for="item in activeAdvices" :key="item"><AlertCircle />{{ item }}</p>
        <div class="debug-box">
          <span>头部下压：{{ vision.debugMetrics.headDrop ?? '--' }}</span>
          <span>肩线倾斜：{{ vision.debugMetrics.shoulderSlope ?? '--' }}</span>
          <span>头部偏侧：{{ vision.debugMetrics.headSide ?? '--' }}</span>
          <span>动作稳定：{{ vision.debugMetrics.motion ?? '--' }}</span>
        </div>
      </article>
    </section>
  </main>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  AlertCircle,
  BadgeCheck,
  Camera,
  Clock,
  DoorOpen,
  Play,
  Smartphone,
  Square,
  VideoOff
} from 'lucide-vue-next'
import { analyzeFocusFrame, endFocusSession, getCurrentFocusSession, startFocusSession, submitFocusState } from '@/api/focus'
import StatCard from '@/components/admin/StatCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { FocusVisionDetector, drawFocusOverlay } from '@/utils/focusVision'

const videoRef = ref(null)
const overlayRef = ref(null)
const session = ref(null)
const cameraReady = ref(false)
const cameraError = ref('')
const modelError = ref('')
const modelLoading = ref(false)
const detectorReady = ref(false)
const endingSession = ref(false)
const logs = ref([])
const liveStats = reactive({ totalDuration: 0, effectiveDuration: 0, distractionCount: 0, awayCount: 0, phoneDuration: 0 })
const vision = reactive({
  state: 'unknown',
  stateLabel: '识别中',
  focusScore: 50,
  confidence: 0,
  posture: '',
  detectedObjects: [],
  fps: 0,
  debugMetrics: {}
})
const yoloe = reactive({
  available: false,
  checking: false,
  attempted: false,
  modelName: 'YOLOE-26M',
  latencyMs: 0,
  detections: [],
  detectedObjects: [],
  suggestedState: 'unknown',
  suggestedFocusScore: 0,
  warningType: '',
  reason: '',
  device: '',
  receivedAt: 0
})
const yoloeHistory = ref([])

let stream = null
let timer = null
let rafId = 0
let frameTimer = null
let frameCanvas = null
let detector = null
let detecting = false
let submitting = false
let frameAnalyzing = false
let lastSubmitAt = 0

const FRAME_ANALYSIS_INTERVAL_MS = 1000
const YOLOE_RESULT_TTL_MS = 4500
const YOLOE_HISTORY_LIMIT = 3
const isSessionActive = computed(() => session.value?.status === 'active')
const postureText = computed(() => {
  const map = {
    normal: '正常',
    head_down: '低头',
    screen_facing: '看屏幕',
    bad_posture: '坐姿异常',
    fatigue: '疲劳',
    away: '离座'
  }
  return map[vision.posture] || '待识别'
})
const objectText = computed(() => {
  return vision.detectedObjects.length ? vision.detectedObjects.map(labelObject).join(' / ') : '未检测到'
})
const yoloeTag = computed(() => {
  if (yoloe.checking) return { type: 'info', text: '检测中' }
  if (!yoloe.attempted) return { type: 'info', text: '待启用' }
  return yoloe.available ? { type: 'success', text: '已连接' } : { type: 'warning', text: '已降级' }
})
const yoloeMessage = computed(() => {
  if (!isSessionActive.value) return '开始学习后按节流上传压缩抽帧。'
  if (yoloe.checking && !yoloe.receivedAt) return '正在请求 YOLOE-26M 对象识别。'
  if (!yoloe.available && yoloe.attempted) return yoloe.reason || '后端模型不可用，当前仅采用端侧姿态。'
  if (yoloe.suggestedState === 'distracted_phone' && stabilizedYoloe.value.suggestedState !== 'distracted_phone') {
    return '发现手机候选目标，等待连续抽帧确认后再记录分心。'
  }
  if (stabilizedYoloe.value.suggestedState === 'distracted_phone') return '连续抽帧确认手机进入学习画面。'
  return yoloe.reason || '等待后端对象识别结果。'
})
const stabilizedYoloe = computed(() => {
  const recent = yoloeHistory.value.filter((item) => Date.now() - item.receivedAt <= YOLOE_RESULT_TTL_MS)
  const phoneHits = recent.filter((item) => item.detectedObjects.includes('mobile phone')).length
  const computerHits = recent.filter((item) => item.suggestedState === 'computer_learning').length
  const studyHits = recent.filter((item) => ['writing', 'focused'].includes(item.suggestedState) && item.detectedObjects.some((object) => ['book', 'notebook', 'pen', 'keyboard'].includes(object))).length
  let stable = null
  if (phoneHits >= 2) stable = [...recent].reverse().find((item) => item.suggestedState === 'distracted_phone')
  else if (computerHits >= 2) stable = [...recent].reverse().find((item) => item.suggestedState === 'computer_learning')
  else if (studyHits >= 2) stable = recent[recent.length - 1]
  return stable || { available: false, suggestedState: 'unknown', detectedObjects: [] }
})
const yoloeFresh = computed(() => Boolean(stabilizedYoloe.value.available))
const displayState = computed(() => {
  if (['away', 'bad_posture', 'fatigue'].includes(vision.state) || !yoloeFresh.value) {
    return { state: vision.state, label: vision.stateLabel }
  }
  const labels = {
    distracted_phone: '手机分心',
    computer_learning: '看电脑学习',
    writing: '低头书写',
    focused: '专注学习'
  }
  const state = stabilizedYoloe.value.suggestedState
  return { state, label: labels[state] || vision.stateLabel }
})
const focusScore = computed(() => {
  if (['away', 'bad_posture', 'fatigue'].includes(vision.state) || !yoloeFresh.value) return vision.focusScore || 0
  return stabilizedYoloe.value.suggestedFocusScore ?? vision.focusScore ?? 0
})
const statusMessage = computed(() => {
  if (cameraError.value) return cameraError.value
  if (modelError.value) return modelError.value
  if (modelLoading.value) return '正在加载姿态与人脸模型'
  if (detectorReady.value) return '端侧实时识别运行中'
  return '等待摄像头与模型就绪'
})
const healthTag = computed(() => {
  if (cameraError.value || modelError.value) return { type: 'warning', text: '未识别' }
  if (detectorReady.value) return { type: 'success', text: '实时识别' }
  return { type: 'info', text: '加载中' }
})
const activeAdvices = computed(() => {
  if (cameraError.value || modelError.value) return ['当前无法进行自动识别，请检查摄像头权限或网络模型资源。']
  if (!isSessionActive.value) return ['开始学习后，识别结果会自动写入状态时间线。']
  if (vision.state === 'away') return ['未检测到有效人体关键点，专注计时已暂停。']
  if (vision.state === 'bad_posture') return ['检测到坐姿或肩颈角度异常，建议调整桌椅高度。']
  if (vision.state === 'fatigue') return ['检测到低伏且动作稳定，建议短休息后再继续。']
  if (yoloeFresh.value && stabilizedYoloe.value.suggestedState === 'distracted_phone') return ['连续检测到手机，当前状态已标记为手机分心。']
  if (yoloeFresh.value && stabilizedYoloe.value.suggestedState === 'computer_learning') return ['连续检测到电脑或显示器，当前记录为看电脑学习。']
  if (vision.state === 'writing') return ['当前识别为低头书写，计入有效专注时间。']
  if (vision.state === 'computer_learning') return ['当前识别为看屏幕学习，计入有效专注时间。']
  return ['当前状态稳定，系统正在自动记录有效专注时间。']
})

function labelObject(item) {
  const map = {
    person: '人体',
    face: '人脸',
    'mobile phone': '手机',
    smartphone: '手机',
    phone: '手机',
    'cell phone': '手机',
    'handheld phone': '手机',
    'mobile device': '手机',
    book: '书本',
    'open book': '书本',
    laptop: '笔记本电脑',
    'computer monitor': '显示器',
    keyboard: '键盘',
    pen: '笔',
    pencil: '笔',
    notebook: '笔记本'
  }
  return map[item] || item
}

function formatDuration(seconds = 0) {
  const safe = Math.max(0, Number(seconds) || 0)
  const h = Math.floor(safe / 3600)
  const m = Math.floor((safe % 3600) / 60)
  const s = safe % 60
  if (h) return `${h}时${m}分`
  if (m) return `${m}分${s}秒`
  return `${s}秒`
}

function applySession(data = {}) {
  session.value = data?.id ? data : null
  logs.value = data?.logs || []
  Object.assign(liveStats, {
    totalDuration: data?.totalDuration || 0,
    effectiveDuration: data?.effectiveDuration || 0,
    distractionCount: data?.distractionCount || 0,
    awayCount: data?.awayCount || 0,
    phoneDuration: data?.phoneDuration || 0
  })
}

function applyVision(result) {
  if (!result) return
  vision.state = result.state
  vision.stateLabel = result.stateLabel
  vision.focusScore = result.focusScore
  vision.confidence = result.confidence || 0
  vision.posture = result.posture || ''
  vision.detectedObjects = result.detectedObjects || []
  vision.fps = result.fps || 0
  vision.debugMetrics = result.debugMetrics || {}
}

function resizeOverlay(result) {
  const canvas = overlayRef.value
  if (!canvas || !result?.videoSize) return
  const { width, height } = result.videoSize
  if (canvas.width !== width) canvas.width = width
  if (canvas.height !== height) canvas.height = height
}

function redrawOverlay(objectDetections = yoloe.detections) {
  const result = detector?.lastResult
  if (!result) return
  resizeOverlay(result)
  drawFocusOverlay(overlayRef.value, result, objectDetections || [])
}

async function initCamera() {
  if (cameraReady.value) return
  cameraError.value = ''
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = '当前浏览器不支持摄像头预览'
    return
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 } },
      audio: false
    })
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      await videoRef.value.play()
    }
    cameraReady.value = true
    await initDetector()
  } catch (error) {
    cameraError.value = error?.name === 'NotAllowedError' ? '摄像头权限未开启' : '摄像头启动失败'
  }
}

function stopCamera() {
  cancelDetectionLoop()
  stopFrameAnalysis()
  detector?.dispose?.()
  detector = null
  detectorReady.value = false
  modelLoading.value = false
  if (stream) stream.getTracks().forEach((track) => track.stop())
  stream = null
  if (videoRef.value) videoRef.value.srcObject = null
  cameraReady.value = false
  resetServerVision()
  const ctx = overlayRef.value?.getContext?.('2d')
  if (ctx && overlayRef.value) ctx.clearRect(0, 0, overlayRef.value.width, overlayRef.value.height)
}

async function initDetector() {
  if (!videoRef.value) return
  modelLoading.value = true
  modelError.value = ''
  try {
    detector = new FocusVisionDetector()
    await detector.init(videoRef.value)
    detectorReady.value = true
    startDetectionLoop()
    if (isSessionActive.value) startFrameAnalysis()
  } catch (error) {
    modelError.value = `模型加载失败：${error?.message || '请检查网络'}`
  } finally {
    modelLoading.value = false
  }
}

function startDetectionLoop() {
  cancelDetectionLoop()
  const loop = (timestamp) => {
    if (detectorReady.value && detector && !detecting) {
      detecting = true
      try {
        const result = detector.detectFrame(timestamp)
        if (result) {
          applyVision(result)
          resizeOverlay(result)
          drawFocusOverlay(overlayRef.value, result, yoloe.detections)
          maybeSubmitState(result)
        }
      } catch (error) {
        modelError.value = `实时识别中断：${error?.message || '未知错误'}`
        detectorReady.value = false
      } finally {
        detecting = false
      }
    }
    rafId = window.requestAnimationFrame(loop)
  }
  rafId = window.requestAnimationFrame(loop)
}

function cancelDetectionLoop() {
  if (rafId) window.cancelAnimationFrame(rafId)
  rafId = 0
}

function captureFrame() {
  const video = videoRef.value
  if (!video || !video.videoWidth || !video.videoHeight) return Promise.resolve(null)
  const maxEdge = 960
  const scale = Math.min(1, maxEdge / Math.max(video.videoWidth, video.videoHeight))
  const width = Math.max(1, Math.round(video.videoWidth * scale))
  const height = Math.max(1, Math.round(video.videoHeight * scale))
  frameCanvas ||= document.createElement('canvas')
  frameCanvas.width = width
  frameCanvas.height = height
  frameCanvas.getContext('2d')?.drawImage(video, 0, 0, width, height)
  return new Promise((resolve) => frameCanvas.toBlob(resolve, 'image/png'))
}

async function analyzeCurrentFrame() {
  if (!isSessionActive.value || !cameraReady.value || frameAnalyzing) return
  frameAnalyzing = true
  try {
    const frame = await captureFrame()
    if (!frame || !isSessionActive.value || !cameraReady.value) return
    yoloe.checking = true
    yoloe.attempted = true
    const payload = new FormData()
    payload.append('frame', frame, 'focus-frame.png')
    payload.append('sessionId', String(session.value.id))
    payload.append('clientState', vision.state)
    payload.append('clientConfidence', String(vision.confidence))
    payload.append('clientPosture', vision.posture)
    payload.append('clientFocusScore', String(vision.focusScore))
    payload.append('capturedAt', new Date().toISOString())
    const res = await analyzeFocusFrame(payload)
    if (isSessionActive.value) {
      const receivedAt = Date.now()
      const result = {
        ...res.data,
        detections: res.data.detections || [],
        detectedObjects: res.data.detectedObjects || [],
        receivedAt
      }
      Object.assign(yoloe, result)
      redrawOverlay(result.detections)
      if (result.available) {
        yoloeHistory.value = [...yoloeHistory.value, result].slice(-YOLOE_HISTORY_LIMIT)
      }
    }
  } catch (error) {
    if (isSessionActive.value) {
      yoloe.available = false
      yoloe.reason = '后端对象识别请求失败，继续使用端侧姿态。'
    }
  } finally {
    yoloe.checking = false
    frameAnalyzing = false
  }
}

function startFrameAnalysis() {
  stopFrameAnalysis()
  if (!isSessionActive.value || !cameraReady.value) return
  analyzeCurrentFrame()
  frameTimer = window.setInterval(analyzeCurrentFrame, FRAME_ANALYSIS_INTERVAL_MS)
}

function stopFrameAnalysis() {
  if (frameTimer) window.clearInterval(frameTimer)
  frameTimer = null
  frameAnalyzing = false
}

function resetServerVision() {
  Object.assign(yoloe, {
    available: false,
    checking: false,
    attempted: false,
    modelName: 'YOLOE-26M',
    latencyMs: 0,
    detections: [],
    detectedObjects: [],
    suggestedState: 'unknown',
    suggestedFocusScore: 0,
    warningType: '',
    reason: '',
    device: '',
    receivedAt: 0
  })
  yoloeHistory.value = []
}

function buildSubmittedState(result) {
  const stableYoloe = stabilizedYoloe.value
  const yoloFresh = yoloeFresh.value
  const preservePose = ['away', 'bad_posture', 'fatigue'].includes(result.state)
  let state = result.state
  let focusScore = result.focusScore
  let warningType = ['bad_posture', 'fatigue', 'away'].includes(result.state) ? result.state : ''
  let detectedObjects = [...result.detectedObjects]

  if (yoloFresh) {
    detectedObjects = [...new Set([...detectedObjects, ...stableYoloe.detectedObjects])]
    if (!preservePose && stableYoloe.suggestedState && stableYoloe.suggestedState !== 'unknown') {
      state = stableYoloe.suggestedState
      focusScore = stableYoloe.suggestedFocusScore
      warningType = stableYoloe.warningType || warningType
    }
  }
  return {
    state,
    detectedObjects,
    focusScore,
    warningType,
    visionMetadata: {
      edge: {
        state: result.state,
        confidence: result.confidence,
        posture: result.posture,
        focusScore: result.focusScore
      },
      yoloe: yoloFresh
        ? {
            available: yoloe.available,
            modelName: stableYoloe.modelName,
            device: stableYoloe.device,
            latencyMs: stableYoloe.latencyMs,
            detections: stableYoloe.detections,
            suggestedState: stableYoloe.suggestedState,
            reason: stableYoloe.reason,
            confirmationSamples: yoloeHistory.value.length
          }
        : { available: false }
    }
  }
}

async function maybeSubmitState(result) {
  if (!isSessionActive.value || endingSession.value || submitting || !result?.isStable || result.state === 'unknown') return
  if (result.state !== 'away' && result.confidence < 0.56) return
  const now = Date.now()
  if (now - lastSubmitAt < 1000) return
  lastSubmitAt = now
  submitting = true
  try {
    const fused = buildSubmittedState(result)
    const res = await submitFocusState({
      sessionId: session.value.id,
      state: fused.state,
      detectedObjects: fused.detectedObjects,
      posture: result.posture,
      focusScore: fused.focusScore,
      warningType: fused.warningType,
      visionMetadata: fused.visionMetadata
    })
    applySession(res.data.session)
  } catch (error) {
    if (isSessionActive.value && !endingSession.value) {
      console.warn('[MindNest] Stable focus state submission failed.', error)
    }
  } finally {
    submitting = false
  }
}

async function startSession() {
  resetServerVision()
  const res = await startFocusSession({ title: 'MindNest 自动专注识别' })
  applySession(res.data)
  lastSubmitAt = 0
  startTimer()
  if (!cameraReady.value) await initCamera()
  if (cameraReady.value) startFrameAnalysis()
  ElMessage.success('学习 session 已开始，系统会自动采样')
}

async function finishSession() {
  if (!isSessionActive.value) return
  endingSession.value = true
  try {
    const res = await endFocusSession(session.value.id)
    applySession(res.data)
    stopTimer()
    stopCamera()
    ElMessage.success('学习 session 已结束')
  } finally {
    endingSession.value = false
  }
}

function startTimer() {
  stopTimer()
  timer = window.setInterval(() => {
    if (isSessionActive.value) liveStats.totalDuration += 1
  }, 1000)
}

function stopTimer() {
  if (timer) window.clearInterval(timer)
  timer = null
}

function handleVisibilityChange() {
  if (document.hidden) {
    stopFrameAnalysis()
  } else if (isSessionActive.value && cameraReady.value) {
    startFrameAnalysis()
  }
}

onMounted(async () => {
  document.addEventListener('visibilitychange', handleVisibilityChange)
  const res = await getCurrentFocusSession()
  applySession(res.data)
  if (isSessionActive.value) {
    startTimer()
    initCamera()
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  stopTimer()
  stopCamera()
})
</script>

<style scoped>
.focus-page {
  padding: 28px 0 80px;
}

.focus-top,
.monitor-grid,
.detail-grid,
.stats-grid {
  display: grid;
  gap: 18px;
}

.focus-top {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  margin-bottom: 18px;
}

.eyebrow,
.focus-top h1,
.focus-top span,
h2,
p {
  margin: 0;
}

.eyebrow {
  color: var(--sm-primary);
  font-weight: 800;
}

.focus-top h1 {
  margin: 6px 0;
  font-size: 30px;
}

.focus-top span,
header p,
small,
.timeline-panel header span {
  color: var(--sm-muted);
}

.session-actions svg {
  width: 16px;
}

.monitor-grid {
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.55fr);
}

.camera-panel,
.state-panel,
.timeline-panel,
.advice-panel {
  padding: 20px;
}

.camera-panel header,
.state-panel header,
.timeline-panel header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.video-box {
  position: relative;
  overflow: hidden;
  min-height: 420px;
  border-radius: 14px;
  background: #0f172a;
}

video,
canvas {
  display: block;
  width: 100%;
  height: 420px;
  object-fit: cover;
}

canvas {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.camera-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  color: #dbeafe;
  text-align: center;
}

.camera-fallback svg {
  width: 42px;
  height: 42px;
}

.camera-fallback span {
  max-width: 300px;
  color: #93c5fd;
}

.state-panel header strong {
  padding: 5px 10px;
  border-radius: 999px;
  color: var(--sm-primary);
  background: var(--sm-soft);
}

.state-panel header strong.away,
.state-panel header strong.bad_posture,
.state-panel header strong.fatigue,
.state-panel header strong.distracted_phone {
  color: #991b1b;
  background: #fee2e2;
}

.score-ring {
  display: grid;
  place-items: center;
  align-content: center;
  width: 160px;
  height: 160px;
  margin: 8px auto 20px;
  border-radius: 50%;
  background: conic-gradient(var(--sm-primary) calc(v-bind(focusScore) * 1%), #e5e7eb 0);
  box-shadow: inset 0 0 0 18px #fff;
}

.score-ring span {
  font-size: 38px;
  font-weight: 800;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.metric-grid p {
  min-height: 66px;
  padding: 12px;
  border: 1px solid var(--sm-border);
  border-radius: 8px;
  background: #fff;
}

.metric-grid span,
.metric-grid strong {
  display: block;
}

.metric-grid span {
  color: var(--sm-muted);
  font-size: 12px;
}

.metric-grid strong {
  margin-top: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.server-vision {
  display: grid;
  gap: 10px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--sm-border);
}

.server-vision-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--sm-text-2);
  font-weight: 700;
}

.server-vision p {
  color: var(--sm-muted);
  font-size: 13px;
  line-height: 1.6;
}

.object-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.stats-grid {
  grid-template-columns: repeat(4, 1fr);
  margin: 18px 0;
}

.detail-grid {
  grid-template-columns: minmax(0, 1fr) 360px;
}

.timeline {
  display: grid;
  gap: 12px;
}

.timeline-row {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr) 48px;
  gap: 12px;
  align-items: center;
}

.timeline-row > span {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--sm-primary);
}

.timeline-row > span.fatigue {
  background: var(--sm-danger);
}

.timeline-row > span.away,
.timeline-row > span.bad_posture,
.timeline-row > span.distracted_phone {
  background: var(--sm-warning);
}

.timeline-row strong,
.timeline-row small {
  display: block;
}

.timeline-row em {
  color: var(--sm-muted);
  font-style: normal;
}

.advice-panel {
  display: grid;
  align-content: start;
  gap: 14px;
}

.advice-panel p {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  color: var(--sm-text-2);
  line-height: 1.7;
}

.advice-panel svg {
  width: 18px;
  margin-top: 4px;
  color: var(--sm-primary);
}

.debug-box {
  display: grid;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px solid var(--sm-border);
  color: var(--sm-muted);
  font-size: 13px;
}

@media (max-width: 980px) {
  .focus-top,
  .monitor-grid,
  .detail-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
