---
name: CipherVault
description: CodeInspectorAi reference adaptation for the React website; separate legacy Streamlit surface.
colors:
  canvas: "#07090d"
  nav: "#090c11"
  panel: "#0f131a"
  raised: "#141924"
  ink: "#e8edf4"
  muted: "#a1aaba"
  soft: "#b4bcc8"
  mint: "#3df5a7"
  violet: "#8b7bff"
  border: "#2b323e"
  action-ink: "#04140d"
  danger: "#ffb4ab"
typography:
  display:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "clamp(3.4rem, 5.2vw, 4.5rem)"
    fontWeight: 800
    lineHeight: 1.06
    letterSpacing: "-.04em"
  headline:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "clamp(1.9rem, 3vw, 2.55rem)"
    fontWeight: 750
    lineHeight: 1.18
  title:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "1.05rem"
    letterSpacing: "-.035em"
  body:
    fontFamily: "Inter, Arial, sans-serif"
    lineHeight: 1.55
  mono:
    fontFamily: "JetBrains Mono, monospace"
rounded:
  control: "9px"
  card: "14px"
  navigation: "8px"
  tag: "5px"
spacing:
  card: "20px"
  compact-card: "16px"
  button: "10px 15px"
components:
  button-primary:
    backgroundColor: "{colors.mint}"
    textColor: "{colors.action-ink}"
    rounded: "{rounded.control}"
    padding: "{spacing.button}"
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "{spacing.button}"
  input:
    backgroundColor: "#0b0e14"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 12px"
  card:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.card}"
    padding: "{spacing.card}"
---

# Design System: CipherVault

## Overview

The React website follows the user-approved CodeInspectorAi reference: near-black surfaces, mint actions, violet accents, Inter headings and JetBrains Mono technical labels. This is an explicitly pinned reference adaptation, with no additional creative concept. Its grid atmosphere, restrained borders and terminal presentation connect the landing page, authentication and signed-in workspace.

The current website sources of truth are `web/src/styles.css`, `web/src/App.jsx` and `web/src/VaultTerminal.jsx`. Frontmatter and the sidecar describe that React surface. Streamlit remains a separate supported legacy interface with its existing Stitch identity; its distinct system is recorded below. Product behavior and security claims remain governed by `PRODUCT.md`, `README.md`, `web_api.py` and `vault.py`.

**Key Characteristics:**

- Near-black tonal layers, mint interaction emphasis and restrained violet accents.
- Compact bordered controls, rounded panels and readable technical metadata.
- Locally bundled fonts and clearly illustrative terminal motion.
- Role-aware actions and truthful verification states across supported interfaces.

## Colors

### Primary

- **Mint:** primary actions, focus rings, active navigation, successful walkthrough steps and upload emphasis. The existing CSS custom property `--cyan` now contains this mint value; its historical name does not indicate the visible hue.

### Secondary

- **Violet:** secondary illustration accents, technical highlights and sharing/role badges. The hero heading blends mint through pale blue into violet.

### Neutral

- **Canvas / Nav:** page backdrop and darker sidebar or authentication fields.
- **Panel / Raised:** bordered containers, metric gradients and secondary controls.
- **Ink / Muted / Soft:** primary content, supporting text and quieter control labels.
- **Border:** structural separation in forms, tables and panels.
- **Action Ink / Danger:** dark text on mint actions; readable destructive and failure states paired with visible labels.

**The Truthful State Rule.** Decorative sample states never substitute for a real verification result or operational metric.

## Typography

Inter supplies the wordmark, headings, controls, prose and metric values. JetBrains Mono supplies terminal text, protocol names, hashes and other technical metadata. Both font families are bundled locally with their licenses. There is no Space Grotesk heading role in the current React surface.

Hero display type is bold and closely spaced; section headings are smaller and lighter. Workspace page headings use a compact responsive range (1.7rem to 2.2rem), with narrow-screen overrides. Body prose has generous line height, while terminal labels and table metadata are compact. Metric values and technical table cells use tabular numerals. Long filenames and hashes wrap in dedicated content areas; user identity text in the topbar truncates to protect controls.

## Layout

The public page uses a centered content wrapper (1244px maximum, including padding), sticky navigation (70px desktop height), and generous section spacing (88px vertically). Its first viewport pairs the headline and actions with a terminal walkthrough in two columns. A subtle grid (56px cells) and localized mint/violet illumination sit behind landing and authentication content. Authentication pairs an identity story and compact terminal with the existing setup/login form. The form heading stands on its own without an eyebrow. Story heading line breaks remain on phones, and its small protection labels wrap horizontally.

The workspace uses a sidebar (260px) and flexible main column, a quiet topbar (69px), metrics, filters, scrollable tables and a file inspector. The desktop listing/inspector grid uses a 1.9fr / .9fr balance with a minimum inspector width (270px); medium widths stack it. Tables retain their own horizontal scrolling rather than widening the page.

At 1000px the landing hero stacks and loses its perspective tilt. At 800px authentication stacks, its compact terminal is hidden, and the sidebar becomes an off-canvas menu with a backdrop and close control. At 550px hero actions and feature cards stack; terminal protocol labels move below step descriptions, and workspace metrics retain two compact columns. Other rules at 1150px and 801–1250px adapt metrics, filters and inspector layout. Match the CSS cascade rather than treating one threshold as universal.

