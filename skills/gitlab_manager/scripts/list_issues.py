from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(project_id: int = None, group_id: int = None, state: str = None, search: str = None):
    client = GitLabClient()
    issues = client.list_issues(project_id=project_id, group_id=group_id, state=state, search=search)
    
    if not issues:
        return f"No se encontraron issues"
        
    if len(issues) > 10:
        summary = {
            "total_found": len(issues),
            "matches": [{"iid": i["iid"], "title": i["title"], "state": i["state"]} for i in issues[:10]],
            "note": f"Se han encontrado {len(issues)} issues. Se muestran los primeros 10."
        }
        return summary
        
    return issues
