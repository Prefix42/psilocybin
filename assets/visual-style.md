# Visual style — psilocybin

Guidance for any agent producing visual or branded material (docs, diagrams, social images, UI) for this project.

## Logo
- Mark: **"Warped orbit"** — three concentric ellipses drifting off-axis around an offset pupil. It reads as a hypnotic eye slipping out of true: the TripSitter watching, reality wobbling.
- Canonical files: `psilocybin-icon.svg` (full 3-ring mark), `favicon.svg` (simplified 1-ring + pupil, for ≤32px).
- Wordmark: lowercase `psilocybin`, Space Grotesk SemiBold (600), letter-spacing -0.01em. In lockups the mark **replaces the "o"** (psil◎cybin), sized ~1.05× the lowercase x-height cap.
- Never redraw the mark; scale the SVGs. At small sizes use the simplified favicon variant, not the 3-ring mark.

## Color
- Signature gradient (135°): `#7C3AED` → `#E04FB0` (55%) → `#F5A524`. Use it for the mark, and sparingly as an accent (one gradient element per composition).
- Dark surface: `#16121E`. Light surface: `#F7F5FB` (borders `#E4E0EC`), card white `#FFFFFF`.
- Ink: `#1A1523`; muted text: `#6B6478` / `#8B8496`. Glitch accent (rare): teal `#2DD4BF`.
- Everything must work on both dark and light; prefer dark for hero/social imagery.

## Type
- Display/UI: **Space Grotesk** (400–700).
- Code/labels: **JetBrains Mono**.
- No other typefaces.

## Voice of imagery
- Psychedelic via geometry and the gradient — rings, orbits, offsets — never literal drug imagery, no emoji, no rainbow-everything.
- Flat vector, generous whitespace, minimal ornament; distortion/drift is the motif (things slightly off-true, echoing hallucinated return values).
- Tagline when needed: "The psychedelic way to test."

## README & GitHub usage
- README header: use the lockup with automatic theme switching:
  ```html
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/psilocybin-lockup-dark.png">
    <img src="assets/psilocybin-lockup-light.png" alt="psilocybin" width="320">
  </picture>
  ```
- Social preview (repo settings): `psilocybin-og.png`.
- Badges (shields.io): keep the existing set; for new badges use color `8A2BE2` (matches the Top Agent badge) or `7C3AED`, `logoColor=white`. No rainbow badge rows.

## Diagrams & docs illustrations
- Flat vector on `#16121E` or white; boxes with 8–12px radius, 1.5–2px strokes in ink/muted, **no drop shadows**.
- The gradient appears once per diagram at most — reserve it for the "hallucinating" element (the mutated return, the injected exception). Sober components stay monochrome; that contrast IS the story.
- Trip states: sober = ink/muted, hallucinating = gradient, bad trip = `#E04FB0` alone, restored/safe = `#2DD4BF`.

## Don't
- Recolor or re-proportion the mark; add glows, shadows, or 3D.
- Set the wordmark in caps or another font.
- Use the full gradient as a text color for body copy or large surfaces.
- Literal mushroom/pill/drug imagery, emoji, or trippy stock textures.

## Existing assets (repo `assets/`)
- `psilocybin-icon.svg`, `favicon.svg`
- `psilocybin-icon-mono-black.svg`, `psilocybin-icon-mono-white.svg` — single-color contexts only (terminals, stickers, print); never recolored beyond ink/white
- `favicon-16.png`, `favicon-32.png`, `favicon-180.png` (apple-touch)
- `psilocybin-lockup-dark.png`, `psilocybin-lockup-light.png`
- `psilocybin-icon-dark.png`, `psilocybin-og.png` (2400×1260, GitHub social preview)

## Gotcha for asset regeneration
When rasterizing the mark from HTML/SVG, the `<linearGradient>` def MUST live inside the same `<svg>` being captured — a gradient referenced across elements renders the rings black in exported crops.
