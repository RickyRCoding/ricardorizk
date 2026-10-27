<template>
  <canvas ref="canvasRef" class="interactive-background"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)

const CELL = 22
const CURSOR_RADIUS = 190
const GLYPHS = ['·', ':', '-', '+', '=', '*', '#', '@']

let animationFrameId = null
let width = 0
let height = 0
let dpr = 1
let cols = 0
let rows = 0
let cells = []
let pulses = []
let time = 0

let baseColor = '#fbfbfa'
const inkRgb = '17, 17, 17'
const accentRgb = '217, 78, 52'

const pointer = {
  x: -9999,
  y: -9999,
  vx: 0,
  vy: 0,
  speed: 0,
  active: false
}

let lastScrollY = 0
let scrollOffset = 0

function detectPalette() {
  const styles = getComputedStyle(document.documentElement)
  const bgPrimary = styles.getPropertyValue('--bg-primary').trim()
  if (bgPrimary) {
    baseColor = bgPrimary
  }
}

function initGrid() {
  const canvas = canvasRef.value
  if (!canvas) return

  dpr = Math.min(window.devicePixelRatio || 1, 2)
  width = window.innerWidth
  height = window.innerHeight

  canvas.width = width * dpr
  canvas.height = height * dpr

  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  cols = Math.ceil(width / CELL) + 1
  rows = Math.ceil(height / CELL) + 1

  const offsetX = (width - (cols - 1) * CELL) / 2
  const offsetY = (height - (rows - 1) * CELL) / 2

  cells = new Array(rows * cols)
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      cells[r * cols + c] = {
        x: offsetX + c * CELL,
        y: offsetY + r * CELL,
        r,
        c,
        energy: 0
      }
    }
  }
}

function onMouseMove(e) {
  const nx = e.clientX
  const ny = e.clientY
  if (pointer.active) {
    const dx = nx - pointer.x
    const dy = ny - pointer.y
    pointer.vx = dx
    pointer.vy = dy
    pointer.speed = Math.min(40, Math.sqrt(dx * dx + dy * dy))
  }
  pointer.x = nx
  pointer.y = ny
  pointer.active = true
}

function onMouseDown(e) {
  pointer.x = e.clientX
  pointer.y = e.clientY
  pointer.active = true
  pulses.push({
    x: e.clientX,
    y: e.clientY,
    radius: 0,
    maxRadius: 420,
    speed: 9.5
  })
}

function onMouseLeave() {
  pointer.active = false
  pointer.x = -9999
  pointer.y = -9999
  pointer.vx = 0
  pointer.vy = 0
  pointer.speed = 0
}

function onScroll() {
  const currentScrollY = window.scrollY || 0
  const delta = currentScrollY - lastScrollY
  lastScrollY = currentScrollY
  scrollOffset += delta * 0.012
}

function onResize() {
  detectPalette()
  initGrid()
}

function sampleField(c, r, t) {
  const nx = c * 0.085
  const ny = r * 0.085 + scrollOffset
  const w1 = Math.sin(nx * 1.3 + t * 0.65 + Math.cos(ny * 1.1 - t * 0.45))
  const w2 = Math.cos(ny * 1.5 - t * 0.55 + Math.sin(nx * 0.9 + t * 0.35))
  const w3 = Math.sin((nx + ny) * 0.75 - t * 0.4)
  return (w1 + w2 + w3) / 3
}

function step() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  time += 0.016

  ctx.fillStyle = baseColor
  ctx.fillRect(0, 0, width, height)

  for (let i = pulses.length - 1; i >= 0; i--) {
    const p = pulses[i]
    p.radius += p.speed
    if (p.radius >= p.maxRadius) {
      pulses.splice(i, 1)
    }
  }

  pointer.speed *= 0.9

  ctx.font = '500 11px "JetBrains Mono", "SFMono-Regular", Menlo, Monaco, Consolas, monospace'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  const rSq = CURSOR_RADIUS * CURSOR_RADIUS

  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i]
    const wave = (sampleField(cell.c, cell.r, time) + 1) * 0.5

    let targetEnergy = 0
    let angleGlyph = null

    if (pointer.active) {
      const dx = cell.x - pointer.x
      const dy = cell.y - pointer.y
      const distSq = dx * dx + dy * dy
      if (distSq < rSq) {
        const dist = Math.sqrt(distSq)
        const falloff = 1 - dist / CURSOR_RADIUS
        targetEnergy = falloff * falloff * (0.75 + pointer.speed * 0.015)

        if (dist > 14 && dist < 85 && pointer.speed > 2.5) {
          const angle = Math.atan2(dy, dx)
          const norm = ((angle + Math.PI) / (Math.PI * 2)) * 4
          const dirIdx = Math.round(norm) % 4
          angleGlyph = ['—', '\\', '|', '/'][dirIdx]
        }
      }
    }

    let pulseHit = 0
    for (let p = 0; p < pulses.length; p++) {
      const pw = pulses[p]
      const dx = cell.x - pw.x
      const dy = cell.y - pw.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const band = Math.abs(dist - pw.radius)
      const bw = 34
      if (band < bw) {
        const fade = (1 - band / bw) * (1 - pw.radius / pw.maxRadius)
        if (fade > pulseHit) pulseHit = fade
      }
    }

    if (pulseHit > targetEnergy) {
      targetEnergy = pulseHit
    }

    if (targetEnergy > cell.energy) {
      cell.energy += (targetEnergy - cell.energy) * 0.35
    } else {
      cell.energy *= 0.91
    }

    const combined = Math.min(1, wave * 0.42 + cell.energy * 0.85)

    if (combined < 0.22 && (cell.r + cell.c) % 2 !== 0) {
      continue
    }

    let glyph
    if (angleGlyph && cell.energy > 0.35) {
      glyph = angleGlyph
    } else {
      const idx = Math.min(GLYPHS.length - 1, Math.floor(combined * GLYPHS.length))
      glyph = GLYPHS[idx]
    }

    if (cell.energy > 0.28 || pulseHit > 0.2) {
      const alpha = Math.min(0.82, 0.22 + cell.energy * 0.65)
      ctx.fillStyle = `rgba(${accentRgb}, ${alpha.toFixed(3)})`
    } else {
      const alpha = 0.045 + Math.pow(combined, 1.6) * 0.22
      ctx.fillStyle = `rgba(${inkRgb}, ${alpha.toFixed(3)})`
    }

    ctx.fillText(glyph, cell.x, cell.y)
  }

  animationFrameId = requestAnimationFrame(step)
}

onMounted(() => {
  lastScrollY = window.scrollY || 0
  detectPalette()
  initGrid()

  window.addEventListener('mousemove', onMouseMove, { passive: true })
  window.addEventListener('mousedown', onMouseDown, { passive: true })
  window.addEventListener('mouseleave', onMouseLeave, { passive: true })
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onResize, { passive: true })

  animationFrameId = requestAnimationFrame(step)
})

onUnmounted(() => {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
  }
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mousedown', onMouseDown)
  window.removeEventListener('mouseleave', onMouseLeave)
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.interactive-background {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
  display: block;
}
</style>
