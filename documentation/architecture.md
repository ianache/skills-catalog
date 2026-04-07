# Arquitectura de Skills Catalog

Este informe técnico consolida nuestra sesión de diseño para la evolución de tu repositorio `skills-catalog`. Transicionamos de una implementación estática de **Google AI ADK** en Python hacia una **Plataforma Agéntica de Grado Empresarial** con observabilidad en tiempo real y persistencia robusta.

![Arquitectura Global](images/sketch-architectura.png)

---

## Parte 1: Keypoints and Reflexions

* **De Script a Sistema:** La solución deja de ser un "script que corre" para convertirse en un ecosistema desacoplado. El motor de ejecución (Python/ADK) se separa de la capa de entrega (Node.js/WebSockets).
* **La IA como Proceso de Negocio:** Al implementar eventos de pasos (`AGENT_STEP`), transformamos la "caja negra" del LLM en un flujo de trabajo auditable. Esto es vital para ganar la confianza de stakeholders en entornos sensibles como SAP u Oracle.
* **Eficiencia Cognitiva (Context Hygiene):** La decisión de no saturar el context window con datos pesados mediante el patrón **Claim Check** asegura que Gemini mantenga el enfoque en el razonamiento lógico, reduciendo alucinaciones y costos por tokens innecesarios.
* **El Factor Humano (HITL):** Entendemos que la autonomía total es un riesgo. El diseño permite que el agente "pida permiso", convirtiéndolo en un colaborador aumentado en lugar de un proceso desatendido peligroso.

---

## Parte 2: Architectural Decisions (Python-Centric)

### 2.1. Motor de Ejecución: Google AI ADK "Pure Python"
* **Decisión:** Mantener el núcleo en ADK nativo en lugar de LangGraph para minimizar la sobrecarga y maximizar el control sobre el ciclo de vida del agente.
* **Intercepción:** Uso de un **Wrapper Asíncrono** sobre el `SkillToolset` para inyectar telemetría y persistencia de forma transparente.

### 2.2. Persistencia Dual y Gestión de Artifacts
* **Hot Path (Redis Streams):** Fuente de verdad para eventos en tiempo real. Permite que el Gateway de Node.js "empuje" actualizaciones al frontend sin consultar la base de datos relacional.
* **Cold Path (PostgreSQL):** Almacenamiento persistente de **Artifacts** (payloads >2KB) y traza histórica de auditoría.
* **Referenciación:** El agente solo recibe un `artifact_id` (puntero) en su historial de mensajes, manteniendo la ventana de contexto limpia.

### 2.3. Comunicación Multi-tenant (WebSocket Gateway)
* **Stack:** Node.js + Socket.io.
* **Aislamiento:** Segmentación mediante **Namespaces** por cliente y **Rooms** por `session_id`.
* **Sincronía:** El Gateway implementa una lógica de "Sync on Connect" leyendo los últimos eventos de Redis (`XRANGE`) para recuperar la línea de tiempo si el usuario refresca la pantalla.



---

## Parte 3: ReqSpec for Antigravity / Gemini

Para implementar esta arquitectura sobre tu código actual, entrega estas especificaciones técnicas a Gemini:

### REQ-01: Auditoría de Skills (Python)
> *"Implementa un decorador asíncrono `@audit_skill` en Python que envuelva todas las funciones del `SkillToolset` de mi proyecto ADK. El decorador debe publicar un evento JSON en Redis Streams (`agent:events`) antes y después de la ejecución. El esquema debe seguir el estándar: `{"event_type": "AGENT_STEP", "payload": {"step_name": tool_name, "status": "running/success/failed"}, "session_id": sid}`."*

![Diagrama 1](images/reqspec1.png)

Desglose Visual del Diagrama:

1. Emisor: Motor de Agentes (Python ADK): En la parte superior, mostramos el origen de la "inteligencia". El orquestador de Python con ADK está ejecutando un skill.

2. REQ-01 Middleware: @audit_skill Decorator: Esta es la pieza central.

   - Intercepción: El decorador actúa como un Wrapper. Captura el START_STEP y el FINISH_STEP.
   - Publicación asíncrona: Utiliza redis-py para enviar eventos JSON a Redis Streams (agent:events) sin bloquear la ejecución de Gemini.

3. Audit Trail (Persistencia): En la parte inferior, implementamos el flujo de auditoría completa.

   - Postgres: Se guardan los "Artifacts" finales y la traza de auditoría completa para cumplimiento (compliance).
   - Redis Streams: La fuente de verdad para los eventos en tiempo real.

4. Reactor Multi-tenant (Node.js/Socket.io): El Gateway de Node.js se suscribe a Redis, filtra por session_id y emite los eventos a los clientes correspondientes, garantizando que un usuario solo vea los pasos de su propio agente.

#### Reflexión Final

Este diagrama visualiza cómo hemos abierto la "tubería de datos" de tus agentes. Ahora, cada skill de tu catálogo informa sobre su inicio, fin y resultado, permitiendo que la auditoría y la reactividad funcionen de forma nativa en tu arquitectura desatendida.

### REQ-02: Gestor de Artifacts y Claim Check

> *"Crea un módulo `artifact_manager.py` que gestione la conexión a PostgreSQL. Si el retorno de un Skill en mi `skills-catalog` es un JSON extenso o texto > 2KB, guárdalo en la tabla `artifacts` y devuelve al Agente una referencia simplificada: `{"__ref": "UUID", "label": "Nombre del dato"}`. Asegúrate de que el Agente esté instruido para informar al usuario sobre este ID."*

