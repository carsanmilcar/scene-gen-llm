# Guía rápida

## Requisitos
- Python 3.9 o superior
- QLC+ instalado para probar los `.qxw`
- Opcional: entorno virtual (`python -m venv .venv`)

## Instalación del proyecto
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .
```

## Ejecutar el generador
```bash
python -m scenegen.cli scene1.qxw "Describe la vibra del tema" --output scene1_generada.qxw
```
- `workspace`: fichero `.qxw` base.
- `description`: texto libre que se envía al LLM para generar escenas.
- `--output`: ruta donde se escribirá el workspace con las escenas nuevas; por defecto `<workspace>_generated.qxw`.

El pipeline intentará primero usar el selector basado en reglas si se le pasa un contexto (`SceneContext`). Si no hay catálogo o no se cumplen las reglas, recurre al LLM y finalmente a un fallback determinista.

## Construir la documentación
```bash
python -m pip install -r docs/requirements.txt
python -m sphinx -b html docs docs/_build/html
```
Abre `docs/_build/html/index.html` en el navegador para ver el resultado.
