# Design System — Workout Agent

## Direction

Technical / instrument — monospace-forward, asymmetric layouts, exposed metadata, single saturated accent on near-monochrome base.

## Typography

| Role | Face | Weight | Reasoning |
|------|------|--------|-----------|
| UI / body | IBM Plex Sans | 400, 500 | Neutral technical sans. Not Inter, not trendy. Designed for data-dense interfaces. |
| Data / metadata / labels | JetBrains Mono | 400, 500 | Already in use. Monospace for numbers, timestamps, versions, tool calls. |
| Display / headings | IBM Plex Sans | 500 | Same family, medium weight only. No 600/700 body text. |

Google Fonts load: `IBM+Plex+Sans:wght@400;500&family=JetBrains+Mono:wght@400;500`

## Color tokens

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#0A0A0A` | Page background |
| `--surface` | `#141414` | Elevated surfaces (chat bubbles, inputs) |
| `--surface-2` | `#1E1E1E` | Secondary surfaces |
| `--border` | `#282828` | Borders, rules |
| `--border-hover` | `#3A3A3A` | Hover borders |
| `--text` | `#E8E8E8` | Primary text |
| `--text-2` | `#CCCCCC` | Secondary text (min #C8C8C8 on #0A0A0A) |
| `--text-3` | `#888888` | Tertiary / metadata |
| `--text-muted` | `#555555` | Disabled, faintest labels |
| `--accent` | `#E8590C` | Single accent — used max 3 places per page |
| `--accent-text` | `#F07020` | Accent for text (higher contrast than bg accent) |
| `--danger` | `#DC2626` | Destructive actions |
| `--success` | `#16A34A` | Positive states |

No purple, indigo, or violet anywhere. No gradients, glows, or blur orbs.

## Layout primitives

- **Sections**: separated by hairline `1px solid var(--border)` rules or whitespace. No card wrappers.
- **Corners**: `0px` on surfaces and containers. `2px` on inline code. `999px` (pill) on primary action buttons only.
- **Asymmetric grids**: 7fr/5fr or 2fr/1fr, never uniform 3-column.
- **Alignment**: left-aligned by default. No centered heroes.

## Specificity markers (real or plausibly real)

Include at least three of: version number, build ID, commit hash, timestamp with seconds, environment label.

## Interactive elements (required, non-decorative)

- Click-to-expand tool call detail rows
- Hover-reveal metadata on data items (timestamps, percentages)
- Keyboard-accessible Cmd+K command palette (if scope permits) or inline calculation

## Forbidden patterns

- Glassmorphism, frosted-glass, backdrop-blur on translucent surfaces
- Gradient text on headlines
- Animated gradient backgrounds
- Floating 3D shapes, particle backgrounds
- "Trusted by" logo strips
- Testimonial cards with circular avatars
- Bento grids
- Lucide icons as decoration next to every heading
- Emoji as icons
- The phrase "Build the future" or variations
- Indigo / violet / purple accent
- Purple-to-pink or purple-to-blue gradients
- Uniform 8-12px border-radius on every container
- All-caps letter-spaced section labels (use sentence case or monospace metadata instead)
- Numbered step sequences (01, 02, 03) as a section pattern
- Background glow orbs or blur decorations
