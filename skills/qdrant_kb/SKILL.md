# Skill: Qdrant Knowledge Base

Este skill permite al agente interactuar con una base de conocimientos vectorial alojada en Qdrant.

## Capacidades

- **Indexación**: Puedes guardar información estructurada o no estructurada en la colección `mykb`.
- **Búsqueda**: Puedes realizar búsquedas semánticas para recuperar contexto relevante según la consulta del usuario.

## Instrucciones para el Agente

1. Cuando el usuario proporcione información que deba ser recordada a largo plazo (lecciones aprendidas, requerimientos, glosarios), utiliza `upsert_kb_document`.
2. Incluye siempre metadatos relevantes para facilitar la trazabilidad (ej: `id_proyecto`, `source`).
3. Antes de responder a una pregunta compleja sobre el dominio del proyecto, utiliza `search_kb` para verificar si hay información previa relevante.
4. Si la búsqueda no devuelve resultados claros, indícalo al usuario.

## Configuración requerida (.env)
- `QDRANT_URL`: URL del servidor Qdrant (o `:memory:` para pruebas locales).
- `QDRANT_API_KEY`: API Key si el servidor requiere autenticación.
- `EMBEDDING_MODEL`: Modelo de LiteLLM para generar vectores (ej: `text-embedding-3-small`).
