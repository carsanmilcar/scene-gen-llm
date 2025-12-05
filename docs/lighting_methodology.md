# Metodología de Creación y Selección de Escenas (SynkroDMX)

Esta guía describe cómo SynkroDMX genera y selecciona escenas lumínicas a partir de la energía y estructura musical. El objetivo es ofrecer un proceso reproducible y extensible que mantenga jerarquía visual, variedad controlada y uso prudente de efectos agresivos. Aquí se explica por qué existen las categorías de fixtures, qué significa una “escena” en términos semánticos y cómo decide el motor qué activar en cada momento.

## 1. Introducción

La metodología está diseñada para rigs mixtos (wash, puntuales y efectos) y se basa en prácticas habituales de directo: separar funciones de los dispositivos, construir “looks” reutilizables y activar efectos solo en momentos clave. Se prioriza claridad visual, jerarquía entre capas, compatibilidad con detección automática de tempo/secciones y un uso moderado de efectos agresivos.

## 2. Clasificación funcional de los dispositivos

Cada fixture se asigna a una categoría que determina su rol principal dentro del show:

### 2.1. Principales (Wash)

Generan la atmósfera base: color uniforme y estabilidad constante.

- Ejemplos: Barras LED, VDPLPS36B2 (#01–#12).
- Funciones: fondo de color según `palette`, chases suaves o transiciones lentas, nivel mínimo de iluminación siempre presente.

### 2.2. Puntuales (Acento)

Alta potencia o presencia visual para momentos destacados.

- Ejemplos: Dallas 180 MK2 (#1–#4), VDPL110CC LED Tri Spot.
- Funciones: golpes rítmicos (hits), flashes en drops, cambios de color dirigidos, refuerzo en subidas de `energy`.

### 2.3. Especiales (Efecto)

Alteran fuertemente la percepción visual; se usan con moderación.

- Ejemplo: Cameo Superfly XS.
- Funciones: rellenar el espacio con patrones dinámicos, crear momentos “wow”, escenas de alta `energy`.

## 3. Taxonomía de escenas (“Scene Model”)

Una escena se define por parámetros semánticos, independientes de valores DMX concretos. Esto permite seleccionar inteligentemente sin conocer aún la salida por fixture.

### 3.1. Parámetros principales

- `energy` (1–5): 1 = muy suave; 5 = extremadamente intensa.
- `palette`: conjuntos base, p.ej. `warm`, `cool`, `neutral`, `mono_blue`, `rainbow`.
- `motion`: `static`, `slow`, `medium`, `fast`; define velocidad de chases/transiciones.
- `strobe`: `none`, `soft`, `hard`; controla permiso e intensidad de estrobo.
- `focus`: categoría protagonista: `wash`, `puntuales`, `special`, `mixed`.

## 4. Diseño de escenas base (“Core Looks”)

Catálogo limitado de escenas canónicas que sirven como look directo o base para variaciones.

### 4.1. Escenas de Wash (principales)

- `wash_warm_soft`: `energy`=1, `palette`=`warm`, `motion`=`static`.
- `wash_cool_soft`: `energy`=1–2, `palette`=`cool`.
- `wash_white_intense`: `energy`=3, `palette`=`neutral`.
- `wash_dual_split`: mitad `warm` / mitad `cool`, `motion`=`slow`.

### 4.2. Escenas con puntuales

- `accent_hit`: puntuales dan golpes breves, principales suaves, `energy`=3–4.
- `puntuales_fade_color`: transiciones lentas en puntuales sobre wash estático.
- `puntuales_sync_beats`: encendido en beats seleccionados (p.ej. 1 y 3).

### 4.3. Escenas especiales

- `superfly_auto_slow`: efecto suave, `energy`=3.
- `superfly_auto_fast`: alto movimiento, `energy`=5.
- `superparty_full_rig`: para picos energéticos; Superfly + puntuales + principales en chase rápido.

## 5. Reglas de aplicación según la música

La escena se deriva de características musicales en tiempo real.

### 5.1. Por nivel de energía musical

- `energy` 1–2 (intro, versos suaves, outro): escenas `focus`=`wash`; sin `strobe`; puntuales apagados o discretos; especiales prohibidos.
- `energy` 3 (verso fuerte, buildup suave): wash + puntuales leves; algún `motion` lento; `strobe` solo si `soft`.
- `energy` 4–5 (estribillo, drop, picos): activar puntuales como acento; permitir Superfly; chases rápidos; `strobe` moderado (`soft`) o `hard` solo en momentos clave.

## 6. Reglas adicionales de variedad y control

Evitan saturación y preservan coherencia.

- `palette`: no repetir la misma más de dos escenas seguidas.
- `strobe`: no encadenar escenas con `strobe`=`hard`; no mantener estrobo más de X segundos (parametrizable).
- Especiales: Superfly solo si `energy` ≥ 4 y apagado tras ≤ Y segundos salvo casos especiales.
- Puntuales: no permanecen encendidos de forma continua; solo hits rítmicos o efectos breves.

## 7. Algoritmo de selección de escenas

El motor evalúa `energy` musical, `tempo`, sección detectada (intro/verse/pre/chorus/drop) y el historial para evitar repeticiones indeseadas.

```pseudo
function seleccionar_escena(context):
    energy = context.energy
    palette_actual = context.last_palette
    ultima = context.last_scene

    candidatas = escenas
        .filter(e.energy ∈ [energy-1, energy+1])
        .filter(e.palette != palette_actual)
        .filter(e != ultima)

    if energy < 3:
        candidatas = candidatas.filter(e.focus == "wash")

    if context.is_drop:
        candidatas = candidatas.filter(e.focus in ["puntuales", "special"])

    if context.strobe_allowed == false:
        candidatas = candidatas.filter(e.strobe == "none")

    return elegir_probabilisticamente(candidatas)
```

## 8. Traducción de escena → valores DMX

Una vez seleccionada la escena semántica:

- Cargar definición base para principales, puntuales y especiales.
- Aplicar `palette` y `motion`.
- Ajustar efectos (`strobe`, Superfly) según `strobe`, `motion` y `energy`.
- Enviar valores DMX por fixture según su diccionario de canales.

## 9. Ventajas de esta metodología

- Escalable a nuevos fixtures.
- Fácil de depurar.
- Separa la lógica musical de la buena programación lumínica.
- Produce shows coherentes y variados sin intervención manual.
- Compatible con rigs small/medium de directo.
