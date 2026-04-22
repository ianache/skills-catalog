from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(search: str = None, username: str = None):
    client = GitLabClient()
    users = client.list_users(search=search, username=username)
    
    if not users:
        return f"No se encontraron usuarios"
        
    if len(users) > 10:
        summary = {
            "total_found": len(users),
            "matches": [{"id": u["id"], "username": u["username"], "name": u["name"]} for u in users[:10]],
            "note": f"Se han encontrado {len(users)} usuarios. Se muestran los primeros 10."
        }
        return summary
        
    return users
