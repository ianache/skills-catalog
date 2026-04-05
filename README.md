# 🎓 Intelligent Skills Agent

Este proyecto es un agente de IA modular diseñado para descubrir, cargar y ejecutar herramientas (**skills**) dinámicamente. Utiliza **LiteLLM** para soportar múltiples proveedores (Gemini, Groq, OpenAI, etc.) y cuenta con una base de conocimientos semántica sobre **Qdrant**.

## 🚀 Características Principales

- **Arquitectura Modular de Skills**: Carga automática de lógica, instrucciones y assets desde la carpeta `skills/`.
- **Soporte Multiproveedor**: Integración con Gemini, Groq, Anthropic y más a través de LiteLLM.
- **Base de Conocimientos Semántica**: Skill de Qdrant integrado para indexación (`upsert_kb_document`) y búsqueda (`search_knowledge_base`) mediante embeddings.
- **Orquestación de Herramientas**: El agente puede encadenar habilidades (ej: consultar GitLab, buscar contexto en Qdrant y redactar una historia de usuario).
- **Consola Interactiva**: Comandos especiales para gestionar el agente en tiempo real:
  - `/reload`: Recarga configuración y skills sin reiniciar.
  - `/settings`: Muestra la configuración actual y estado de APIs.
  - `/confidential`: Permite verificar el valor de las claves API configuradas.
  - `/help`: Muestra la ayuda disponible.

## 🛠️ Instalación y Configuración

### Requisitos
- **Python 3.12+**
- **uv** (Gestor de paquetes moderno)

### Setup

1. **Clonar y Sincronizar**:
   ```powershell
   git clone <repo-url>
   cd skills-catalog
   uv sync
   ```

2. **Configurar Entorno**:
   Copia el archivo de ejemplo y completa tus claves:
   ```powershell
   cp .env.example .env
   ```
   *Nota: El agente prioriza las variables de entorno de tu terminal sobre el archivo `.env`.*

3. **Configuración de Qdrant**:
   Puedes usar una instancia en memoria o remota:
   - Local: `QDRANT_URL=:memory:`
   - Remota: `QDRANT_URL=http://tu-servidor:6333`

## ⌨️ Uso

Inicia el agente con el siguiente comando:
```powershell
uv run .\main.py
```

### Ejemplos de Prompt
- *"Especificar la historia de usuario para el issue #123 del proyecto 456."*
- *"Añadir a la base de conocimientos: El patrón de diseño Circuit Breaker ayuda a evitar fallos en cascada."*
- *"Consultar la base de conocimientos por 'microservicios'."*

## 🏗️ Estructura del Proyecto

```text
.
├── skills/               # Directorio raíz de habilidades
│   ├── qdrant_kb/        # Skill de Gestión de Conocimientos
│   ├── especificar_user_story/ # Skill de Metodologías Ágiles
│   └── ...
├── main.py               # Agente principal y CLI
├── catalog.yaml          # Registro central de metadatos de skills
├── pyproject.toml        # Dependencias y configuración de uv
└── .env                  # Variables de entorno (no incluido en git)
```

## 🤝 Contribución

Ilver Anache - [GitHub](https://github.com/ianache)
