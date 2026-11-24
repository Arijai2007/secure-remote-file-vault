# CodeInspector-inspired redesign implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply the approved reference style across the React website and open a verified PR.
**Architecture:** Preserve App.jsx routing, API hooks and security behavior. Introduce a standalone illustrative VaultTerminal component and a shared, consistent CSS theme.
**Tech Stack:** React 19, Vite, CSS, Vitest, existing Python API.
**Spec:** ../specs/2026-11-24-codeinspector-redesign.md (approved by user).

## Global constraints
Keep existing dependencies, accurate security claims, server-enforced behavior, role boundaries, local fonts and reduced-motion support. Streamlit and deployments are outside scope.

## Review focus
Pause/replay must work with timers; reduced motion must remain static; unavailable IntersectionObserver must leave content visible; narrow layouts must avoid page overflow; mobile menu must expose expanded state and close accessibly.

### Task 1: Terminal illustration
**Files:** Create web/src/VaultTerminal.jsx and VaultTerminal.test.jsx; integrate in App.jsx.
**Interface:** VaultTerminal({ compact = false }) returns a clearly labeled synthetic illustration with four staged rows, pause/resume and replay.
- [ ] Write tests for completion, pause/resume, replay and reduced-motion behavior, then confirm failure.
- [ ] Implement finite timer progression and cleanup with matchMedia change handling.
- [ ] Replace website Scene usage with the illustration and verify tests pass.

### Task 2: Shared visual system and layouts
**Files:** web/src/styles.css, App.jsx, web/index.html.
- [ ] Set reference tokens: canvas #07090d, panels #0f131a/#141924, mint #3df5a7, violet #8b7bff, ink #e8edf4. Use Inter headings and JetBrains Mono labels.
- [ ] Recompose landing hero, add protocol strip, preserve all truthful content, and style authentication/workspace consistently.
- [ ] Keep reveal content visible by default; enhance only when IntersectionObserver exists. Add mobile menu aria-expanded/controls, close label, Escape handling and focus management.
- [ ] Run frontend tests and production build; inspect desktop/mobile layouts and interactive states together.

### Task 3: Verification, documentation and PR
**Files:** DESIGN.md, .impeccable/design.json, README.md; visual evidence.
- [ ] Run design detector once; fix material screenshot findings in one batch and confirm once.
- [ ] Update website design docs without overwriting Streamlit's separate design truth.
- [ ] Request independent final diff review, resolve material issues, rerun affected checks.
- [ ] Commit, publish branch, and create PR against main with validation and limitations.
