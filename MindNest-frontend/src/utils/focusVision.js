import { FaceLandmarker, FilesetResolver, PoseLandmarker } from '@mediapipe/tasks-vision'

const WASM_BASE = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm'
const POSE_MODEL =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task'
const FACE_MODEL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task'
const INFERENCE_INTERVAL_MS = 90
const PERSON_CONFIDENCE_MIN = 0.55
const STATE_DWELL_MS = {
  focused: 500,
  writing: 900,
  away: 900,
  bad_posture: 1800,
  fatigue: 3000
}

const STATE_LABELS = {
  focused: '专注学习',
  writing: '低头书写',
  computer_learning: '看屏幕学习',
  away: '离开座位',
  bad_posture: '坐姿提醒',
  fatigue: '疲劳休息',
  unknown: '识别中'
}

const POSE = {
  nose: 0,
  leftEye: 2,
  rightEye: 5,
  leftEar: 7,
  rightEar: 8,
  leftShoulder: 11,
  rightShoulder: 12,
  leftElbow: 13,
  rightElbow: 14,
  leftWrist: 15,
  rightWrist: 16,
  leftHip: 23,
  rightHip: 24
}

const POSE_CONNECTIONS = [
  [POSE.leftShoulder, POSE.rightShoulder],
  [POSE.leftShoulder, POSE.leftElbow],
  [POSE.leftElbow, POSE.leftWrist],
  [POSE.rightShoulder, POSE.rightElbow],
  [POSE.rightElbow, POSE.rightWrist],
  [POSE.leftShoulder, POSE.leftHip],
  [POSE.rightShoulder, POSE.rightHip],
  [POSE.leftHip, POSE.rightHip],
  [POSE.nose, POSE.leftEye],
  [POSE.nose, POSE.rightEye],
  [POSE.leftEye, POSE.leftEar],
  [POSE.rightEye, POSE.rightEar]
]

async function createWithDelegate(factory, wasm, options) {
  try {
    return await factory(wasm, {
      ...options,
      baseOptions: {
        ...options.baseOptions,
        delegate: 'GPU'
      }
    })
  } catch (error) {
    console.warn('[MindNest] MediaPipe GPU delegate failed, falling back to CPU.', error)
    return factory(wasm, {
      ...options,
      baseOptions: {
        ...options.baseOptions,
        delegate: 'CPU'
      }
    })
  }
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

function distance(a, b) {
  if (!a || !b) return 0
  const dx = (a.x || 0) - (b.x || 0)
  const dy = (a.y || 0) - (b.y || 0)
  return Math.sqrt(dx * dx + dy * dy)
}

function visibility(point) {
  return point?.visibility ?? point?.presence ?? 0
}

function valid(point, min = 0.45) {
  return point && visibility(point) >= min
}

function avgPoint(a, b) {
  if (!a && !b) return null
  if (!a) return b
  if (!b) return a
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: ((a.z || 0) + (b.z || 0)) / 2, visibility: Math.max(visibility(a), visibility(b)) }
}

function median(items) {
  if (!items.length) return 0
  const sorted = [...items].sort((a, b) => a - b)
  return sorted[Math.floor(sorted.length / 2)]
}

function stateScore(state, confidence) {
  const base = {
    focused: 88,
    writing: 84,
    computer_learning: 80,
    bad_posture: 64,
    fatigue: 36,
    away: 8,
    unknown: 50
  }[state] ?? 50
  return clamp(Math.round(base * (0.72 + confidence * 0.28)), 0, 100)
}

function stabilizeState(rawState, memory, timestamp) {
  if (memory.candidateState !== rawState) {
    memory.candidateState = rawState
    memory.candidateSince = timestamp
  }

  if (rawState === memory.lastStableState) {
    return { state: rawState, isStable: true }
  }

  const dwell = STATE_DWELL_MS[rawState] ?? 900
  if (timestamp - memory.candidateSince >= dwell) {
    memory.lastStableState = rawState
    return { state: rawState, isStable: true }
  }

  return {
    state: memory.lastStableState || 'unknown',
    isStable: false
  }
}

