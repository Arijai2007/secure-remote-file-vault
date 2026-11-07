// Adapted from the user-supplied Stitch ANIMATION_6 export.

(function() {
  const container = document.getElementById('vault-scene');
  const devicePixelRatio = window.devicePixelRatio || 1;
  // Three.js interactive 3D Cyber Vault Scene
const width = container.clientWidth || window.innerWidth || 400;
const height = container.clientHeight || window.innerHeight || 400;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
camera.position.set(0, 0, 8);

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
} catch (error) {
  document.getElementById('fallback').hidden = false;
  document.getElementById('motion-toggle').hidden = true;
  return;
}
renderer.setSize(width, height);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);
renderer.domElement.setAttribute('aria-hidden', 'true');

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
scene.add(ambientLight);

const cyanPoint = new THREE.PointLight(0x22d3ee, 3, 20);
cyanPoint.position.set(3, 4, 4);
scene.add(cyanPoint);

const violetPoint = new THREE.PointLight(0x8b5cf6, 3, 20);
violetPoint.position.set(-3, -3, 3);
scene.add(violetPoint);

const vaultGroup = new THREE.Group();
scene.add(vaultGroup);

// 1. Translucent Glass Outer Safe Cube
const outerBoxGeo = new THREE.BoxGeometry(2.6, 2.6, 2.6);
const outerBoxMat = new THREE.MeshPhongMaterial({
  color: 0x091428,
  emissive: 0x132742,
  specular: 0x22d3ee,
  shininess: 90,
  transparent: true,
  opacity: 0.45,
  wireframe: false
});
const outerCube = new THREE.Mesh(outerBoxGeo, outerBoxMat);
vaultGroup.add(outerCube);

// Glowing wireframe cage
const wireframeGeo = new THREE.BoxGeometry(2.62, 2.62, 2.62);
const wireframeEdges = new THREE.EdgesGeometry(wireframeGeo);
const wireframeMat = new THREE.LineBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.85, linewidth: 2 });
const wireframe = new THREE.LineSegments(wireframeEdges, wireframeMat);
vaultGroup.add(wireframe);

// 2. Inner Metallic Core Safe / Enclave Lock
const coreGeo = new THREE.BoxGeometry(1.4, 1.4, 1.4);
const coreMat = new THREE.MeshPhongMaterial({
  color: 0x101b33,
  emissive: 0x06b6d4,
  specular: 0x38bdf8,
  shininess: 100
});
const coreMesh = new THREE.Mesh(coreGeo, coreMat);
vaultGroup.add(coreMesh);

// Keyhole / Lock dial ring in center
const dialGeo = new THREE.TorusGeometry(0.5, 0.08, 16, 40);
const dialMat = new THREE.MeshPhongMaterial({ color: 0x8b5cf6, emissive: 0x3b0764, specular: 0xffffff });
const dialMesh = new THREE.Mesh(dialGeo, dialMat);
dialMesh.position.z = 1.32;
vaultGroup.add(dialMesh);

// 3. Floating Orbital Cryptographic Rings
const ringGeo1 = new THREE.TorusGeometry(2.1, 0.03, 16, 80);
const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.7 });
const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
ring1.rotation.x = Math.PI / 3;
scene.add(ring1);

const ringGeo2 = new THREE.TorusGeometry(2.35, 0.02, 16, 80);
const ringMat2 = new THREE.MeshBasicMaterial({ color: 0xa855f7, transparent: true, opacity: 0.6 });
const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
ring2.rotation.y = Math.PI / 4;
ring2.rotation.x = -Math.PI / 6;
scene.add(ring2);

// 4. Floating Encryption Document / Key Tiles
const docGeo = new THREE.BoxGeometry(0.5, 0.7, 0.03);
const docMat = new THREE.MeshPhongMaterial({ color: 0x38bdf8, emissive: 0x0369a1, transparent: true, opacity: 0.85 });

