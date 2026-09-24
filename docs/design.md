# ReLoop AI — Design System

## 1. Design Direction
Use a restrained interface inspired by the **Apple Store India** web experience: product-first layouts, generous whitespace, strong typography, light neutral backgrounds, restrained color, rounded cards, simple navigation, and clear hierarchy.

Reference: https://www.apple.com/in/store

Take inspiration from the interface language, not Apple's logos, product imagery, or proprietary assets. ReLoop should remain its own brand.

## 2. Fixed Color Palette
```css
:root {
  --background: #F5F5F7;
  --surface: #FFFFFF;
  --surface-secondary: #FBFBFD;

  --text-primary: #1D1D1F;
  --text-secondary: #6E6E73;
  --text-tertiary: #86868B;

  --border: #D2D2D7;
  --border-light: #E5E5E7;

  --accent-blue: #0071E3;
  --accent-blue-hover: #0077ED;

  --success: #34C759;
  --warning: #FF9F0A;
  --danger: #FF3B30;

  --overlay: rgba(0, 0, 0, 0.04);
}
```

### Palette rules
- `#F5F5F7`: primary page background
- `#FFFFFF`: cards/content surfaces
- `#1D1D1F`: primary text
- `#6E6E73`: secondary text
- `#0071E3`: primary action/link
- `#D2D2D7`: borders
- Green/orange/red only for semantic states
- Do not introduce arbitrary accent colors

These are the fixed ReLoop implementation colors chosen to closely match the neutral/blue Apple Store interface language; they are not claimed to be Apple's official published brand-color specification.

## 3. Typography
Preferred:
- SF Pro Display / SF Pro Text where appropriately available
- Otherwise Inter/system UI

Fallback:
```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "SF Pro Display",
  "SF Pro Text",
  "Inter",
  "Segoe UI",
  sans-serif;
```

Hierarchy:
- Hero: 48–64px, 600–700
- Page heading: 32–40px, 600
- Section: 22–28px, 600
- Body: 16–18px, 400, 1.45–1.6 line-height
- Secondary: 13–15px, #6E6E73

Avoid excessive bold.

## 4. Layout
- Max content width: 1200–1280px
- Center content
- Large whitespace
- 24–32px standard spacing
- 48–96px section spacing
- Cards: white, 1px border, 18–24px radius, minimal/no shadow, 24–32px padding

## 5. Buttons
Primary: Apple-like blue, white text, 12–14px radius, medium/semibold.
Secondary: white/light surface, dark text, border.
No gradients or oversized buttons.

## 6. Product Scan
```text
ReLoop AI
────────────────────────
Assess your product

Upload 2–3 photos
[ Upload Photos ]

or

[ Enter Model ]

Your device
[ Product preview ]

[ Continue ]
```

## 7. Condition Dashboard
```text
Product
Dell Latitude 5420
4–5 years old

Condition overview

Battery       73%*
SSD           91%
RAM           PASS
Thermals      Service
Display       Good
Keyboard      Damage
```

Every measurement must show its source, e.g. `73% — Diagnostic data`.

## 8. Evidence Labels
Use neutral pills:
- VISUAL
- DIAGNOSTIC
- USER REPORTED
- DATABASE
- ESTIMATE

## 9. Recommendation Screen
```text
Recommended pathway

REPAIR + UPGRADE

Why?
✓ Battery capacity reduced
✓ SSD remains healthy
✓ RAM diagnostic passed
✓ Thermal service required

Estimated result
+2–3 years useful life*

[ View alternatives ]
[ View assumptions ]
```

Do not hide evidence behind a chatbot.

## 10. Circular Pathway UI
Simple cards:
- Repair — Fix failed component
- Upgrade — Improve performance
- Refurbish — Service and restore
- Reuse — Keep product in use
- Component Recovery — Salvage usable parts
- Recycle — Last option

Use simple line icons.

## 11. Animation
Allowed:
- Subtle hover
- Button transitions
- Progress indicators
- Small card reveals

Avoid:
- Parallax
- Glowing effects
- Animated gradients
- Particles
- Excessive motion

## 12. Responsive
Support desktop, tablet and mobile. Primary demo target is desktop browser.

## 13. Brand Personality
ReLoop should feel:
- Calm
- Precise
- Trustworthy
- Practical
- Product-focused
- Technical without being intimidating

It should not feel futuristic, cyberpunk, overly “AI”, corporate-heavy, or sustainability-cliché.
