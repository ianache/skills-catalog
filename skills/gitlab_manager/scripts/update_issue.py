from skills.gitlab_manager.scripts.gitlab_client import GitLabClient
from typing import List

def execute(project_id: int, issue_iid: int, **kwargs):
    client = GitLabClient()
    issue = client.update_issue(
        project_id=project_id, 
        issue_iid=issue_iid,
        **kwargs
    )
    return issue