function analyzePose(poseLandmarks, faceResult, memory, timestamp) {
  const now = timestamp || performance.now()
  const pose = poseLandmarks?.[0] || []
  const faceDetected = Boolean(faceResult?.faceLandmarks?.length)
  const nose = pose[POSE.nose]
  const leftShoulder = pose[POSE.leftShoulder]
  const rightShoulder = pose[POSE.rightShoulder]
  const leftEye = pose[POSE.leftEye]
  const rightEye = pose[POSE.rightEye]
  const hips = [pose[POSE.leftHip], pose[POSE.rightHip]]
  const core = [nose, leftShoulder, rightShoulder, ...hips]
  const visibleCore = core.filter((item) => valid(item, 0.45))
  const personConfidence = visibleCore.length ? visibleCore.reduce((sum, item) => sum + visibility(item), 0) / visibleCore.length : 0
  const shouldersVisible = valid(leftShoulder, PERSON_CONFIDENCE_MIN) && valid(rightShoulder, PERSON_CONFIDENCE_MIN)
  const headVisible = valid(nose, PERSON_CONFIDENCE_MIN) || (valid(leftEye, PERSON_CONFIDENCE_MIN) && valid(rightEye, PERSON_CONFIDENCE_MIN))
  const hipVisible = hips.some((item) => valid(item, 0.48))
  const personPresent =
    shouldersVisible &&
    headVisible &&
    personConfidence >= PERSON_CONFIDENCE_MIN &&
    (faceDetected || hipVisible || personConfidence >= 0.68)

  if (!personPresent) {
    const stable = stabilizeState('away', memory, now)
    const confidence = clamp(1 - personConfidence, 0.05, 1)
    return {
      state: stable.state,
      stateLabel: STATE_LABELS[stable.state],
      focusScore: stateScore(stable.state, confidence),
      confidence,
      posture: 'away',
      detectedObjects: [],
      isStable: stable.isStable,
      landmarks: pose,
      faceLandmarks: faceResult?.faceLandmarks?.[0] || [],
      debugMetrics: {
        personConfidence: Number(personConfidence.toFixed(2)),
        faceDetected,
        rawState: 'away'
      }
    }
  }

  const shoulderCenter = avgPoint(leftShoulder, rightShoulder)
  const hipCenter = avgPoint(pose[POSE.leftHip], pose[POSE.rightHip])
  const eyeCenter = avgPoint(leftEye, rightEye) || nose
  const shoulderWidth = Math.max(0.05, distance(leftShoulder, rightShoulder))
  const torsoLength = Math.max(0.05, distance(shoulderCenter, hipCenter))
  const headDrop = shoulderCenter && eyeCenter ? (eyeCenter.y - shoulderCenter.y) / torsoLength : 0
  const noseDrop = shoulderCenter && nose ? (nose.y - shoulderCenter.y) / torsoLength : 0
  const shoulderSlope = leftShoulder && rightShoulder ? Math.abs(leftShoulder.y - rightShoulder.y) / shoulderWidth : 0
  const headSide = shoulderCenter && nose ? Math.abs(nose.x - shoulderCenter.x) / shoulderWidth : 0
  const headShoulderDistance = shoulderCenter && nose ? distance(nose, shoulderCenter) / torsoLength : 0

  const wrists = [pose[POSE.leftWrist], pose[POSE.rightWrist]].filter((item) => valid(item, 0.28))
  const handsLow = wrists.some((item) => shoulderCenter && item.y > shoulderCenter.y + torsoLength * 0.22)
  const headLow = headDrop > -0.3 || noseDrop > -0.12
  const headVeryLow = headDrop > -0.08 || headShoulderDistance < 0.3
  const postureTilt = shoulderSlope > 0.3 || headSide > 0.85

  const headY = nose?.y || eyeCenter?.y || 0
  const lastHeadY = memory.lastHeadY ?? headY
  const motion = Math.abs(headY - lastHeadY)
  memory.lastHeadY = headY
  memory.motionHistory.push(motion)
  if (memory.motionHistory.length > 30) memory.motionHistory.shift()
  const motionMedian = median(memory.motionHistory)

  let rawState = 'focused'
  let posture = 'normal'
  if (headVeryLow && motionMedian < 0.003) {
    rawState = 'fatigue'
    posture = 'fatigue'
  } else if (postureTilt) {
    rawState = 'bad_posture'
    posture = 'bad_posture'
  } else if (headLow && handsLow && !postureTilt) {
    rawState = 'writing'
    posture = 'head_down'
  }

  const stable = stabilizeState(rawState, memory, now)
  const confidence = clamp(personConfidence * 0.7 + (faceDetected ? 0.18 : 0.05) + (stable.isStable ? 0.08 : 0), 0, 1)

  return {
    state: stable.state,
    stateLabel: STATE_LABELS[stable.state] || STATE_LABELS.unknown,
    focusScore: stateScore(stable.state, confidence),
    confidence,
    posture,
    isStable: stable.isStable,
    detectedObjects: faceDetected ? ['person', 'face'] : ['person'],
    landmarks: pose,
    faceLandmarks: faceResult?.faceLandmarks?.[0] || [],
    debugMetrics: {
      rawState,
      personConfidence: Number(personConfidence.toFixed(2)),
      faceDetected,
      headDrop: Number(headDrop.toFixed(2)),
      shoulderSlope: Number(shoulderSlope.toFixed(2)),
      headSide: Number(headSide.toFixed(2)),
      motion: Number(motionMedian.toFixed(4))
    }
  }
}

