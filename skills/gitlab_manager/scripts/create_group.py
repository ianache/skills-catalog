from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(name: str, path: str, parent_id: int = None):
    client = GitLabClient()
    group = client.create_group(name=name, path=path, parent_id=parent_id)
    return group
