// Lee params de stdin, llama GitLab API, imprime JSON a stdout
const params = JSON.parse(await new Response(Deno.stdin.readable).text());
const { project_id, issue_id } = params;

const token = Deno.env.get("GITLAB_TOKEN") ?? "";
const url = `https://project.comsatel.com.pe/api/v4/projects/${project_id}/issues/${issue_id}`;

const res = await fetch(url, {
  headers: token ? { "PRIVATE-TOKEN": token } : {},
});
const issue = await res.json();

console.log(JSON.stringify({
  title: issue.title,
  description: issue.description,
  state: issue.state,
  labels: issue.labels,
}));
