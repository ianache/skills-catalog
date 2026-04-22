from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(project_id: int = None, group_id: int = None, state: str = None, search: str = None):
    client = GitLabClient()
    milestones = client.list_milestones(project_id=project_id, group_id=group_id, state=state, search=search)
    return milestones
