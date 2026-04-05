import os
import gitlab
from typing import Dict, Any

def execute(project_id: int, specification: str, issue_id: int = None) -> Dict[str, Any]:
    """
    Registra o actualiza una historia de usuario en GitLab.
    """
    url = "https://project.comsatel.com.pe"
    token = os.getenv("GITLAB_TOKEN")
    
    if not token:
        return {"error": "GITLAB_TOKEN no configurado en el entorno (.env)"}
    
    try:
        # Conectar a GitLab
        gl = gitlab.Gitlab(url=url, private_token=token)
        gl.auth()
        
        project = gl.projects.get(project_id)
        
        if issue_id:
            # Actualizar issue existente
            issue = project.issues.get(issue_id)
            issue.description = specification
            issue.save()
            return {
                "status": "success",
                "action": "update",
                "issue_id": issue.iid,
                "project_id": project_id,
                "web_url": issue.web_url
            }
        else:
            # Crear nuevo issue
            # Usar la primera línea de la especificación como título si es corta
            title = specification.split('\n')[0].strip() if specification else "Nueva Historia de Usuario"
            if len(title) > 60:
                title = title[:57] + "..."
            if not title:
                title = "Especificación de User Story"
                
            issue = project.issues.create({
                'title': title,
                'description': specification
            })
            return {
                "status": "success",
                "action": "create",
                "issue_id": issue.iid,
                "project_id": project_id,
                "web_url": issue.web_url
            }
            
    except Exception as e:
        return {"error": f"Error en GitLab: {str(e)}"}