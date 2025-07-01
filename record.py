import requests
import datetime
import os
from dotenv import load_dotenv
import pendulum

load_dotenv()


def get_github_daily_work(
    username, target_date_range: pendulum.Interval, github_token, org_name
):
    base_url = "https://api.github.com"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    all_events = []
    page = 1
    # Note: GitHub API has limits. For organization events, we use /orgs/{org}/events
    # This gives us public events for the organization.
    # For private events, you need to use /user/events/orgs/{org} if you're authenticated
    # and have access to the organization.

    while True:
        # Try authenticated user's organization events first (includes private repos)
        # This requires the token to belong to a user who is a member of the organization
        events_url = f"{base_url}/orgs/{org_name}/events?per_page=100&page={page}"
        response = requests.get(events_url, headers=headers)

        response.raise_for_status()
        current_events = response.json()

        if not current_events:
            break  # No more events

        # Filter events by the specific username since org events include all users
        user_events = []
        for event in current_events:
            if event.get("actor", {}).get("login") == username:
                user_events.append(event)

        all_events.extend(user_events)
        page += 1

    # Organize activity by repository
    repo_activities = {}

    for event in all_events:
        event_date = pendulum.parse(event["created_at"]).date()
        repo_name = event["repo"]["name"] if "repo" in event else "Unknown Repository"

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
                    commit["author"]["email"] == f"{username}@users.noreply.github.com"
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
        return "No significant GitHub activity found for this period."
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
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "mcklmo")  # Replace or set ENV
    GITHUB_TOKEN = os.getenv(
        "GITHUB_TOKEN"
    )  # Set this securely as an environment variable

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it with your GitHub Personal Access Token.")
        exit(1)

    # Example usage for a specific day
    dt = pendulum.now()

    # A period is the difference between 2 instances
    period = dt - dt.subtract(days=30)

    report = get_github_daily_work(
        GITHUB_USERNAME, period, GITHUB_TOKEN, "BC-Technology"
    )
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
