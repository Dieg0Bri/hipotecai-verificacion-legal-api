# verificacion-legal-api

Servicio Python/FastAPI **nuevo (no tiene equivalente en ISA1)**. Ejecuta un motor de reglas sobre la síntesis del estudio hipotecario y emite hallazgos legales para que el abogado revise antes de validar el estudio.

## Endpoints

| Método | Ruta                       | Descripción |
|--------|----------------------------|-------------|
| GET    | `/health`                  | Health |
| GET    | `/reglas`                  | Catálogo de reglas registradas |
| POST   | `/verificar`               | `{folio, persistir}` → corre todas las reglas y persiste hallazgos |
| GET    | `/hallazgos/{folio}`       | Lista de hallazgos persistidos en `dt_hallazgos` |

## Catálogo de reglas v0

| ID         | Categoría     | Severidad | Pregunta que responde |
|------------|---------------|-----------|------------------------|
| `R-CD-001` | cadena_dominio | alta     | ¿El titular del Cert. Dominio Vigente coincide con el último comprador en escrituras? |
| `R-G-001`  | gravamenes    | alta      | ¿Las hipotecas en escrituras aparecen en el certificado vigente del CBR? |
| `R-G-002`  | gravamenes    | crítica   | ¿El certificado dice 'libre de gravámenes' a pesar de existir escrituras de hipoteca? |
| `R-V-001`  | vigencia      | media     | ¿Los certificados CBR tienen menos de 30 días de antigüedad? |
| `R-V-002`  | vigencia      | baja      | ¿El certificado SII tiene menos de 180 días? |
| `R-CD-D-001` | dimensional | media    | ¿La superficie construida en SII coincide con el plano (tolerancia 1 m²)? |
| `R-N-001`  | normativa     | alta      | ¿El destino del inmueble está permitido por la zonificación del plan regulador? |
| `S-INC-001` | sintetizador | (heredada) | Discrepancias inter-fuente detectadas por el sintetizador-api |

## Severidades

- **`critica`** — bloquea el cierre del estudio sin revisión humana explícita.
- **`alta`** — debe ser explicada o resuelta antes de emitir informe.
- **`media`** — observación documentada, normalmente requiere acción.
- **`baja`** — recordatorio.
- **`info`** — referencia, no bloquea.

## Estructura de un hallazgo

```jsonc
{
  "regla_id": "R-G-002",
  "severidad": "critica",
  "titulo": "Coherencia certificado libre vs escrituras de hipoteca",
  "descripcion": "El certificado declara la propiedad libre de gravámenes…",
  "detalle": { "hipotecas_en_escrituras": 1 },
  "recomendacion": "Confirmar que los alzamientos correspondientes estén inscritos."
}
```

## Cómo agregar una nueva regla

1. Crear `src/reglas/rules/<categoria>.py` con función `regla_<nombre>(synthesis: dict) → list[dict]`
2. Exportar `REGLAS_<CATEGORIA>` con metadata (`id`, `titulo`, `severidad`, `categoria`, `check`)
3. Importar en `src/reglas/engine.py` y agregar a `REGLAS`

## Desarrollo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8087
```