## Elevation & Depth

Depth comes mainly from tonal layering, fine borders and restrained gradients. The terminal uses a soft black shadow with a faint violet glow; authentication uses a quiet black shadow. Mint actions have a small accent shadow. The hero terminal has a desktop perspective tilt that settles on hover; it is removed on stacked layouts and for reduced motion. Ordinary workspace panels remain comparatively flat.

Short control transitions use roughly 200–300ms; the shared easing curve is `cubic-bezier(.16,1,.3,1)`. Reveal elements remain fully opaque at all times, with a one-time translation animation when observation is available. Reduced-motion styling suppresses animation, transition movement, smooth scrolling and hero tilt.

## Shapes

Panels use softly rounded corners (14px), controls use tighter corners (9px), selected navigation uses 8px, and tags use 5px. Terminal status icons are circular. The logo combines a mint/violet tile with a small geometric mark. Upload regions use dashed outlines; technical values use darker inset surfaces. These shapes distinguish function without relying on ornamental imagery.

## Components

### Buttons and fields

Primary buttons use mint with dark text; secondary buttons use the raised surface; ghost buttons keep transparent backgrounds and visible borders. Common buttons have a minimum height (43px), with larger mobile hero actions. Hover lifts by a small amount and changes surface/border color. Keyboard focus uses an explicit mint outline (2px, offset 3px for buttons and links). Fields have a minimum height (42px), dark backgrounds, visible placeholders, a mint caret and a mint focus outline. Disabled buttons fade and retain an unavailable cursor.

### Navigation, tags and cards

Workspace navigation uses compact icon/label rows; the selected item has a translucent mint fill, mint text and a quiet mint border. Mobile navigation exposes its expanded state and closes through its own button or backdrop. Tags use text with semantic color, including violet sharing/role accents, mint success and red failures. Cards share the panel/border system; metrics use a raised-to-panel gradient. The inspector adds a subtle green-black gradient and wrapped digest blocks.

### Illustrative terminal

The landing terminal shows a sample document and four stages: validate access, encrypt the file, wrap the key and verify on retrieval. Every stage is present in the markup; the finite sequence advances every 900ms, then stops. Pause/resume is available during playback and replay after completion. Reduced motion presents all stages complete without playback controls. SAMPLE and “Illustrative walkthrough · no file is processed” make the illustration explicit. Authentication reuses a compact version on wider screens. No real credentials, secrets or files enter this illustration.

The React landing page and sign-in no longer render a Three.js hero. The unused React scene file may remain in the repository; its presence does not make it part of the current composition.

### Separate legacy Streamlit surface

Streamlit retains its supplied Stitch File Vault and Sign In / Unlock design; this React redesign did not restyle it. Its sources remain `ui.css`, `ui.py`, `.streamlit/config.toml` and `app.py`. Its palette uses navy canvas (#0e1321), darker navigation (#090e1c), panels (#1a1f2e), raised surfaces (#252a39), pale ink (#dee2f6), muted text (#a6b4ca), cyan (#22d3ee), pale violet (#d0bcff), borders (#30394e), success (#62e0ba) and danger (#ffb4ab). Space Grotesk carries its headings, wordmark and metrics; Inter carries UI/prose; JetBrains Mono carries technical metadata.

Legacy controls are native Streamlit widgets, with cyan-to-violet primary gradients, cyan checked radio navigation and focus outlines, 8px controls, 9px fields, 12px insets, 16px file cards, 18px feature surfaces and 20px forms. Its content container caps at 1520px. Story/form columns use a 1.35:1 ratio; file listing/inspector uses 1.8:1. Streamlit supplies column stacking and the sidebar collapse behavior; custom CSS thresholds at 1000px and 760px tighten padding, wrap headings and adjust supporting layouts. Legacy surfaces use tonal layering rather than custom box shadows; control transitions use 180ms ease-out.

Streamlit still uses the isolated animated sign-in vault in `assets/vault-scene.js`, adapted from the supplied Stitch `ANIMATION_6` export. Its local `assets/three.min.js` is Three.js r125 with the MIT license. It receives no credentials, session token or vault data, honors reduced motion, offers pause/play, suspends when hidden and includes a WebGL fallback. Legacy Space Grotesk, Inter and JetBrains Mono fonts retain their SIL Open Font Licenses. Authored geometric SVG icons survive Streamlit sanitization as data images. Preserve these assets and licenses independently of the React terminal.

## Do's and Don'ts

### Do:

- **Do** carry the approved reference palette, type roles and compact geometry across the React landing, authentication and workspace.
- **Do** keep all sample terminal activity visibly illustrative and honor reduced motion.
- **Do** preserve visible focus, mobile navigation controls, scrollable tables and readable identifiers.
- **Do** preserve each surface's local asset licenses and Streamlit's existing animation controls/fallback.
- **Do** describe SHA-256 values as upload metadata until live verification succeeds; keep guest controls metadata-only and report individual verification failures.

### Don't:

- **Don't** apply the React mint system to Streamlit without a separate redesign request.
- **Don't** restore mockup sample users, role switchers, artificial integrity badges or invented live metrics.
- **Don't** introduce unsupported hardware-enclave, FIPS, compliance or zero-knowledge claims; security remains implemented by `vault.py`.
- **Don't** treat the illustrative terminal or legacy 3D vault as a security boundary.
