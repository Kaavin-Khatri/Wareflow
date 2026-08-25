# WareFlow — Animation & Motion Layer Specification

> Architecture reference defining library boundaries, spring presets, and choreography protocols.

---

## 1. Motion Library Ownership Matrix

WareFlow utilizes a layered motion stack. Every motion job has ONE designated owner library to avoid conflicts, bundle bloat, and frame drops:

| Motion Domain                     | Designated Library       | When to Use                                                                             | Rationale & Presets                                                                                                 |
| :-------------------------------- | :----------------------- | :-------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------ |
| **React UI State Transitions**    | `motion` (Framer Motion) | Page/route enter/exit, modal & drawer entrance, dropdown popovers, list enter/leave     | Seamless declarative lifecycle hooks (`<AnimatePresence>`), layout animations (`layoutId`), shared spring presets.  |
| **Marketing & Complex Timelines** | `gsap` (+ ScrollTrigger) | Landing page hero animations, scroll-linked multi-stage reveal sequences                | Unrivaled timeline control, precision scrubbing, zero React render overhead for complex canvas/SVG choreographies.  |
| **List/Grid Mutations**           | `@formkit/auto-animate`  | Dynamic table row insertion/deletion, cart item lists, inventory filter grid reflows    | Zero-config DOM mutation animations with 1 line of code: `const [parent] = useAutoAnimate()`.                       |
| **Physics Micro-Interactions**    | `@react-spring/web`      | Gesture-driven drag cards, fluid magnetic cursor interactions, springy draggable panels | Direct imperative spring solver without triggering React re-renders during high-frequency pointer movement.         |
| **SVG Morphing & Icon Micro-FX**  | `animejs`                | SVG path morphing/draw-in, checkbox check-draw, snappy icon state morphs, button pulse  | Ultra-lightweight path drawing (`strokeDashoffset`), numeric property interpolation, and non-React SVG micro-loops. |

---

## 2. Standard Spring Physics Presets (`SPRING_PRESETS`)

All React UI motion must import shared physics curves from `@/components/motion/MotionProvider`:

```tsx
import { SPRING_PRESETS } from "@/components/motion/MotionProvider";

// Available Presets:
// 1. SPRING_PRESETS.snappy     — Fast, crisp response for buttons, toggles, icon clicks (stiffness 450, damping 30)
// 2. SPRING_PRESETS.glassMorph — Liquid morphing for modals, panels, cards (stiffness 380, damping 26, mass 0.8)
// 3. SPRING_PRESETS.gentle     — Calm ambient reveal for background elements (stiffness 220, damping 24)
// 4. SPRING_PRESETS.bouncy     — Playful spring for success badges, notifications (stiffness 550, damping 18)
// 5. SPRING_PRESETS.smoothFade — Eased opacity/filter transitions (duration 0.25s, cubic-bezier(0.16, 1, 0.3, 1))
```

---

## 3. Standard UI Motion Patterns

### 3.1 Route & Page Transitions

Wrap top-level page views in `<PageTransition>`:

```tsx
import { PageTransition } from "@/components/motion/GlassMotion";

export default function InventoryPage() {
  return (
    <PageTransition>
      <div className="space-y-6">...</div>
    </PageTransition>
  );
}
```

### 3.2 Staggered List Entrance

```tsx
import { StaggerContainer, StaggerItem } from "@/components/motion/GlassMotion";

<StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-4">
  {products.map((p) => (
    <StaggerItem key={p.id}>
      <ProductCard product={p} />
    </StaggerItem>
  ))}
</StaggerContainer>;
```

### 3.3 Auto-Animated List Reflow

```tsx
import { useAutoAnimate } from "@formkit/auto-animate/react";

export function OrderList({ orders }) {
  const [parentRef] = useAutoAnimate();
  return (
    <ul ref={parentRef}>
      {orders.map((o) => (
        <OrderItem key={o.id} order={o} />
      ))}
    </ul>
  );
}
```

---

## 4. Accessibility & Performance Guardrails

1. **`prefers-reduced-motion`**: All motion components must honor `prefers-reduced-motion: reduce` by replacing spatial translations with instant or subtle opacity fades.
2. **GPU Layering**: Animate `transform` and `opacity` only. Never animate `width`, `height`, `margin`, or `left`/`top` properties directly to avoid CPU reflows.

---

## 5. Element-to-Interaction Pattern Mapping Registry

| Element Category | Component / Target | Interaction Behavior | Motion Preset / Physics | Reduced-Motion Fallback |
| :--- | :--- | :--- | :--- | :--- |
| **Buttons & Action Triggers** | `GlassButton`, icon buttons | Tap scale `0.97`, top specular sheen sweep, active brightness shift | `SPRING_PRESETS.snappy` (450, 30) | Instant opacity shift |
| **Cards & Containers** | `GlassCard(hoverable=true)` | Translate `-translate-y-0.5`, shadow lift, perimeter gradient boost | `SPRING_PRESETS.glassMorph` (380, 26) | Static border highlight |
| **Table Rows** | `DataTable` `<tr>` | Surface highlight `hover:bg-[var(--surface-hover)]`, AutoAnimate reorder | `@formkit/auto-animate` | Instant DOM update |
| **Navigation Gliders** | `Sidebar` & `Topbar` links | Fluid sliding pill background across active tabs | `layoutId="active-nav-pill"` | Immediate active class switch |
| **Desktop Pointer** | `CustomCursor` | Spring-solved trailing ring, `1.6x` scale on interactive targets | Motion springs (350, 28) | Completely disabled (`null`) |
| **Page-Load Content** | KPI grids, catalog cards | Staggered entrance reveal (`staggerDelay: 0.04s`, blur->sharp) | `StaggerContainer` + `StaggerItem` | Instant layout render |
| **Loading Skeletons** | `SkeletonCard`, `SkeletonTable` | Precision shape silhouettes with continuous 1.8s shimmer gradient | CSS keyframe `shimmer` wave | Solid muted placeholder |

