from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(search: str = None, group_id: int = None):
    client = GitLabClient()
    projects = client.list_projects(search=search, group_id=group_id)
    
    if not projects:
        return f"No se encontraron proyectos"
        
    if len(projects) > 10:
        summary = {
            "total_found": len(projects),
            "matches": [{"id": p["id"], "name": p["name"], "path_with_namespace": p["path_with_namespace"]} for p in projects[:10]],
            "note": f"Se han encontrado {len(projects)} proyectos. Se muestran los primeros 10."
        }
        return summary
        
    return projects
