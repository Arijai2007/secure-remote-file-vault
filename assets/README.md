# Bundled asset provenance

Assets are loaded from the application package; browsers make no runtime CDN/font requests for them.

| Asset | Upstream source | License |
|---|---|---|
| `three.min.js` | https://ajax.googleapis.com/ajax/libs/threejs/r125/three.min.js | MIT; `three-LICENSE.txt` from the matching Three.js r125 tag |
| `space-grotesk.woff2` | Google Fonts CSS API, `Space Grotesk:wght@400..700`, Latin subset | SIL OFL; `space-grotesk-OFL.txt` |
| `inter.woff2` | Google Fonts CSS API, `Inter:wght@400..700`, Latin subset | SIL OFL; `inter-OFL.txt` |
| `jetbrains-mono.woff2` | Google Fonts CSS API, `JetBrains Mono:wght@400..500`, Latin subset | SIL OFL; `jetbrains-mono-OFL.txt` |
| `vault-scene.js` | User-supplied `stitch_ciphervault_ui_design_system.zip`, `three.js/code.html`, `ANIMATION_6` | Supplied project artwork/code; adapted for sizing, pause, reduced motion, visibility and WebGL fallback |

Fonts were retrieved through `https://fonts.googleapis.com/css2?family=<family>&display=swap`; the final Latin `fonts.gstatic.com` resource was bundled. Font licenses originate from the corresponding `ofl/spacegrotesk`, `ofl/inter`, and `ofl/jetbrainsmono` directories in `google/fonts`.

SHA-256 of unmodified vendor binaries:

```text
e9c638dc91bfdea9ad5cdc231a489af25e4977d7b56f9b6213af5225f8626213  three.min.js
0640890476fc1198ab4de571fb658de443c4d85b66466ec09534a8737ab1ce9d  space-grotesk.woff2
3100e775e8616cd2611beecfa23a4263d7037586789b43f035236a2e6fbd4c62  inter.woff2
83c005d49d8a6a50474c73a5a36ac0468076e9c4a29da7bdb14995d80560a5be  jetbrains-mono.woff2
```
