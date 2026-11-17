import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { Pause, Play } from 'lucide-react'

export default function VaultScene({ compact = false }) {
  const mount = useRef(null)
  const paused = useRef(false)
  const [isPaused, setPaused] = useState(false)
  const [fallback, setFallback] = useState(false)

  useEffect(() => {
    const host = mount.current
    if (!host) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
    let renderer
    try { renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' }) }
    catch { setFallback(true); return }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    host.appendChild(renderer.domElement)
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(42, 1, .1, 100)
    camera.position.z = 8.6
    scene.add(new THREE.AmbientLight(0x8aaac7, 1.4))
    const cyan = new THREE.PointLight(0x36d9ed, 80); cyan.position.set(3, 3, 5); scene.add(cyan)
    const violet = new THREE.PointLight(0xa78bfa, 55); violet.position.set(-4, -2, 4); scene.add(violet)
    const group = new THREE.Group(); scene.add(group)
    const coreGeometry = new THREE.IcosahedronGeometry(1.4, 1)
    const core = new THREE.Mesh(coreGeometry, new THREE.MeshPhongMaterial({ color: 0x17263a, emissive: 0x07121e, flatShading: true, shininess: 90 }))
    group.add(core)
    const cage = new THREE.Mesh(coreGeometry, new THREE.MeshBasicMaterial({ color: 0x36d9ed, wireframe: true, transparent: true, opacity: .45 }))
    cage.scale.setScalar(1.025); group.add(cage)
    const ringGeometry = new THREE.TorusGeometry(2.15, .022, 8, 100)
    const ringA = new THREE.Mesh(ringGeometry, new THREE.MeshBasicMaterial({ color: 0x36d9ed, transparent: true, opacity: .7 }))
    ringA.rotation.x = Math.PI / 3; group.add(ringA)
    const ringB = new THREE.Mesh(new THREE.TorusGeometry(2.7, .018, 8, 110), new THREE.MeshBasicMaterial({ color: 0xa78bfa, transparent: true, opacity: .6 }))
    ringB.rotation.x = -Math.PI / 4; ringB.rotation.y = Math.PI / 5; group.add(ringB)
    const tiles = []
    for (let i = 0; i < 9; i++) {
      const tile = new THREE.Mesh(new THREE.BoxGeometry(.18, .25, .025), new THREE.MeshPhongMaterial({ color: i % 2 ? 0x9b8bd7 : 0x5cd5e8 }))
      group.add(tile); tiles.push(tile)
    }
    const resize = () => { const w = host.clientWidth || 500; const h = host.clientHeight || 400; renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix() }
    const observer = new ResizeObserver(resize); observer.observe(host); resize()
    let frame, t = 0
    const draw = () => {
      if (!paused.current && !reduced.matches) {
        t += .006
        core.rotation.y += .004; core.rotation.x += .002
        cage.rotation.y -= .003
        ringA.rotation.z += .004; ringB.rotation.z -= .003
        tiles.forEach((tile, i) => { const a = t + i * Math.PI * 2 / tiles.length; tile.position.set(Math.cos(a) * 2.42, Math.sin(a * 1.8) * .7, Math.sin(a) * 2.42); tile.rotation.y = a })
      }
      renderer.render(scene, camera)
      frame = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(frame); observer.disconnect(); host.removeChild(renderer.domElement); renderer.dispose(); coreGeometry.dispose(); ringGeometry.dispose(); group.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose() }) }
  }, [])

  return <div className={'scene-shell' + (compact ? ' compact' : '')}>
    <div ref={mount} className="scene-canvas" aria-hidden="true" />
    {fallback && <div className="scene-fallback">◇<span>Encrypted vault core</span></div>}
    <div className="scene-label mono">AES-256-GCM · RSA-3072 OAEP</div>
    <button className="scene-toggle" onClick={() => { paused.current = !paused.current; setPaused(paused.current) }} aria-label={isPaused ? 'Resume animation' : 'Pause animation'}>{isPaused ? <Play size={15}/> : <Pause size={15}/>} {isPaused ? 'Resume' : 'Pause'}</button>
  </div>
}
