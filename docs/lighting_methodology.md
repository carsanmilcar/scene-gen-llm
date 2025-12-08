# Scene Creation and Selection Methodology (SynkroDMX)

This guide describes how SynkroDMX generates and selects lighting scenes based on musical energy and structure. The goal is to provide a reproducible, extensible process that preserves visual hierarchy, controlled variety, and careful use of aggressive effects. It explains why fixture categories exist, what a "scene" means in semantic terms, and how the engine decides what to activate at any moment.

## 1. Introduction

The methodology is designed for mixed rigs (wash, spots, and effects) and follows common live-show practices: separating device functions, building reusable looks, and triggering effects only at key moments. It prioritizes visual clarity, hierarchy between layers, compatibility with automatic tempo/section detection, and a moderate use of aggressive effects.

## 2. Functional classification of fixtures

Each fixture is assigned to a category that determines its main role in the show:

### 2.1. Primaries (Wash)

Create the base atmosphere: uniform color and steady presence.

- Examples: LED bars, VDPLPS36B2 (#01-#12).
- Functions: background color from `palette`, soft chases or slow fades, minimal lighting always present.

### 2.2. Spots (Accent)

High power or visual presence for highlighted moments.

- Examples: Dallas 180 MK2 (#1-#4), VDPL110CC LED Tri Spot.
- Functions: rhythmic hits, flashes on drops, directed color changes, reinforcement during `energy` rises.

### 2.3. Specials (Effect)

Strongly alter visual perception; used sparingly.

- Example: Cameo Superfly XS.
- Functions: fill the space with dynamic patterns, create "wow" moments, high-`energy` scenes.

## 3. Scene taxonomy ("Scene Model")

A scene is defined by semantic parameters, independent of specific DMX values. This enables smart selection without yet knowing per-fixture output.

### 3.1. Main parameters

- `energy` (1-5): 1 = very soft; 5 = extremely intense.
- `palette`: base sets, e.g., `warm`, `cool`, `neutral`, `mono_blue`, `rainbow`.
- `motion`: `static`, `slow`, `medium`, `fast`; defines chase/transition speed.
- `strobe`: `none`, `soft`, `hard`; controls permission and intensity of strobe.
- `focus`: leading category: `wash`, `puntuales` (spots), `special`, `mixed`.

## 4. Core look design

Limited catalog of canonical scenes that serve as direct looks or bases for variations.

### 4.1. Wash scenes (primaries)

- `wash_warm_soft`: `energy`=1, `palette`=`warm`, `motion`=`static`.
- `wash_cool_soft`: `energy`=1-2, `palette`=`cool`.
- `wash_white_intense`: `energy`=3, `palette`=`neutral`.
- `wash_dual_split`: half `warm` / half `cool`, `motion`=`slow`.

### 4.2. Scenes with spots

- `accent_hit`: spots deliver short hits, primaries soft, `energy`=3-4.
- `puntuales_fade_color`: slow transitions on spots over static wash.
- `puntuales_sync_beats`: turned on for selected beats (e.g., 1 and 3).

### 4.3. Special scenes

- `superfly_auto_slow`: gentle effect, `energy`=3.
- `superfly_auto_fast`: high movement, `energy`=5.
- `superparty_full_rig`: for energy peaks; Superfly + spots + primaries in a fast chase.

## 5. Application rules based on the music

The scene is derived from musical characteristics in real time.

### 5.1. By musical energy level

- `energy` 1-2 (intro, soft verses, outro): scenes with `focus`=`wash`; no `strobe`; spots off or subtle; specials forbidden.
- `energy` 3 (strong verse, gentle buildup): wash + light spots; some slow `motion`; `strobe` only if `soft`.
- `energy` 4-5 (chorus, drop, peaks): activate spots as accent; allow Superfly; fast chases; moderate `strobe` (`soft`) or `hard` only at key moments.

## 6. Additional variety and control rules

Avoid saturation and preserve coherence.

- `palette`: do not repeat the same one more than two scenes in a row.
- `strobe`: do not chain scenes with `strobe`=`hard`; do not keep strobe active for more than X seconds (configurable).
- Specials: Superfly only if `energy` >= 4 and turned off after Y seconds unless exceptional.
- Spots: should not remain on continuously; only rhythmic hits or short effects.

## 7. Scene selection algorithm

The engine evaluates musical `energy`, `tempo`, detected section (intro/verse/pre/chorus/drop), and history to avoid unwanted repetition.

```pseudo
function select_scene(context):
    energy = context.energy
    current_palette = context.last_palette
    last = context.last_scene

    candidates = scenes
        .filter(e.energy in [energy-1, energy+1])
        .filter(e.palette != current_palette)
        .filter(e != last)

    if energy < 3:
        candidates = candidates.filter(e.focus == "wash")

    if context.is_drop:
        candidates = candidates.filter(e.focus in ["puntuales", "special"])

    if context.strobe_allowed == false:
        candidates = candidates.filter(e.strobe == "none")

    return choose_probabilistically(candidates)
```

## 8. Scene translation to DMX values

Once the semantic scene is selected:

- Load base definition for primaries, spots, and specials.
- Apply `palette` and `motion`.
- Adjust effects (`strobe`, Superfly) according to `strobe`, `motion`, and `energy`.
- Send DMX values per fixture according to its channel dictionary.

## 9. Benefits of this methodology

- Scales to new fixtures.
- Easy to debug.
- Separates musical logic from good lighting programming.
- Produces coherent and varied shows without manual intervention.
- Compatible with small/medium live rigs.
