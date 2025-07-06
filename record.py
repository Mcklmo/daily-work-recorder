import requests
import datetime
import os
from dotenv import load_dotenv
import pendulum
from typing import Dict, List, Any, Optional

load_dotenv()


class GitHubActivityTracker:
    def __init__(self, github_token: str, org_name: str):
        self.github_token = github_token
        self.org_name = org_name
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_org_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories from the organization"""
        repositories = []
        page = 1

        while True:
            url = f"{self.base_url}/orgs/{self.org_name}/repos?per_page=100&page={page}&type=all"
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                print(
                    f"Error fetching repositories: {response.status_code} - {response.text}"
                )
                break

            repos = response.json()
            if not repos:
                break

            repositories.extend(repos)
            page += 1

        return repositories

    def get_commits_for_repo(
        self, repo_name: str, username: str, since: str, until: str
    ) -> List[Dict[str, Any]]:
        """Get commits for a specific repository within date range"""
        commits = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits"
            params = {
                "author": username,
                "since": since,
                "until": until,
                "per_page": 100,
                "page": page,
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                if response.status_code == 409:  # Repository is empty
                    break
                print(
                    f"Error fetching commits for {repo_name}: {response.status_code} - {response.text}"
                )
                break

            repo_commits = response.json()
            if not repo_commits:
                break

            commits.extend(repo_commits)
            page += 1

        return commits

    def get_pull_requests_for_repo(
        self, repo_name: str, username: str, since: str, until: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get pull requests for a specific repository within date range"""
        prs = {"created": [], "merged": [], "reviewed": []}

        # Get PRs created by the user
        for state in ["open", "closed"]:
            page = 1
            while True:
                url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/pulls"
                params = {
                    "state": state,
                    "per_page": 100,
                    "page": page,
                    "sort": "created",
                    "direction": "desc",
                }

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code != 200:
                    break

                repo_prs = response.json()
                if not repo_prs:
                    break

                for pr in repo_prs:
                    pr_created = pendulum.parse(pr["created_at"])
                    pr_merged = (
                        pendulum.parse(pr["merged_at"]) if pr["merged_at"] else None
                    )

                    since_date = pendulum.parse(since)
                    until_date = pendulum.parse(until)

                    # Check if PR was created in date range
                    if (
                        pr["user"]["login"] == username
                        and since_date <= pr_created <= until_date
                    ):
                        prs["created"].append(pr)

                    # Check if PR was merged in date range
                    if (
                        pr_merged
                        and pr["user"]["login"] == username
                        and since_date <= pr_merged <= until_date
                    ):
                        prs["merged"].append(pr)

                page += 1

                # Stop if we've gone beyond our date range
                if repo_prs and pendulum.parse(repo_prs[-1]["created_at"]) < since_date:
                    break

        # Get PRs reviewed by the user
        prs["reviewed"] = self.get_pr_reviews_for_repo(
            repo_name, username, since, until
        )

        return prs

    def get_pr_reviews_for_repo(
        self, repo_name: str, username: str, since: str, until: str
    ) -> List[Dict[str, Any]]:
        """Get PR reviews by the user within date range"""
        reviewed_prs = []

        # Use search API to find PRs reviewed by the user
        query = f"type:pr repo:{self.org_name}/{repo_name} reviewed-by:{username}"
        url = f"{self.base_url}/search/issues"
        params = {"q": query, "sort": "updated", "per_page": 100}

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            search_results = response.json()
            for pr in search_results.get("items", []):
                # Get detailed PR info to check review dates
                pr_url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/pulls/{pr['number']}/reviews"
                reviews_response = requests.get(pr_url, headers=self.headers)

                if reviews_response.status_code == 200:
                    reviews = reviews_response.json()
                    since_date = pendulum.parse(since)
                    until_date = pendulum.parse(until)

                    for review in reviews:
                        if (
                            review["user"]["login"] == username
                            and review["submitted_at"]
                            and since_date
                            <= pendulum.parse(review["submitted_at"])
                            <= until_date
                        ):
                            reviewed_prs.append({"pr": pr, "review": review})
                            break

        return reviewed_prs

    def get_pr_comments_for_repo(
        self, repo_name: str, username: str, since: str, until: str
    ) -> List[Dict[str, Any]]:
        """Get PR comments by the user within date range"""
        comments = []

        # Get all PRs and check for comments
        for state in ["open", "closed"]:
            page = 1
            while True:
                url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/pulls"
                params = {
                    "state": state,
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                }

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code != 200:
                    break

                prs = response.json()
                if not prs:
                    break

                for pr in prs:
                    # Get PR comments
                    comments_url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/issues/{pr['number']}/comments"
                    comments_response = requests.get(comments_url, headers=self.headers)

                    if comments_response.status_code == 200:
                        pr_comments = comments_response.json()
                        since_date = pendulum.parse(since)
                        until_date = pendulum.parse(until)

                        for comment in pr_comments:
                            if (
                                comment["user"]["login"] == username
                                and since_date
                                <= pendulum.parse(comment["created_at"])
                                <= until_date
                            ):
                                comments.append({"pr": pr, "comment": comment})

                page += 1

                # Stop if we've gone beyond our date range
                if prs and pendulum.parse(prs[-1]["updated_at"]) < pendulum.parse(
                    since
                ):
                    break

        return comments

    def get_github_daily_work(
        self,
        username: str,
        target_date_range: pendulum.Interval,
    ) -> str:
        """Generate a comprehensive daily work summary"""
        since = target_date_range.start.to_iso8601_string()
        until = target_date_range.end.to_iso8601_string()

        # Get all organization repositories
        print(f"Fetching repositories from organization: {self.org_name}")
        repositories = self.get_org_repositories()

        if not repositories:
            return (
                "No repositories found in the organization or insufficient permissions."
            )

        daily_work_summary = f"# GitHub Activity Report for {username}\n"
        daily_work_summary += f"**Organization:** {self.org_name}\n"
        daily_work_summary += f"**Period:** {target_date_range.start.format('YYYY-MM-DD')} to {target_date_range.end.format('YYYY-MM-DD')}\n\n"

        total_commits = 0
        total_prs_created = 0
        total_prs_merged = 0
        total_reviews = 0
        total_comments = 0

        for repo in repositories:
            repo_name = repo["name"]
            repo_full_name = repo["full_name"]

            print(f"Processing repository: {repo_name}")

            # Get commits
            commits = self.get_commits_for_repo(repo_name, username, since, until)

            # Get pull requests
            prs = self.get_pull_requests_for_repo(repo_name, username, since, until)

            # Get PR comments
            comments = self.get_pr_comments_for_repo(repo_name, username, since, until)

            # Only include repository in report if there's activity
            if (
                commits
                or prs["created"]
                or prs["merged"]
                or prs["reviewed"]
                or comments
            ):
                daily_work_summary += f"## Repository: {repo_name}\n"

                if commits:
                    daily_work_summary += f"### Commits ({len(commits)})\n"
                    for commit in commits:
                        commit_msg = commit["commit"]["message"].splitlines()[0]
                        commit_sha = commit["sha"][:7]
                        commit_url = f"https://github.com/{repo_full_name}/commit/{commit['sha']}"
                        daily_work_summary += (
                            f"- **{commit_msg}** ([{commit_sha}]({commit_url}))\n"
                        )
                    daily_work_summary += "\n"
                    total_commits += len(commits)

                if prs["created"]:
                    daily_work_summary += (
                        f"### Pull Requests Created ({len(prs['created'])})\n"
                    )
                    for pr in prs["created"]:
                        pr_url = (
                            f"https://github.com/{repo_full_name}/pull/{pr['number']}"
                        )
                        daily_work_summary += (
                            f"- **#{pr['number']}**: {pr['title']} ([Link]({pr_url}))\n"
                        )
                    daily_work_summary += "\n"
                    total_prs_created += len(prs["created"])

                if prs["merged"]:
                    daily_work_summary += (
                        f"### Pull Requests Merged ({len(prs['merged'])})\n"
                    )
                    for pr in prs["merged"]:
                        pr_url = (
                            f"https://github.com/{repo_full_name}/pull/{pr['number']}"
                        )
                        daily_work_summary += (
                            f"- **#{pr['number']}**: {pr['title']} ([Link]({pr_url}))\n"
                        )
                    daily_work_summary += "\n"
                    total_prs_merged += len(prs["merged"])

                if prs["reviewed"]:
                    daily_work_summary += (
                        f"### Pull Requests Reviewed ({len(prs['reviewed'])})\n"
                    )
                    for review_data in prs["reviewed"]:
                        pr = review_data["pr"]
                        review = review_data["review"]
                        pr_url = (
                            f"https://github.com/{repo_full_name}/pull/{pr['number']}"
                        )
                        daily_work_summary += f"- **#{pr['number']}**: {pr['title']} - {review['state'].capitalize()} ([Link]({pr_url}))\n"
                    daily_work_summary += "\n"
                    total_reviews += len(prs["reviewed"])

                if comments:
                    daily_work_summary += f"### PR Comments ({len(comments)})\n"
                    for comment_data in comments:
                        pr = comment_data["pr"]
                        comment = comment_data["comment"]
                        pr_url = (
                            f"https://github.com/{repo_full_name}/pull/{pr['number']}"
                        )
                        comment_preview = (
                            comment["body"][:100] + "..."
                            if len(comment["body"]) > 100
                            else comment["body"]
                        )
                        daily_work_summary += f"- **#{pr['number']}**: {comment_preview} ([Link]({pr_url}))\n"
                    daily_work_summary += "\n"
                    total_comments += len(comments)

        # Add summary
        daily_work_summary += "## Summary\n"
        daily_work_summary += f"- **Total Commits**: {total_commits}\n"
        daily_work_summary += f"- **Total PRs Created**: {total_prs_created}\n"
        daily_work_summary += f"- **Total PRs Merged**: {total_prs_merged}\n"
        daily_work_summary += f"- **Total Reviews**: {total_reviews}\n"
        daily_work_summary += f"- **Total Comments**: {total_comments}\n"

        if (
            total_commits == 0
            and total_prs_created == 0
            and total_prs_merged == 0
            and total_reviews == 0
            and total_comments == 0
        ):
            return f"No GitHub activity found for {username} in {self.org_name} during the specified period."

        return daily_work_summary


def main():
    # Load environment variables
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "mcklmo")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    ORG_NAME = os.getenv("GITHUB_ORG", "BC-Technology")

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it with your GitHub Personal Access Token.")
        print("Required scopes: repo, read:org, read:user")
        exit(1)

    # Initialize the tracker
    tracker = GitHubActivityTracker(GITHUB_TOKEN, ORG_NAME)

    # Example usage for a specific day
    today = pendulum.now()
    yesterday = today.subtract(days=1)

    # Create a period for the last day
    period = pendulum.interval(yesterday, today)

    print(f"Generating GitHub activity report for {GITHUB_USERNAME} in {ORG_NAME}")
    print(
        f"Period: {period.start.format('YYYY-MM-DD')} to {period.end.format('YYYY-MM-DD')}"
    )

    report = tracker.get_github_daily_work(GITHUB_USERNAME, period)
    print("\n" + "=" * 80)
    print(report)

    # Save report to file
    filename = f"github_report_{period.start.format('YYYY-MM-DD')}_to_{period.end.format('YYYY-MM-DD')}.md"
    with open(filename, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    main()
