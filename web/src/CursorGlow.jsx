import React, { useEffect, useRef } from 'react'

// Same fixed radial spotlight and viewport pointer coordinates as CodeInspectorAi.
export default function CursorGlow() {
  const glow = useRef(null)
  useEffect(() => {
    const motion = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    const pointer = window.matchMedia?.('(hover: hover) and (pointer: fine)')
    if (!motion || !pointer) return
    let frame = 0
    let x = 0, y = 0
    const hide = () => { if (glow.current) glow.current.style.opacity = '0' }
    const move = event => {
      if (motion.matches || !pointer.matches || event.pointerType === 'touch') return
      x = event.clientX; y = event.clientY
      if (frame) return
      frame = requestAnimationFrame(() => {
        frame = 0
        if (!glow.current) return
        glow.current.style.setProperty('--mx', x + 'px')
        glow.current.style.setProperty('--my', y + 'px')
        glow.current.style.opacity = '1'
      })
    }
    const reset = () => { cancelAnimationFrame(frame); frame = 0; hide() }
    window.addEventListener('pointermove', move, { passive: true })
    document.documentElement.addEventListener('pointerleave', reset)
    window.addEventListener('blur', reset)
    motion.addEventListener('change', reset)
    pointer.addEventListener('change', reset)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('pointermove', move)
      document.documentElement.removeEventListener('pointerleave', reset)
      window.removeEventListener('blur', reset)
      motion.removeEventListener('change', reset)
      pointer.removeEventListener('change', reset)
    }
  }, [])
  return <div ref={glow} className="cursor-glow" aria-hidden="true"/>
}
