from skills.gitlab_manager.scripts.gitlab_client import GitLabClient
from typing import List

def execute(project_id: int, title: str, description: str = None, labels: List[str] = None, assignee_ids: List[int] = None):
    client = GitLabClient()
    issue = client.create_issue(
        project_id=project_id, 
        title=title, 
        description=description, 
        labels=labels, 
        assignee_ids=assignee_ids
    )
    return issue