export class FocusVisionDetector {
  constructor(options = {}) {
    this.options = options
    this.poseLandmarker = null
    this.faceLandmarker = null
    this.video = null
    this.memory = {
      awaySince: 0,
      lastHeadY: 0,
      motionHistory: [],
      candidateState: 'unknown',
      candidateSince: 0,
      lastStableState: 'unknown'
    }
    this.frameTimes = []
    this.lastResult = null
    this.lastInferenceAt = 0
  }

  async init(video) {
    this.video = video
    const wasm = await FilesetResolver.forVisionTasks(this.options.wasmBase || WASM_BASE)
    const [poseLandmarker, faceLandmarker] = await Promise.all([
      createWithDelegate(PoseLandmarker.createFromOptions, wasm, {
        baseOptions: {
          modelAssetPath: this.options.poseModel || POSE_MODEL
        },
        runningMode: 'VIDEO',
        numPoses: 1,
        minPoseDetectionConfidence: 0.55,
        minPosePresenceConfidence: 0.55,
        minTrackingConfidence: 0.5
      }),
      createWithDelegate(FaceLandmarker.createFromOptions, wasm, {
        baseOptions: {
          modelAssetPath: this.options.faceModel || FACE_MODEL
        },
        runningMode: 'VIDEO',
        numFaces: 1,
        minFaceDetectionConfidence: 0.58,
        minFacePresenceConfidence: 0.58,
        minTrackingConfidence: 0.55
      })
    ])
    this.poseLandmarker = poseLandmarker
    this.faceLandmarker = faceLandmarker
    return true
  }

  detectFrame(timestamp = performance.now()) {
    if (!this.video || !this.poseLandmarker || !this.faceLandmarker) return null
    if (this.video.readyState < 2 || !this.video.videoWidth || !this.video.videoHeight) return null
    if (timestamp - this.lastInferenceAt < INFERENCE_INTERVAL_MS) return null
    this.lastInferenceAt = timestamp
    const poseResult = this.poseLandmarker.detectForVideo(this.video, timestamp)
    const faceResult = this.faceLandmarker.detectForVideo(this.video, timestamp)
    const result = analyzePose(poseResult.landmarks, faceResult, this.memory, timestamp)
    this.frameTimes.push(timestamp)
    while (this.frameTimes.length > 2 && timestamp - this.frameTimes[0] > 1000) this.frameTimes.shift()
    result.fps = this.frameTimes.length > 1 ? Math.round(((this.frameTimes.length - 1) * 1000) / (timestamp - this.frameTimes[0] || 1)) : 0
    result.videoSize = { width: this.video.videoWidth, height: this.video.videoHeight }
    this.lastResult = result
    return result
  }

  dispose() {
    this.poseLandmarker?.close?.()
    this.faceLandmarker?.close?.()
    this.poseLandmarker = null
    this.faceLandmarker = null
    this.video = null
  }
}

function objectLabel(label) {
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
  return map[label] || label
}

