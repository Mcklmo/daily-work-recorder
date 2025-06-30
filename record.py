import requests
import datetime
import os


def get_github_daily_work(username, target_date_str, github_token):
    base_url = "https://api.github.com"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    next_day = target_date + datetime.timedelta(days=1)

    all_events = []
    page = 1
    # Note: GitHub API has limits. /users/:user/events is often limited to public events
    # and up to 300 events in the last 90 days. For comprehensive private activity,
    # it's better to use /user/events for the authenticated user.
    # The authenticated user events (GET /user/events) include private activity.
    # It still has rate limits and potentially pagination.
    # Also, events older than 90 days for non-authenticated users are not available.
    # For a specific user's *private* activities, make sure the token is for *that* user.
    while True:
        # Using /user/events for the authenticated user (token owner) to get private activity
        events_url = f"{base_url}/users/{username}/events?per_page=100&page={page}"
        # If your token is for *your* user, and you want *your* private events, use:
        # events_url = f"{base_url}/user/events?per_page=100&page={page}"

        response = requests.get(events_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        current_events = response.json()

        if not current_events:
            break  # No more events

        all_events.extend(current_events)

        # Simple check to stop early if we've passed the target date
        # More robust pagination would involve checking 'Link' header for 'next' rel
        if (
            len(current_events) < 100
            or datetime.datetime.strptime(
                current_events[-1]["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            < target_date
        ):
            break
        page += 1

    daily_work_summary = f"--- GitHub Work Report for {target_date_str} ---\n\n"

    # Organize activity by repository
    repo_activities = {}

    for event in all_events:
        event_date = datetime.datetime.strptime(
            event["created_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).date()

        if event_date == target_date:
            repo_name = (
                event["repo"]["name"] if "repo" in event else "Unknown Repository"
            )
            if repo_name not in repo_activities:
                repo_activities[repo_name] = {
                    "commits": [],
                    "pull_requests": [],
                    "issues": [],
                    "comments": [],
                    "reviews": [],
                }

            if event["type"] == "PushEvent":
                for commit in event["payload"]["commits"]:
                    # Filter commits by author, as PushEvent can contain multiple authors
                    if (
                        commit["author"]["email"]
                        == f"{username}@users.noreply.github.com"
                        or commit["author"]["name"] == username
                    ):  # Or check your actual commit email/name
                        repo_activities[repo_name]["commits"].append(
                            f"- Commit: '{commit['message'].splitlines()[0]}' ({commit['sha'][:7]}) "
                            f"on [{repo_name}](https://github.com/{repo_name}/commit/{commit['sha']})"
                        )
            elif event["type"] == "PullRequestEvent":
                pr = event["payload"]["pull_request"]
                action = event["payload"]["action"]
                repo_activities[repo_name]["pull_requests"].append(
                    f"- PR {action}: #{pr['number']} - '{pr['title']}' "
                    f"on [{repo_name}](https://github.com/{repo_name}/pull/{pr['number']})"
                )
            elif event["type"] == "IssuesEvent":
                issue = event["payload"]["issue"]
                action = event["payload"]["action"]
                repo_activities[repo_name]["issues"].append(
                    f"- Issue {action}: #{issue['number']} - '{issue['title']}' "
                    f"on [{repo_name}](https://github.com/{repo_name}/issues/{issue['number']})"
                )
            elif event["type"] == "IssueCommentEvent":
                issue = event["payload"]["issue"]
                comment = event["payload"]["comment"]
                repo_activities[repo_name]["comments"].append(
                    f"- Commented on issue #{issue['number']}: '{issue['title']}' - "
                    f"[{repo_name}](https://github.com/{repo_name}/issues/{issue['number']}#issuecomment-{comment['id']})"
                )
            elif event["type"] == "PullRequestReviewEvent":
                pr = event["payload"]["pull_request"]
                state = event["payload"]["review"]["state"]
                repo_activities[repo_name]["reviews"].append(
                    f"- Reviewed PR #{pr['number']} ('{pr['title']}') - State: {state.capitalize()} "
                    f"on [{repo_name}](https://github.com/{repo_name}/pull/{pr['number']}/files/)"
                )
            # Add more event types as needed (e.g., CreateEvent for new branches/repos, DeleteEvent, etc.)

    if not repo_activities:
        daily_work_summary += "No significant GitHub activity found for this day."
    else:
        for repo, activities in repo_activities.items():
            daily_work_summary += f"### Repository: {repo}\n"
            if activities["commits"]:
                daily_work_summary += (
                    "  * **Commits:**\n" + "\n".join(activities["commits"]) + "\n"
                )
            if activities["pull_requests"]:
                daily_work_summary += (
                    "  * **Pull Requests:**\n"
                    + "\n".join(activities["pull_requests"])
                    + "\n"
                )
            if activities["issues"]:
                daily_work_summary += (
                    "  * **Issues:**\n" + "\n".join(activities["issues"]) + "\n"
                )
            if activities["comments"]:
                daily_work_summary += (
                    "  * **Comments:**\n" + "\n".join(activities["comments"]) + "\n"
                )
            if activities["reviews"]:
                daily_work_summary += (
                    "  * **Reviews:**\n" + "\n".join(activities["reviews"]) + "\n"
                )
            daily_work_summary += "\n"  # Add a newline for separation

    return daily_work_summary


# --- How to use it ---
if __name__ == "__main__":
    # It's highly recommended to use environment variables for sensitive info
    GITHUB_USERNAME = os.getenv(
        "GITHUB_USERNAME", "your_github_username"
    )  # Replace or set ENV
    GITHUB_TOKEN = os.getenv(
        "GITHUB_TOKEN"
    )  # Set this securely as an environment variable

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it with your GitHub Personal Access Token.")
        exit(1)

    # Example usage for a specific day
    target_day = "2025-05-15"  # Replace with the desired date

    report = get_github_daily_work(GITHUB_USERNAME, target_day, GITHUB_TOKEN)
    print(report)

    # You could then write this report to a file for your client:
    # with open(f"github_report_{target_day}.md", "w") as f:
    #     f.write(report)
    # print(f"Report saved to github_report_{target_day}.md")

    # To generate reports for the past month (example):
    # today = datetime.date.today()
    # for i in range(30): # For the last 30 days
    #     day = today - datetime.timedelta(days=i)
    #     day_str = day.strftime("%Y-%m-%d")
    #     report = get_github_daily_work(GITHUB_USERNAME, day_str, GITHUB_TOKEN)
    #     print(f"\n--- Report for {day_str} ---\n")
    #     print(report)
    #     # Optionally save each day's report
    #     # with open(f"github_report_{day_str}.md", "w") as f:
    #     #     f.write(report)
