import json, os, re, urllib.parse, urllib.request
from datetime import datetime

USER = os.environ.get("GH_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
TOKEN = os.environ.get("GITHUB_TOKEN")
LIMIT = 10                      # rows shown in the table
EXTERNAL_ONLY = False           # True = only PRs to other people's repos

q = f"author:{USER} type:pr" + (f" -user:{USER}" if EXTERNAL_ONLY else "")
url = f"https://api.github.com/search/issues?q={urllib.parse.quote(q)}&sort=updated&order=desc&per_page=100"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
if TOKEN:
    req.add_header("Authorization", f"Bearer {TOKEN}")
items = json.load(urllib.request.urlopen(req))["items"]

def status(i):
    if i["pull_request"].get("merged_at"):
        return "🟣 Merged"
    return "🟢 Open" if i["state"] == "open" else "🔴 Closed"

merged = sum(1 for i in items if i["pull_request"].get("merged_at"))
opened = sum(1 for i in items if i["state"] == "open")
closed = len(items) - merged - opened

lines = [
    f"**{len(items)}** PRs &nbsp;|&nbsp; 🟣 **{merged}** merged &nbsp;|&nbsp; 🟢 **{opened}** open &nbsp;|&nbsp; 🔴 **{closed}** closed",
    "",
    "| Repository | Pull Request | Status | Updated |",
    "|---|---|---|---|",
]
for i in items[:LIMIT]:
    repo = i["repository_url"].split("repos/")[1]
    title = i["title"].replace("|", "\\|")
    date = datetime.strptime(i["updated_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y")
    lines.append(f"| [{repo}](https://github.com/{repo}) | [#{i['number']} {title}]({i['html_url']}) | {status(i)} | {date} |")
if not items:
    lines.append("| – | No pull requests yet | – | – |")

block = "<!--PR_START-->\n" + "\n".join(lines) + "\n<!--PR_END-->"
path = os.environ.get("README_PATH", "README.md")
text = open(path, encoding="utf-8").read()
new = re.sub(r"<!--PR_START-->.*?<!--PR_END-->", lambda m: block, text, flags=re.S)
if new != text:
    open(path, "w", encoding="utf-8").write(new)
print(f"{len(items)} PRs found")