![Diagrama 2](images/reqspec2.png)

Desglose Visual del Diagrama:

1. Origen del Dato (Agente Python): En la parte superior, mostramos el inicio de la "inteligencia". El orquestador de Python con ADK está ejecutando un skill de tu skills-catalog.

2. REQ-02: Gestor de Artifacts y Claim Check: Esta es la pieza central.

   - Evaluación: Una "balanza" o "regla" evalúa el tamaño del output.
   - Flujo LIGERO (<2KB): El dato crudo vuelve directo al historial de mensajes del agente.
   - Flujo PESADO (>2KB/5000 chars): El dato pesado se guarda en la tabla artifacts de PostgreSQL.
3. Referenciación: Se genera una referencia simplificada ({ "__ref": "UUID", "label": "logs_sap" }).
4. Inyección: El agente recibe esta referencia en su contexto, permitiendo que la ventana de tokens se mantenga limpia.
5. Notificación Reactiva: Se envía un evento ARTIFACT_GENERATED a Redis Streams (agent:events), permitiendo que el Gateway de Node.js notifique al frontend.

#### Reflexión Final

Este diagrama visualiza cómo hemos resuelto el problema de la "Contaminación Cognitiva". Al no saturar la ventana de tokens de Gemini con datos pesados, el agente puede mantener la atención en la lógica y el razonamiento, ahorrando costos y mejorando la precisión. Tendrás una base de datos en Postgres con cada "Artifact" para cumplimiento (compliance) e historial completo de auditoría.

### REQ-03: Gateway de Eventos (Node.js)
> *"Genera un servidor Node.js que use `ioredis` para escuchar el stream `agent:events`. Implementa un servidor Socket.io que, al recibir un mensaje de Redis, lo emita al 'Room' correspondiente al `session_id`. Incluye un middleware de autenticación que valide el `tenant_id` antes de permitir la conexión al socket."*

![Diagrama 3](images/reqspec3.png)

Desglose Visual del Diagrama:

1. Emisor: Motor de Agentes (Python ADK/Redis Streams): En la parte superior, mostramos el origen de la "inteligencia". Los agentes de Python, al ejecutar un skill, emiten un evento JSON a Redis Streams (agent_events).

2. Middleware: Node.js Gateway: Esta es la pieza central.

3. Escucha de Eventos: El Gateway usa ioredis para leer el stream (XREADBLOCK) de forma asíncrona.

4. Autenticación de Middleware: Mostramos un "escudo" que valida el tenant_id en el handshake del WebSocket antes de permitir la conexión.

5. Socket.io Rooms: La lógica clave. Los mensajes se "rutean" a "Rooms" específicos basados en el tenant_id y session_id. Así, un usuario solo ve los pasos de su propio agente.

6. Receptor: Clientes (WebSockets): Múltiples dispositivos (laptop, tablet, phone) reciben la emisión filtrada (io.to(session_id).emit('agent_update', ...)).

7. Sync on Connect: En la parte inferior, implementamos tu requerimiento de resiliencia. Si un usuario se conecta tarde, el Gateway pide un "Sync" a Redis (XRANGE), recupera la historia y la envía para que la línea de tiempo esté completa.

#### Reflexión Final

Este diagrama visualiza cómo hemos logrado que la "inteligencia" de Python se encuentre con la "reactividad" de Node.js sin saturar tu base de datos relacional. El Gateway es ahora un dispatcher puro, rápido y agnóstico de la lógica de negocio de los agentes.

### REQ-04: Lógica de Intervención Humana (HITL)
> *"Define un Skill especial `require_approval`. Cuando se invoque, debe emitir un evento `HITL_REQUEST` a Redis y poner el proceso de Python en espera asíncrona (`asyncio.Future`). El proceso debe reanudarse únicamente cuando se reciba un mensaje en el canal de retorno de Redis `agent:input:{session_id}` con la decisión del usuario."*

![Diagrama 4](images/reqspec4.png)

Desglose Visual del Diagrama:

1. Motor de Agentes (Python Engine): En la parte superior, mostramos el inicio de la "inteligencia". El orquestador de Python con ADK está ejecutando una tarea compleja.

2. REQ-04: Lógica de Intervención Humana (HITL): Esta es la pieza central, dividida en dos fases.

   - Fase 1: Pausa y Solicitud: Un Skill especial detecta la necesidad de aprobación. El agente Python publica un evento HITL_REQUEST en Redis Streams y se pone en estado de espera asíncrona (asyncio.Future). No se cierra el proceso, se pausa de forma eficiente.
   - Fase 2: Notificación y Reanudación: El Gateway de Node.js escucha el evento, filtra por session_id y emite la solicitud vía Socket.io a los clientes correspondientes (laptop ianache, phone global_corp).
3.  Aprobación Humana: El usuario aprueba la acción en su interfaz.
4.  Despertar del Agente: La señal de aprobación viaja de vuelta por Socket.io al Gateway, quien la inyecta en el canal de retorno de Redis. El motor Python lee la señal, "despierta" al agente y reanuda la ejecución con el nuevo contexto.
5.  Watchdog Timeout: Hemos incluido el mecanismo de seguridad. Si el usuario no responde en X minutos, el agente falla de forma segura y se registra el evento.

#### Reflexión Final

Este diagrama visualiza cómo hemos resuelto el problema de la Autonomía Peligrosa. Al tratar la "intervención humana" como un estado de red asíncrono, mantenemos la eficiencia de la plataforma y garantizamos la seguridad en procesos sensibles como despliegues o accesos a SAP.