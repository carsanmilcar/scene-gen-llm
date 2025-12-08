# Scene Creation and Selection Methodology (SynkroDMX)

This guide explains how SynkroDMX builds and selects lighting scenes from musical energy and structure. The goal is a repeatable, extensible process that keeps visual hierarchy, controlled variety, and prudent use of aggressive effects. It describes fixture categories, what a *semantic scene* means, and how the engine decides what to activate at each moment.

## 1. Introduction

The methodology is designed for mixed rigs (wash, spots, and effects) and borrows common live-show practices: separate device roles, build reusable looks, and trigger effects only at key moments. It prioritizes visual clarity, hierarchy between layers, compatibility with automatic tempo/section detection, and moderate use of harsh effects.

## 2. Functional fixture classification

Each fixture is assigned a category that defines its main role in the show:

### 2.1. Primaries (Wash)

Provide the base atmosphere: uniform color and steady presence.

- Examples: LED bars, VDPLPS36B2 (#01-#12).
- Functions: background color per `palette`, soft chases or slow fades, minimum light always present.

### 2.2. Accents (Spots)

High punch or visual presence for featured moments.

- Examples: Dallas 180 MK2 (#1-#4), VDPL110CC LED Tri Spot.
- Functions: rhythmic hits, flashes on drops, targeted color changes, reinforcement when `energy` rises.

### 2.3. Specials (Effects)

Strongly alter the visual perception; used sparingly.

- Example: Cameo Superfly XS.
- Functions: fill space with dynamic patterns, create “wow” moments, high-`energy` looks.

## 3. Scene taxonomy (Semantic Scene Model)

A scene is defined by semantic parameters, independent of specific DMX values. This allows intelligent selection without knowing fixture outputs beforehand.

### 3.1. Core parameters

- `energy` (1-5): 1 = very soft; 5 = extremely intense.
- `palette`: base sets, e.g., `warm`, `cool`, `neutral`, `mono_blue`, `rainbow`.
- `motion`: `static`, `slow`, `medium`, `fast`; defines chase/transition speed.
- `strobe`: `none`, `soft`, `hard`; controls permission and intensity of strobe.
- `focus`: leading category: `wash`, `accents`, `special`, `mixed`.

## 4. Canonical base scenes (Core Looks)

A limited catalog of canonical scenes that act as direct looks or bases for variations.

### 4.1. Wash scenes (primaries)

- `wash_warm_soft`: `energy`=1, `palette`=`warm`, `motion`=`static`.
- `wash_cool_soft`: `energy`=1-2, `palette`=`cool`.
- `wash_white_intense`: `energy`=3, `palette`=`neutral`.
- `wash_dual_split`: half `warm` / half `cool`, `motion`=`slow`.

### 4.2. Scenes with accents

- `accent_hit`: accents deliver brief hits, primaries stay soft, `energy`=3-4.
- `accent_fade_color`: slow transitions on accents over static wash.
- `accent_sync_beats`: on selected beats (e.g., 1 and 3).

### 4.3. Specials

- `superfly_auto_slow`: gentle effect, `energy`=3.
- `superfly_auto_fast`: high movement, `energy`=5.
- `superparty_full_rig`: for energy peaks; Superfly + accents + primaries in fast chase.

## 5. Rules by musical context

The scene derives from musical characteristics in real time.

### 5.1. By energy level

- `energy` 1-2 (intro, soft verses, outro): scenes with `focus`=`wash`; no `strobe`; accents off or minimal; specials forbidden.
- `energy` 3 (strong verse, mild buildup): wash + light accents; some slow `motion`; `strobe` only if `soft`.
- `energy` 4-5 (chorus, drop, peaks): enable accents as hits; allow Superfly; fast chases; `strobe` moderate (`soft`) or `hard` only for key moments.

## 6. Variety and control rules

These keep saturation in check and preserve coherence.

- `palette`: do not repeat the same palette for more than two scenes in a row.
- `strobe`: avoid chaining `strobe`=`hard`; do not keep strobe active beyond X seconds (configurable).
- Specials: Superfly only if `energy` >= 4 and turned off after Y seconds unless exceptional.
- Accents: avoid staying on continuously; only rhythmic hits or short effects.

## 7. Scene selection algorithm

The engine evaluates musical `energy`, `tempo`, detected section (intro/verse/pre/chorus/drop), and history to avoid unwanted repetition.

```text
function select_scene(context):
    energy = context.energy
    last_palette = context.last_palette
    last_scene = context.last_scene

    candidates = scenes
        .filter(e.energy in [energy-1, energy+1])
        .filter(e.palette != last_palette)
        .filter(e != last_scene)

    if energy < 3:
        candidates = candidates.filter(e.focus == "wash")

    if context.is_drop:
        candidates = candidates.filter(e.focus in ["accents", "special"])

    if context.strobe_allowed == false:
        candidates = candidates.filter(e.strobe == "none")

    return choose_weighted_by_energy(candidates)
```

## 8. Mapping semantic scene to DMX

Once the semantic scene is selected:

- Load base definitions for primaries, accents, and specials.
- Apply `palette` and `motion`.
- Adjust effects (`strobe`, Superfly) according to `strobe`, `motion`, and `energy`.
- Send DMX values per fixture based on its channel map.

## 9. Benefits

- Scales to new fixtures.
- Easy to debug.
- Separates musical logic from good lighting programming.
- Produces coherent, varied shows without manual intervention.
- Works well on small/medium live rigs.
