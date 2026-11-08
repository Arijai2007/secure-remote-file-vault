const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

// Exercise the real animation controller with a deterministic clock. Rendering
// is stubbed so the motion lifecycle can be checked without a GPU or browser.
function controller() {
  const source = fs.readFileSync(path.join(__dirname, '../assets/vault-scene.js'), 'utf8');
  const loop = source.slice(source.indexOf('// Animation Loop'), source.lastIndexOf('})();'));
  const frames = new Map();
  const events = {};
  let nextFrame = 0;
  const motion = { matches: false, addEventListener: (name, cb) => { events.motion = cb; } };
  const toggle = { setAttribute() {}, addEventListener: (name, cb) => { events.toggle = cb; } };
  const object = () => ({ rotation: {}, position: {} });
  const document = { hidden: false, getElementById: () => toggle,
    addEventListener: (name, cb) => { events[name] = cb; } };
  const context = vm.createContext({
    window: { matchMedia: () => motion, addEventListener() {} }, document,
    requestAnimationFrame: cb => { frames.set(++nextFrame, cb); return nextFrame; },
    cancelAnimationFrame: id => frames.delete(id),
    targetX: 0, targetY: 0, mouseX: 0, mouseY: 0,
    vaultGroup: object(), coreMesh: object(), ring1: object(), ring2: object(),
    particles: object(), docs: [], renderer: { render() {}, dispose() {} },
    observer: { disconnect() {} }, scene: { traverse() {} }, camera: {},
  });
  vm.runInContext(loop, context);
  return {
    frames, events, motion, document,
    state: () => vm.runInContext('({ clock, paused, lastTime })', context),
    tick(timestamp) {
      const [id, cb] = frames.entries().next().value;
      frames.delete(id);
      cb(timestamp);
    },
  };
}

test('reduced-motion changes cancel pending animation and resume without rewinding', () => {
  const c = controller();
  c.tick(1000);
  c.tick(1032);
  const clock = c.state().clock;
  c.motion.matches = true;
  c.events.motion();
  assert.equal(c.frames.size, 0, 'pausing must cancel the already queued frame');
  c.motion.matches = false;
  c.events.motion();
  assert.equal(c.state().clock, clock, 'resuming must not subtract the previous RAF timestamp');
  assert.equal(c.frames.size, 1);
  c.tick(5000);
  c.tick(5032);
  assert.ok(c.state().clock > clock);
});

test('manual pause and hidden-page transitions leave only one animation loop', () => {
  const c = controller();
  c.tick(1000);
  c.tick(1032);
  c.events.toggle();
  assert.equal(c.state().paused, true);
  assert.equal(c.frames.size, 0);
  c.events.toggle();
  assert.equal(c.frames.size, 1);
  c.document.hidden = true;
  c.events.visibilitychange();
  assert.equal(c.frames.size, 0);
  c.document.hidden = false;
  c.events.visibilitychange();
  assert.equal(c.frames.size, 1);
});
