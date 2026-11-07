---
name: CipherVault
description: Native Streamlit adaptation of the supplied CipherVault sign-in and file workspace.
colors:
  canvas: "#0e1321"
  nav: "#090e1c"
  panel: "#1a1f2e"
  raised: "#252a39"
  ink: "#dee2f6"
  muted: "#a6b4ca"
  cyan: "#22d3ee"
  violet: "#d0bcff"
  border: "#30394e"
  success: "#62e0ba"
  danger: "#ffb4ab"
typography:
  display:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "clamp(2.25rem, 3.4vw, 3.8rem)"
    lineHeight: 1.1
    letterSpacing: "-.025em"
  headline:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "1.85rem"
    letterSpacing: "-.025em"
  title:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "1.15rem"
    letterSpacing: "-.025em"
  body:
    fontFamily: "Inter, sans-serif"
    lineHeight: 1.6
  mono:
    fontFamily: "JetBrains Mono, monospace"
rounded:
  control: "8px"
  input: "9px"
  inset: "12px"
  card: "16px"
  feature: "18px"
  form: "20px"
spacing:
  inline: "12px"
  inset: "1rem"
  card: "1.25rem"
  form: "1.8rem"
  feature: "2rem"
components:
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
  input:
    backgroundColor: "{colors.nav}"
    textColor: "{colors.ink}"
    rounded: "{rounded.input}"
  navigation-active:
    backgroundColor: "{colors.cyan}"
    textColor: "#00252e"
    rounded: "{rounded.control}"
    padding: ".65rem .8rem"
  file-card:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.card}"
---

# Design System: CipherVault

## Overview

The visual authority is the user-supplied `stitch_ciphervault_ui_design_system.zip`: the File Vault and animated Sign In / Unlock screens. This implementation adapts the export to native Streamlit controls and real vault data. Navy surfaces, cyan actions, violet accents, geometric headings and monospaced cryptographic metadata carry the supplied identity. No additional creative metaphor is established.

The sign-in illustration and workspace lock artwork carry the vault motif; working controls stay native Streamlit widgets. Sources of truth are `ui.css`, `ui.py`, `.streamlit/config.toml` and the layout in `app.py`. Product and security facts remain in `README.md` and `vault.py`.

**Key Characteristics:**

- Dark tonal layers with cyan interaction emphasis.
- Rounded file cards, inset metadata and a separate cryptographic inspector.
- Locally bundled type and an isolated animated sign-in vault.
- Role-aware controls and truthful verification states.

## Colors

Frontmatter records the reused CSS custom properties. Gradients and interaction treatments remain in the sidecar component snippets.

### Primary

- **Cyan:** actions, selected sidebar rows, caret, keyboard focus and illustrative highlights.

### Secondary

- **Violet:** the primary-action gradient endpoint and sharing/role accent family.

### Neutral

- **Canvas / Nav:** page backdrop and darker sidebar, fields and metadata insets.
- **Panel / Raised:** cards and forms, then secondary controls.
- **Ink / Muted:** primary text, then captions and metadata labels.
- **Border:** separation between controls and surfaces.
- **Success / Danger:** activity outcomes, paired with visible outcome text.

## Typography

Space Grotesk carries headings, the wordmark and metric values; Inter carries controls and prose; JetBrains Mono carries code, protocol names and cryptographic values. Latin font subsets are bundled with their SIL Open Font Licenses. System fallbacks cover other scripts.

Display type belongs to the sign-in story; at the narrow breakpoint it becomes a fixed size (2.4rem). Headline and title roles describe standard h2 and h3, with component-specific overrides for form titles and file names. The page h1 is smaller (1.65rem). Cryptographic values and metrics use tabular numerals. Story prose is constrained (52ch); long filenames and metadata wrap rather than truncate identifiers.

## Layout

