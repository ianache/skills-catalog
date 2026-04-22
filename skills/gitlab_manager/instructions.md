
# Instrucciones de Uso - GitLab Manager

Este skill interactúa con la API v4 de GitLab. Para la mayoría de las operaciones, necesitarás el `project_id` o `group_id`.

## Comportamiento esperado

1. **Búsqueda**: Antes de crear un issue o milestone, es recomendable listar los existentes para evitar duplicados.
2. **Identificación**: Si el usuario se refiere a un proyecto por nombre, utiliza `list_groups` o herramientas de búsqueda de proyectos (si estuvieran disponibles) para obtener el ID numérico necesario.
3. **Labels**: Al crear o actualizar issues, envía las etiquetas como una lista de strings. El cliente se encargará de formatearlas.
4. **Fechas**: Para los milestones, utiliza el formato `YYYY-MM-DD`.

## Detalles de Herramientas

### list_groups
Lista los grupos disponibles. Utiliza el parámetro `search` para filtrar.

### create_group
Crea un nuevo grupo. Requiere `name` y `path`.

### list_users
Lista los usuarios. Útil para obtener `assignee_ids` antes de crear un issue.

### list_issues
Lista issues de un proyecto (`project_id`) o grupo (`group_id`). Puedes filtrar por `state` (opened, closed, all).

### create_issue
Crea un issue. Requiere `project_id` y `title`.

### update_issue
Actualiza un issue existente usando su `project_id` e `issue_iid`. Permite cerrar el issue con `state_event="close"`.

### list_milestones
Lista milestones de un proyecto o grupo.

### create_milestone
Crea un milestone. Requiere `title` y opcionalmente `start_date` y `due_date`.