function drawObjectDetections(ctx, width, height, detections = []) {
  if (!detections.length) return
  const sourceWidth = detections.find((item) => item.imageWidth)?.imageWidth || Math.max(...detections.map((item) => (item.bbox?.x || 0) + (item.bbox?.width || 0)), 1)
  const sourceHeight = detections.find((item) => item.imageHeight)?.imageHeight || Math.max(...detections.map((item) => (item.bbox?.y || 0) + (item.bbox?.height || 0)), 1)
  const scaleX = width / sourceWidth
  const scaleY = height / sourceHeight
  ctx.save()
  ctx.lineWidth = 4
  ctx.font = '700 14px Microsoft YaHei, sans-serif'
  ctx.shadowColor = 'rgba(15, 23, 42, 0.35)'
  ctx.shadowBlur = 8
  for (const item of detections) {
    const box = item.bbox
    if (!box || !box.width || !box.height) continue
    const label = item.label || ''
    const isPhone = ['mobile phone', 'smartphone', 'phone', 'cell phone', 'handheld phone', 'mobile device'].includes(label)
    const colorMap = {
      'mobile phone': '#ef4444',
      smartphone: '#ef4444',
      phone: '#ef4444',
      'cell phone': '#ef4444',
      'computer monitor': '#2563eb',
      laptop: '#2563eb',
      keyboard: '#0f766e',
      book: '#7c3aed',
      notebook: '#7c3aed',
      pen: '#f59e0b',
      pencil: '#f59e0b',
      person: '#22c55e'
    }
    const color = colorMap[label] || (isPhone ? '#ef4444' : '#38bdf8')
    const x = box.x * scaleX
    const y = box.y * scaleY
    const w = box.width * scaleX
    const h = box.height * scaleY
    ctx.strokeStyle = color
    ctx.fillStyle = color
    ctx.globalAlpha = 0.14
    ctx.fillRect(x, y, w, h)
    ctx.globalAlpha = 1
    ctx.strokeRect(x, y, w, h)
    const text = `${objectLabel(label)} ${Math.round((item.confidence || 0) * 100)}%`
    const metrics = ctx.measureText(text)
    const labelWidth = Math.max(64, Math.min(metrics.width + 16, width - x - 4))
    const labelY = y > 30 ? y - 28 : y + 4
    ctx.fillRect(x, labelY, labelWidth, 22)
    ctx.fillStyle = '#fff'
    ctx.shadowBlur = 0
    ctx.fillText(text, x + 8, labelY + 15)
    ctx.shadowBlur = 8
    ctx.fillStyle = color
  }
  ctx.restore()
}

export function drawFocusOverlay(canvas, result, objectDetections = []) {
  const ctx = canvas?.getContext?.('2d')
  if (!ctx || !result) return
  const width = canvas.width
  const height = canvas.height
  ctx.clearRect(0, 0, width, height)
  const landmarks = result.landmarks || []
  ctx.lineWidth = 3
  ctx.strokeStyle = result.state === 'away' ? '#f59e0b' : result.state === 'bad_posture' || result.state === 'fatigue' ? '#ef4444' : '#22c55e'
  ctx.fillStyle = ctx.strokeStyle

  if (result.detectedObjects?.includes('person')) for (const [a, b] of POSE_CONNECTIONS) {
    const pa = landmarks[a]
    const pb = landmarks[b]
    if (!valid(pa, 0.25) || !valid(pb, 0.25)) continue
    ctx.beginPath()
    ctx.moveTo(pa.x * width, pa.y * height)
    ctx.lineTo(pb.x * width, pb.y * height)
    ctx.stroke()
  }

  if (result.detectedObjects?.includes('person')) for (const point of landmarks) {
    if (!valid(point, 0.35)) continue
    ctx.beginPath()
    ctx.arc(point.x * width, point.y * height, 3.5, 0, Math.PI * 2)
    ctx.fill()
  }

  drawObjectDetections(ctx, width, height, objectDetections)

  ctx.save()
  ctx.font = '600 16px Microsoft YaHei, sans-serif'
  ctx.fillStyle = 'rgba(15, 23, 42, 0.72)'
  ctx.fillRect(14, 14, 230, 70)
  ctx.fillStyle = '#fff'
  ctx.fillText(result.stateLabel || '识别中', 28, 42)
  ctx.font = '12px Microsoft YaHei, sans-serif'
  ctx.fillText(`置信度 ${Math.round((result.confidence || 0) * 100)}% · ${result.fps || 0} FPS`, 28, 64)
  ctx.restore()
}

export const focusStateLabels = STATE_LABELS
