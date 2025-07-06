import requests
import datetime
import os
from dotenv import load_dotenv
import pendulum
from typing import Dict, List, Any, Optional
import json

load_dotenv()


class GitHubActivityTracker:
    def __init__(self, github_token: str, org_name: str, debug: bool = False):
        self.github_token = github_token
        self.org_name = org_name
        self.debug = debug
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def debug_log(self, message: str, data: Any = None):
        """Print debug information if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}")
            if data is not None:
                if isinstance(data, (dict, list)):
                    print(f"[DEBUG] Data: {json.dumps(data, indent=2, default=str)}")
                else:
                    print(f"[DEBUG] Data: {data}")

    def get_org_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories from the organization"""
        repositories = []
        page = 1

        self.debug_log(f"Fetching repositories from organization: {self.org_name}")

        while True:
            url = f"{self.base_url}/orgs/{self.org_name}/repos?per_page=100&page={page}&type=all"
            self.debug_log(f"API Request: {url}")

            response = requests.get(url, headers=self.headers)
            self.debug_log(f"Response status: {response.status_code}")

            if response.status_code != 200:
                self.debug_log(f"Error response: {response.text}")
                print(
                    f"Error fetching repositories: {response.status_code} - {response.text}"
                )
                break

            repos = response.json()
            self.debug_log(f"Found {len(repos)} repositories on page {page}")

            if not repos:
                break

            repositories.extend(repos)
            page += 1

        self.debug_log(f"Total repositories found: {len(repositories)}")
        return repositories

    def debug_recent_commits(
        self, repo_name: str, since: str, until: str, limit: int = 5
    ):
        """Debug method to check recent commits in repository without author filtering"""
        if not self.debug:
            return

        self.debug_log(
            f"Checking recent commits in {repo_name} (without author filter)"
        )

        url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits"
        params = {
            "since": since,
            "until": until,
            "per_page": limit,
            "page": 1,
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            commits = response.json()
            self.debug_log(
                f"Found {len(commits)} recent commits in {repo_name} (any author)"
            )

            for i, commit in enumerate(commits):
                commit_info = {
                    "sha": commit.get("sha", "")[:7],
                    "message": commit.get("commit", {}).get("message", "")[:50],
                    "author_name": commit.get("commit", {})
                    .get("author", {})
                    .get("name", ""),
                    "author_email": commit.get("commit", {})
                    .get("author", {})
                    .get("email", ""),
                    "committer_name": commit.get("commit", {})
                    .get("committer", {})
                    .get("name", ""),
                    "committer_email": commit.get("commit", {})
                    .get("committer", {})
                    .get("email", ""),
                    "github_author": (
                        commit.get("author", {}).get("login", "")
                        if commit.get("author")
                        else ""
                    ),
                    "github_committer": (
                        commit.get("committer", {}).get("login", "")
                        if commit.get("committer")
                        else ""
                    ),
                    "date": commit.get("commit", {}).get("author", {}).get("date", ""),
                }
                self.debug_log(f"  Recent commit {i+1}: {commit_info}")
        else:
            self.debug_log(
                f"Error fetching recent commits: {response.status_code} - {response.text}"
            )

    def get_commits_for_repo(
        self, repo_name: str, username: str, since: str, until: str
    ) -> List[Dict[str, Any]]:
        """Get commits for a specific repository within date range"""
        all_commits = []
        filtered_commits = []
        page = 1

        self.debug_log(f"Fetching commits for repository: {repo_name}")
        self.debug_log(f"Date range: {since} to {until}")
        self.debug_log(f"Target user: {username}")

        # First, check what commits exist in the repository (for debugging)
        self.debug_recent_commits(repo_name, since, until)

        # Fetch all commits in date range (without author filtering)
        while True:
            url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits"
            params = {
                "since": since,
                "until": until,
                "per_page": 100,
                "page": page,
            }
            # Removed 'author' parameter to get all commits

            self.debug_log(f"API Request: {url}")
            self.debug_log(f"Params: {params}")

            response = requests.get(url, headers=self.headers, params=params)
            self.debug_log(f"Response status: {response.status_code}")

            if response.status_code != 200:
                if response.status_code == 409:  # Repository is empty
                    self.debug_log("Repository is empty")
                    break
                self.debug_log(f"Error response: {response.text}")
                print(
                    f"Error fetching commits for {repo_name}: {response.status_code} - {response.text}"
                )
                break

            repo_commits = response.json()
            self.debug_log(f"Found {len(repo_commits)} commits on page {page}")

            if not repo_commits:
                break

            all_commits.extend(repo_commits)
            page += 1

        # Now filter commits locally by matching various author identifiers
        self.debug_log(f"Total commits fetched: {len(all_commits)}")
        self.debug_log(f"Filtering commits locally for user: {username}")

        for commit in all_commits:
            commit_data = commit.get("commit", {})
            author_info = commit_data.get("author", {})
            committer_info = commit_data.get("committer", {})

            # Get various identifiers
            author_name = author_info.get("name", "").lower()
            author_email = author_info.get("email", "").lower()
            committer_name = committer_info.get("name", "").lower()
            committer_email = committer_info.get("email", "").lower()

            # GitHub user info (if available)
            github_author = (
                commit.get("author", {}).get("login", "").lower()
                if commit.get("author")
                else ""
            )
            github_committer = (
                commit.get("committer", {}).get("login", "").lower()
                if commit.get("committer")
                else ""
            )

            # Flexible matching criteria
            username_lower = username.lower()
            is_match = False
            match_reason = ""

            # Match by GitHub username
            if github_author == username_lower or github_committer == username_lower:
                is_match = True
                match_reason = f"GitHub username ({github_author or github_committer})"

            # Match by commit author/committer name
            elif author_name == username_lower or committer_name == username_lower:
                is_match = True
                match_reason = f"Git name ({author_name or committer_name})"

            # Match by email patterns (flexible matching for common variations)
            elif (
                username_lower in author_email
                or username_lower in committer_email
                or author_email.startswith(username_lower)
                or committer_email.startswith(username_lower)
            ):
                is_match = True
                match_reason = f"Email pattern ({author_email or committer_email})"

            if is_match:
                filtered_commits.append(commit)
                self.debug_log(
                    f"Matched commit {commit.get('sha', '')[:7]}: {match_reason}"
                )
            else:
                self.debug_log(
                    f"Skipped commit {commit.get('sha', '')[:7]}: author='{author_name}', email='{author_email}', github='{github_author}'"
                )

        self.debug_log(
            f"Total commits found for {repo_name} after filtering: {len(filtered_commits)}"
        )
        return filtered_commits

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
        repository_filter: Optional[List[str]] = None,
    ) -> str:
        """Generate a comprehensive daily work summary

        Args:
            username: GitHub username to track
            target_date_range: Date range for the report
            repository_filter: Optional list of repository names to filter for (e.g., ["heads-backend", "heads-frontend"])
        """
        since = target_date_range.start.to_iso8601_string()
        until = target_date_range.end.to_iso8601_string()

        self.debug_log(f"Starting get_github_daily_work for user: {username}")
        self.debug_log(
            f"Date range: {target_date_range.start} to {target_date_range.end}"
        )
        self.debug_log(f"Since (ISO): {since}")
        self.debug_log(f"Until (ISO): {until}")
        self.debug_log(f"Repository filter: {repository_filter}")

        # Get all organization repositories
        print(f"Fetching repositories from organization: {self.org_name}")
        all_repositories = self.get_org_repositories()

        if not all_repositories:
            return (
                "No repositories found in the organization or insufficient permissions."
            )

        # Filter repositories if filter is provided
        if repository_filter:
            repositories = [
                repo for repo in all_repositories if repo["name"] in repository_filter
            ]
            print(f"Filtering for repositories: {repository_filter}")
            print(
                f"Found {len(repositories)} out of {len(all_repositories)} repositories"
            )

            self.debug_log(f"Filtered repositories found:")
            for repo in repositories:
                self.debug_log(f"  - {repo['name']} (full_name: {repo['full_name']})")

            # Check if any filtered repositories were not found
            found_repo_names = [repo["name"] for repo in repositories]
            missing_repos = [
                name for name in repository_filter if name not in found_repo_names
            ]
            if missing_repos:
                print(
                    f"Warning: The following repositories were not found: {missing_repos}"
                )
                self.debug_log(f"Missing repositories: {missing_repos}")
        else:
            repositories = all_repositories
            print(f"Processing all {len(repositories)} repositories")

        if not repositories:
            if repository_filter:
                return f"No repositories found matching the filter: {repository_filter}"
            else:
                return "No repositories found in the organization."

        daily_work_summary = f"# GitHub Activity Report for {username}\n"
        daily_work_summary += f"**Organization:** {self.org_name}\n"
        daily_work_summary += f"**Period:** {target_date_range.start.format('YYYY-MM-DD')} to {target_date_range.end.format('YYYY-MM-DD')}\n"

        if repository_filter:
            daily_work_summary += f"**Repositories:** {', '.join(repository_filter)}\n"

        daily_work_summary += "\n"

        total_commits = 0
        total_prs_created = 0
        total_prs_merged = 0
        total_reviews = 0
        total_comments = 0

        for repo in repositories:
            repo_name = repo["name"]
            repo_full_name = repo["full_name"]

            print(f"Processing repository: {repo_name}")
            self.debug_log(
                f"Processing repository: {repo_name} (full_name: {repo_full_name})"
            )

            # Get commits
            commits = self.get_commits_for_repo(repo_name, username, since, until)

            # Get pull requests
            prs = self.get_pull_requests_for_repo(repo_name, username, since, until)

            # Get PR comments
            comments = self.get_pr_comments_for_repo(repo_name, username, since, until)

            self.debug_log(f"Repository {repo_name} results:")
            self.debug_log(f"  - Commits: {len(commits)}")
            self.debug_log(f"  - PRs created: {len(prs['created'])}")
            self.debug_log(f"  - PRs merged: {len(prs['merged'])}")
            self.debug_log(f"  - PRs reviewed: {len(prs['reviewed'])}")
            self.debug_log(f"  - Comments: {len(comments)}")

            # Only include repository in report if there's activity
            if (
                commits
                or prs["created"]
                or prs["merged"]
                or prs["reviewed"]
                or comments
            ):
                daily_work_summary += f"## Repository: {repo_name}\n\n"

                if commits:
                    daily_work_summary += f"### Commits ({len(commits)})\n\n"
                    for commit in commits:
                        commit_msg = commit["commit"]["message"].splitlines()[0]
                        commit_sha = commit["sha"][:7]
                        commit_url = f"https://github.com/{repo_full_name}/commit/{commit['sha']}"
                        commit_date = (
                            commit["commit"]["author"]["date"]
                            or commit["commit"]["committer"]["date"]
                        )
                        daily_work_summary += f"- {commit_date} **{commit_msg}** ([{commit_sha}]({commit_url}))\n"
                    daily_work_summary += "\n"
                    total_commits += len(commits)

                if prs["created"]:
                    daily_work_summary += (
                        f"### Pull Requests Created ({len(prs['created'])})\n\n"
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
                        f"### Pull Requests Merged ({len(prs['merged'])})\n\n"
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
                        f"### Pull Requests Reviewed ({len(prs['reviewed'])})\n\n"
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
                    daily_work_summary += f"### PR Comments ({len(comments)})\n\n"
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
        daily_work_summary += "## Summary\n\n"
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
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    # Repository filter - can be set via environment variable or hardcoded
    REPO_FILTER = os.getenv("GITHUB_REPO_FILTER")  # Comma-separated list
    if REPO_FILTER:
        repository_filter = [repo.strip() for repo in REPO_FILTER.split(",")]
    else:
        # Set to None to process all repositories, or specify a list to filter
        # Example: repository_filter = ["heads-backend", "heads-frontend"]
        repository_filter = [
            "heads-backend",
            # "heads-frontend",
        ]  # Default filter for testing

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it with your GitHub Personal Access Token.")
        print("Required scopes: repo, read:org, read:user")
        exit(1)

    # Initialize the tracker with debug mode
    tracker = GitHubActivityTracker(GITHUB_TOKEN, ORG_NAME, debug=False)

    today = pendulum.now()
    week_ago = today.start_of("year")
    period = pendulum.interval(week_ago, today)

    # Debug information
    print(f"[DEBUG] Today: {today}")
    print(f"[DEBUG] Week ago: {week_ago}")
    print(f"[DEBUG] Period start: {period.start}")
    print(f"[DEBUG] Period end: {period.end}")
    print(f"[DEBUG] Period duration: {period.in_words()}")

    print(f"Generating GitHub activity report for {GITHUB_USERNAME} in {ORG_NAME}")
    print(
        f"Period: {period.start.format('YYYY-MM-DD HH:mm:ss')} to {period.end.format('YYYY-MM-DD HH:mm:ss')}"
    )

    if repository_filter:
        print(f"Repository filter: {repository_filter}")
    else:
        print("Processing all repositories in the organization")

    report = tracker.get_github_daily_work(GITHUB_USERNAME, period, repository_filter)
    print("\n" + "=" * 80)
    print(report)

    # Save report to file
    filter_suffix = "_filtered" if repository_filter else ""
    filename = f"github_report_{period.start.format('YYYY-MM-DD')}_to_{period.end.format('YYYY-MM-DD')}{filter_suffix}.md"
    with open(filename, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    main()
