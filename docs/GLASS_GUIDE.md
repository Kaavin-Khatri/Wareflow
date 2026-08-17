# WareFlow — Liquid Glass Architecture & Specular Refraction Guide

> Standard specification for all UI surfaces across WareFlow.
> **Rule:** Never create flat, non-refractive "blurred" rectangles. All glass surfaces must use the established specular refraction primitives.

---

## 1. The Physics of Liquid Glass

Ordinary web "glassmorphism" is typically just `backdrop-filter: blur(10px)` with a flat translucent white or gray background. Real optical glass behaves fundamentally differently:

1. **Perimeter Lensing & Refraction**: Light bends sharply at curved boundaries and bevels, visibly refracting whatever content is directly behind the edge.
2. **Specular Top Highlight**: Physical glass catches ambient top-down lighting, producing a micro-thin (1px–1.5px) luminous highlight along its upper perimeter edge.
3. **Tactile Spring Compression**: When pressed, a physical control compresses slightly, narrowing the refraction angle and heightening specular luminance.

---

## 2. Refraction Strength Hierarchy & Performance Budget

To guarantee a locked 60 FPS on mobile and low-power hardware, refraction strength scales inversely with element surface area and frequency:

| Primitive                       | Refraction Tier              | Specular Sheen                                     | Backdrop Blur                | Target Scale & Frequency                                                       |
| :------------------------------ | :--------------------------- | :------------------------------------------------- | :--------------------------- | :----------------------------------------------------------------------------- |
| **`GlassButton`**               | **Full-Strength Refraction** | 1.5px shifting gradient + active scale compression | 16px (`--glass-bg`)          | Small surface area (~100x40px). Safe for 30+ buttons per dense table row.      |
| **`GlassModal` / `GlassSheet`** | **Full-Strength Border**     | 1.5px top highlight + deep drop diffusion          | 24px (`--glass-bg-elevated`) | Elevated modal dialog. Only 1 active instance on screen at a time.             |
| **`GlassDropdown`**             | **Full-Strength Border**     | 1px top highlight + subtle scale pop               | 24px (`--glass-bg-elevated`) | Popover/menu. Short-lived overlay.                                             |
| **`GlassInput`**                | **Full-Strength Refraction** | 1px border + Electric Violet focus glow ring       | 12px (`--glass-bg`)          | Small form controls. Refraction shifts to violet glow on focus.                |
| **`GlassPanel` / `GlassCard`**  | **Light-Edge Refraction**    | 1px perimeter highlight sheen                      | 16px (`--glass-bg`)          | Large surface areas. Thinner perimeter displacement to preserve GPU fill rate. |
| **`GlassNav` (Sidebar/Topbar)** | **Light-Edge Refraction**    | 1px perimeter highlight sheen                      | 16px (`--glass-bg`)          | Fixed layout boundaries.                                                       |

---

## 3. Component Reference & Usage

### 3.1 `GlassButton` (Flagship Interactive Primitive)

```tsx
import { GlassButton } from "@/components/glass";

// Primary CTA (Electric Violet Gradient + Glow)
<GlassButton variant="primary" size="md">
  Create Purchase Order
</GlassButton>

// Secondary Translucent Frosted Glass
<GlassButton variant="secondary" size="md">
  Export CSV
</GlassButton>

// Destructive Frosted Glass
<GlassButton variant="destructive" size="sm">
  Delete Item
</GlassButton>
```

### 3.2 `GlassCard` (Structured Content Container)

```tsx
import {
  GlassCard,
  GlassCardHeader,
  GlassCardTitle,
  GlassCardDescription,
  GlassCardContent,
  GlassCardFooter,
} from "@/components/glass";

<GlassCard hoverable glow>
  <GlassCardHeader>
    <GlassCardTitle>Batch FIFO Tracker</GlassCardTitle>
    <GlassCardDescription>Automated expiry date routing</GlassCardDescription>
  </GlassCardHeader>
  <GlassCardContent>
    <p>Warehouse batch details...</p>
  </GlassCardContent>
  <GlassCardFooter>
    <GlassButton variant="primary" size="sm">
      Inspect Batch
    </GlassButton>
  </GlassCardFooter>
</GlassCard>;
```

### 3.3 `GlassModal` (Elevated Dialog Overlay)

```tsx
import { GlassModal } from "@/components/glass";

<GlassModal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Adjust Credit Limit"
  description="Modify authorized wholesale credit terms for Retailer."
>
  <div className="space-y-4">{/* Form contents */}</div>
</GlassModal>;
```

---

## 4. Theme Token Alignment

All glass components automatically consume CSS variables from `globals.css`:

- Light Theme: `--glass-bg: rgba(255, 255, 255, 0.72)`, `--glass-border: rgba(0, 0, 0, 0.08)`, `--accent: #7c3aed`
- Dark Theme: `--glass-bg: rgba(18, 18, 24, 0.65)`, `--glass-border: rgba(255, 255, 255, 0.12)`, `--accent: #8b5cf6`

Never hardcode `bg-black/50` or `bg-white/20` inline. Always use token classes or the established glass primitives.
