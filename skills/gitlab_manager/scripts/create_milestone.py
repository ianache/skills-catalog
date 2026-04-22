from skills.gitlab_manager.scripts.gitlab_client import GitLabClient

def execute(project_id: int = None, group_id: int = None, title: str = None, description: str = None, start_date: str = None, due_date: str = None):
    client = GitLabClient()
    milestone = client.create_milestone(
        project_id=project_id,
        group_id=group_id,
        title=title,
        description=description,
        start_date=start_date,
        due_date=due_date
    )
    return milestone
