---
name: "gitlab_manager"
description: "Gestiona grupos, usuarios, issues y milestones en GitLab."
version: "1.0.0"
author: "Ilver Anache"
capabilities:
  - "Gestión de grupos y usuarios en GitLab"
  - "Administración de issues (creación, listado, actualización)"
  - "Gestión de milestones de proyectos y grupos"
---

# GitLab Manager Skill

Este skill permite gestionar grupos, usuarios, issues y milestones en una instancia de GitLab a través de su API REST v4.

## Configuración

Se requiere configurar la siguiente variable de entorno:
- `GITLAB_TOKEN`: Token de acceso personal con permisos suficientes.
- `GITLAB_URL`: (Opcional) URL de la instancia de GitLab. Por defecto: `https://project.comsatel.com.pe`.

## Herramientas principales

- **Grupos**: `list_groups`, `get_group`, `create_group`
- **Usuarios**: `list_users`
- **Proyectos**: `list_projects`
- **Issues**: `list_issues`, `create_issue`, `update_issue`
- **Milestones**: `list_milestones`, `create_milestone`

