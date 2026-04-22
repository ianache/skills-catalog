from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(group_id: int):
    client = GitLabClient()
    group = client.get_group(group_id=group_id)
    return group
