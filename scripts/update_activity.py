#!/usr/bin/env python3
import json
import re
import urllib.request

USERNAME = "Hardikrepo"
README = "README.md"
START = "<!-- ACTIVITY:START -->"
END = "<!-- ACTIVITY:END -->"
MAX_LINES = 5

ICONS = {
    "PushEvent": "\U0001F528",
    "PullRequestEvent": "\U0001F500",
    "IssuesEvent": "\U0001F41B",
    "CreateEvent": "\U0001F195",
    "ForkEvent": "\U0001F374",
    "ReleaseEvent": "\U0001F3F7️",
}


def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/events/public",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USERNAME},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def describe(event):
    repo = event["repo"]["name"]
    etype = event["type"]
    icon = ICONS.get(etype)
    if icon is None:
        return None
    url = f"https://github.com/{repo}"

    if etype == "PushEvent":
        # GitHub's public events feed no longer includes the commits array,
        # so fall back to the branch ref instead of a commit count.
        branch = event["payload"].get("ref", "").rsplit("/", 1)[-1]
        suffix = f" ({branch})" if branch else ""
        return f"{icon} Pushed to [`{repo}`]({url}){suffix}"
    if etype == "PullRequestEvent":
        action = event["payload"].get("action", "updated")
        pr = event["payload"].get("pull_request", {})
        return f"{icon} {action.capitalize()} a PR in [`{repo}`]({pr.get('html_url', url)})"
    if etype == "IssuesEvent":
        action = event["payload"].get("action", "updated")
        return f"{icon} {action.capitalize()} an issue in [`{repo}`]({url})"
    if etype == "CreateEvent":
        ref_type = event["payload"].get("ref_type")
        if ref_type != "repository":
            return None
        return f"{icon} Created [`{repo}`]({url})"
    if etype == "ForkEvent":
        return f"{icon} Forked [`{repo}`]({url})"
    if etype == "ReleaseEvent":
        return f"{icon} Published a release in [`{repo}`]({url})"
    return None


def main():
    events = fetch_events()
    lines = []
    seen = set()
    for event in events:
        line = describe(event)
        if not line:
            continue
        key = (event["repo"]["name"], event["type"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {line}")
        if len(lines) == MAX_LINES:
            break

    block = "\n".join(lines) if lines else "- No recent public activity."

    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new_content = pattern.sub(f"{START}\n{block}\n{END}", content)

    with open(README, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    main()