const docs = [];
for (let i = 0; i < 4; i++) {
  const doc = new THREE.Mesh(docGeo, docMat.clone());
  scene.add(doc);
  docs.push({
    mesh: doc,
    angle: (i * Math.PI) / 2,
    radius: 2.7 + (i % 2) * 0.4,
    speed: 0.008 * (i % 2 === 0 ? 1 : -1),
    yOffset: (i - 1.5) * 0.6
  });
}

// 5. Encrypted Particle Stream
const particleCount = 70;
const particleGeo = new THREE.BufferGeometry();
const particlePos = new Float32Array(particleCount * 3);
for (let i = 0; i < particleCount * 3; i += 3) {
  particlePos[i] = (Math.random() - 0.5) * 7;
  particlePos[i + 1] = (Math.random() - 0.5) * 7;
  particlePos[i + 2] = (Math.random() - 0.5) * 5;
}
particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
const particleMat = new THREE.PointsMaterial({
  color: 0x34d399,
  size: 0.06,
  transparent: true,
  opacity: 0.75
});
const particles = new THREE.Points(particleGeo, particleMat);
scene.add(particles);

// Mouse interaction
let mouseX = 0;
let mouseY = 0;
let targetX = 0;
let targetY = 0;

function onMouseMove(event) {
  const rect = container.getBoundingClientRect();
  mouseX = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouseY = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
}
container.addEventListener('pointermove', onMouseMove);

function onResize() {
  const w = container.clientWidth || window.innerWidth;
  const h = container.clientHeight || window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  renderer.render(scene, camera);
}
const observer = new ResizeObserver(onResize);
observer.observe(container);

// Animation Loop
let clock = 0;
let frame = 0;
const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
let paused = motion.matches;
let lastTime = 0;
const toggle = document.getElementById('motion-toggle');
function updateToggle() {
  toggle.textContent = paused ? 'Play animation' : 'Pause animation';
  toggle.setAttribute('aria-pressed', String(paused));
}
toggle.addEventListener('click', () => { paused = !paused; updateToggle(); lastTime = 0; if (!paused) animate(); });
motion.addEventListener('change', () => { paused = motion.matches; updateToggle(); if (!paused) animate(); });
document.addEventListener('visibilitychange', () => { lastTime = 0; if (!document.hidden && !paused) animate(); });
updateToggle();
function animate(timestamp = 0) {
  cancelAnimationFrame(frame);
  if (document.hidden) return;
  if (!paused) frame = requestAnimationFrame(animate);
  const delta = lastTime ? Math.min((timestamp - lastTime) / 1000, 0.05) : 0;
  lastTime = timestamp;
  clock += delta * 0.9;

  targetX += (mouseX - targetX) * 0.05;
  targetY += (mouseY - targetY) * 0.05;

  vaultGroup.rotation.y = clock * 0.4 + targetX * 0.6;
  vaultGroup.rotation.x = Math.sin(clock * 0.5) * 0.15 - targetY * 0.4;
  vaultGroup.position.y = Math.sin(clock * 1.2) * 0.18;

  coreMesh.rotation.y = -clock * 0.6;
  coreMesh.rotation.z = Math.cos(clock * 0.8) * 0.15;

  ring1.rotation.z = clock * 0.53;
  ring1.rotation.y = clock * 0.27;
  ring2.rotation.z = -clock * 0.4;
  ring2.rotation.x = -Math.PI / 6 + clock * 0.33;

  docs.forEach((item, idx) => {
    const angle = item.angle + clock * item.speed * 67;
    item.mesh.position.x = Math.cos(angle) * item.radius;
    item.mesh.position.z = Math.sin(angle) * item.radius;
    item.mesh.position.y = item.yOffset + Math.sin(clock * 1.5 + idx) * 0.2;
    item.mesh.rotation.y = angle + Math.PI / 2;
    item.mesh.rotation.x = Math.sin(clock + idx) * 0.2;
  });

  particles.rotation.y = clock * 0.05;

  renderer.render(scene, camera);
}
animate();
window.addEventListener('pagehide', () => {
  cancelAnimationFrame(frame);
  observer.disconnect();
  scene.traverse(object => {
    if (object.geometry) object.geometry.dispose();
    if (object.material) object.material.dispose();
  });
  renderer.dispose();
}, {once: true});
})();