The content container caps its width (1520px), with desktop padding (4rem 2rem 2rem). Sign-in uses story/credentials columns (1.35:1); the file vault uses listing/inspector columns (1.8:1), with Streamlit's large gap. Metrics, search, filters and tools precede the file list. Streamlit handles narrow-screen column stacking and the collapsible sidebar.

At the first CSS breakpoint (1000px), horizontal padding decreases and the protocol strip becomes one column. At the narrow breakpoint (760px), padding tightens further, identity/file headings wrap, the footer stacks and inspector/form padding decreases. The banner lock becomes subdued behind text. These CSS thresholds do not define Streamlit's column-stacking threshold.

## Elevation & Depth

Custom styling uses tonal layering, borders and gradients rather than box shadows. The banner and inspector use restrained navy gradients. Rendered depth belongs to the isolated sign-in scene, without prescribing shadows for ordinary controls.

Control transitions use short ease-out timing (180ms). Reduced-motion CSS disables transitions and animations. The scene separately honors reduced motion, offers pause/play, suspends when hidden, resizes and provides a WebGL-unavailable fallback.

## Shapes

Controls use compact rounded corners; file cards, feature surfaces and forms use progressively broader corners as recorded above. Sharing and role badges are small rounded capsules. Decorative lock geometry has its own larger curves. Upload and empty states use dashed outlines; metadata sits in a darker rounded inset.

## Components

### Buttons

Secondary controls use the raised surface, ink text and a border. Hover shifts toward blue with lighter text and border. Primary actions use a cyan-to-pale-cyan-to-violet gradient; primary button/form hover brightens it. Native Streamlit determines geometry not explicitly overridden; the custom minimum height is 2.65rem and the sign-in submit minimum is 3.2rem. Disabled ordinary buttons fade and use the unavailable cursor.

### Inputs / Fields

Fields use the nav surface and border, visible placeholders and a cyan caret. Explicit keyboard focus for buttons, inputs, links, summaries and radios uses a cyan outline (2px) offset from the edge (3px).

### Navigation

The dark sidebar uses native radio navigation. Rows have padded rounded hit areas and a blue hover surface. A checked row is cyan with dark text and a semibold label. The native sidebar supplies its mobile collapse control.

### Chips

Team/role badges use pale violet on deep purple; private badges use pale cyan on dark teal. Visible text supplies meaning alongside color. The banner's outlined capsule is descriptive rather than interactive.

### Cards / Containers

File cards and metrics use the panel layer. Forms add a solid border and broader corners. Protection cards, empty states, expanders and upload regions share the palette with purpose-specific radii and spacing. The inspector uses a navy gradient shell and darker definition-list metadata rows.

### Sign-in vault and assets

The user-supplied Three.js scene runs in an isolated Streamlit component and receives no credentials, session token or vault data. The dependency and scene are bundled locally; there are no runtime CDN requests. `assets/vault-scene.js` adapts the supplied Stitch `ANIMATION_6` export. `assets/three.min.js` is Three.js r125, matching that export, with its MIT license. Fonts originate from Google Fonts (Space Grotesk, Inter, JetBrains Mono), with adjacent licenses. Inline icons are authored geometric SVGs embedded as data images to survive Streamlit HTML sanitization. No external image or avatar is required.

## Do's and Don'ts

### Do:

- **Do** preserve the supplied navy/cyan/violet identity and established font roles.
- **Do** retain native Streamlit actions and escaped file metadata.
- **Do** describe SHA-256 values as upload metadata until live verification succeeds.
- **Do** apply batch verification to all matching filtered files and report individual failures; keep guest controls metadata-only.
- **Do** share these tokens and native widget styling across bootstrap, overview, account, team access, audit and security pages.
- **Do** preserve local asset licenses, animation controls and the WebGL fallback.

### Don't:

- **Don't** restore mockup sample users, a role switcher or artificial integrity badges.
- **Don't** introduce unsupported hardware-enclave, FIPS or zero-knowledge claims; authentication and cryptography remain implemented by `vault.py`.
- **Don't** treat the decorative vault scene as a security boundary or pass credentials or vault data into it.
