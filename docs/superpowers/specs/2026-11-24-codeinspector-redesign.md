# CipherVault visual redesign

## Intent
Apply CodeInspectorAi's recognizable visual language across the existing React landing page, authentication, and workspace. Deliver a coherent, attractive website and a reviewed pull request, with desktop and mobile layout evidence.

## Approaches
1. Full reference adaptation: carry near-black/mint/violet tokens, Inter/JetBrains Mono typography, grid atmosphere, terminal presentation, and purposeful motion across all three surfaces. Recommended and selected by the user.
2. Landing/sign-in only: less scope but leaves a visually inconsistent signed-in experience.
3. Theme/motion only: minimizes composition changes but leaves the landing page's existing 3D-led identity.

## Design
Use #07090d canvas, #0f131a panels, #141924 raised surfaces, #3df5a7 primary actions, #8b7bff secondary accents, #e8edf4 text, and readable muted text. Use locally bundled Inter for UI/headings and JetBrains Mono for technical labels. Match the reference's restrained borders, compact controls, and 14px panel corners.

Landing: sticky navigation, subtle grid with mint/violet illumination, strong two-column headline and actions, and a terminal-style sample encryption walkthrough. Its filename and activity are explicitly illustrative, with no real secrets or files. Show staged upload/encryption/key-wrapping/verification steps, pause/replay controls, and a static reduced-motion view. Keep existing feature, workflow, role and limitation content; improve hierarchy, spacing and mobile stacking.

Sign-in: matching grid atmosphere and terminal/identity illustration alongside the existing setup/login card. Preserve enrollment QR, validation, password semantics, TOTP and recoverable error handling. Consistent focus rings and clear form hierarchy.

Workspace: compact dark sidebar with mint selected navigation, quiet topbar, readable page headings, consistent cards/metrics, tables, inspector, upload and empty/error states. Retain all role-aware actions. Improve small-screen navigation, stacking, table scrolling, long filename wrapping, and touch target sizes. Add accessible menu state attributes.

Motion: staged illustrative rows, short hover transitions and one-time section reveals. Avoid global pointer tracking, unbounded expensive effects, and hiding content when observation is unavailable. Honor reduced motion and offer pause for repeating decorative animation. No animation should imply a real file was processed.

## Constraints and boundaries
Keep React/Vite and existing dependencies. No backend behavior changes or deployment. Streamlit styling is outside this website redesign. Preserve all security claims and warnings. Keep licensed local fonts. Additional elements are presentational and clearly labeled where synthetic.

## Verification
Run existing frontend tests and production build. Add targeted tests for new pause/replay and fallback behavior. Inspect landing, sign-in and representative signed-in pages at desktop and mobile sizes using isolated local test data; check overflow, keyboard navigation, mobile menu, forms and reduced motion. Capture representative evidence for the PR. Run the design detector once, review the final diff, commit and open a PR against main.

## Builder decisions
Exact spacing, icon sizes, animation timings, and responsive breakpoints follow the reference and can be settled during implementation. The user approved both the overall scope and this design brief on 2026-11-24.
