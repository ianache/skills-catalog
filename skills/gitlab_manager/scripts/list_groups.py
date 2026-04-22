from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(search: str = None):
    client = GitLabClient()
    groups = client.list_groups(search=search)
    
    if not groups:
        return f"No se encontraron grupos que coincidan con '{search}'"
    
    # Si hay muchos resultados, devolvemos un resumen para no saturar el contexto
    # pero el ArtifactManager guardará el JSON completo si supera el umbral.
    if len(groups) > 10:
        summary = {
            "total_found": len(groups),
            "matches": [{"id": g["id"], "name": g["name"], "full_path": g["full_path"]} for g in groups[:10]],
            "note": f"Se han encontrado {len(groups)} grupos. Se muestran los primeros 10. El resultado completo está disponible en el artefacto generado."
        }
        return summary
        
    return groups
