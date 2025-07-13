import subprocess
import os
import argparse
import pendulum
from typing import Any, Optional, List, Tuple
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


logger = logging.getLogger(__name__)

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def print(message: str):
    logger.info(message)


class Commit:
    def __init__(
        self,
        commit_date: pendulum.DateTime,
        commit_msg: str,
        commit_hash: str,
    ):
        self.commit_date = commit_date
        self.commit_msg = commit_msg
        self.commit_hash = commit_hash

    def __str__(self):
        return f"`{self.commit_date.to_datetime_string()}` ({self.commit_hash}) **{self.commit_msg}**"


class GitActivityTracker:
    def __init__(self, repo_path: Optional[str] = None, debug: bool = False):
        self.debug = debug
        self.repo_path = self._find_git_repo(repo_path)

    def debug_log(self, message: str, data: Any = None):
        """Print debug information if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}")
            if data is not None:
                if isinstance(data, (dict, list)):
                    print(f"[DEBUG] Data: {json.dumps(data, indent=2, default=str)}")
                else:
                    print(f"[DEBUG] Data: {data}")

    def _find_git_repo(self, repo_path: Optional[str] = None) -> Optional[str]:
        """Find the git repository root by looking for .git folder"""
        if repo_path:
            # Use provided path
            repo_path = os.path.abspath(os.path.expanduser(repo_path))
            if os.path.isdir(repo_path):
                # Check if the provided path contains .git
                if os.path.isdir(os.path.join(repo_path, ".git")):
                    return repo_path

                # Search parent directories
                current_dir = repo_path
                while current_dir != os.path.dirname(current_dir):  # Not at root
                    if os.path.isdir(os.path.join(current_dir, ".git")):
                        return current_dir
                    current_dir = os.path.dirname(current_dir)
            return None
        else:
            # Use current directory logic
            current_dir = os.getcwd()
            while current_dir != os.path.dirname(current_dir):  # Not at root
                if os.path.isdir(os.path.join(current_dir, ".git")):
                    return current_dir
                current_dir = os.path.dirname(current_dir)

            # Check if current directory has .git
            if os.path.isdir(os.path.join(os.getcwd(), ".git")):
                return os.getcwd()

            return None

    def find_git_repos_in_directory(
        self, root_path: str, max_depth: int = 1
    ) -> List[str]:
        """Find all git repositories in a directory with max depth traversal"""
        git_repos = []
        root_path = os.path.abspath(os.path.expanduser(root_path))

        if not os.path.isdir(root_path):
            self.debug_log(f"Root path is not a directory: {root_path}")
            return git_repos

        # Check if the root path itself is a git repository
        if os.path.isdir(os.path.join(root_path, ".git")):
            git_repos.append(root_path)
            self.debug_log(f"Found git repository at root: {root_path}")

        # Traverse subdirectories up to max_depth
        if max_depth > 0:
            try:
                for item in os.listdir(root_path):
                    item_path = os.path.join(root_path, item)

                    # Skip if not a directory
                    if not os.path.isdir(item_path):
                        continue

                    # Skip hidden directories (except .git which we already checked)
                    if item.startswith(".") and item != ".git":
                        continue

                    # Check if this subdirectory is a git repository
                    if os.path.isdir(os.path.join(item_path, ".git")):
                        git_repos.append(item_path)
                        self.debug_log(f"Found git repository: {item_path}")

                    # Recurse into subdirectories if we haven't reached max depth
                    elif max_depth > 1:
                        sub_repos = self.find_git_repos_in_directory(
                            item_path, max_depth - 1
                        )
                        git_repos.extend(sub_repos)

            except PermissionError as e:
                self.debug_log(
                    f"Permission denied accessing directory: {root_path} - {e}"
                )
            except Exception as e:
                self.debug_log(f"Error traversing directory: {root_path} - {e}")

        return git_repos

    def _run_git_command(self, args: List[str]) -> str:
        """Run a git command and return the output"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.debug_log(f"Git command failed: {e}")
            self.debug_log(f"Command: git {' '.join(args)}")
            self.debug_log(f"Error output: {e.stderr}")
            return ""

    def get_repo_name(self) -> str:
        """Get the repository name from git remote or directory name"""
        try:
            # Try to get from remote URL
            remote_url = self._run_git_command(["remote", "get-url", "origin"])
            if remote_url:
                # Extract repo name from URL
                if remote_url.endswith(".git"):
                    remote_url = remote_url[:-4]
                repo_name = remote_url.split("/")[-1]
                return repo_name
        except:
            pass

        # Fallback to directory name
        return os.path.basename(self.repo_path)

    def get_all_branches(self) -> List[str]:
        """Get all branches in the repository"""
        try:
            # Get all branches (local and remote)
            output = self._run_git_command(["branch", "-a"])
            branches = []

            for line in output.split("\n"):
                line = line.strip()
                if line and not line.startswith("*"):
                    # Clean up branch names
                    branch = line.replace("remotes/origin/", "").replace("remotes/", "")
                    if branch not in branches and branch != "HEAD":
                        branches.append(branch)
                elif line.startswith("*"):
                    # Current branch
                    branch = line[1:].strip()
                    if branch not in branches:
                        branches.append(branch)

            # Remove duplicates and sort
            branches = list(set(branches))
            self.debug_log(f"Found branches: {branches}")
            return branches
        except:
            self.debug_log("Failed to get branches, using current branch only")
            return ["HEAD"]

    def get_commits_for_repo(
        self,
        username: str,
        since: str,
        until: str,
        branches: Optional[List[str]] = None,
    ) -> List[Commit]:
        """Get all commits for the repository within date range, filtered by author"""

        if not branches:
            branches = self.get_all_branches()

        all_commits = {}

        # Git log format: hash|author_name|author_email|date|subject
        log_format = "--pretty=format:%H|%an|%ae|%ai|%s"

        for branch in branches:
            try:
                self.debug_log(f"Getting commits for branch: {branch}")

                # Build git log command
                cmd = [
                    "log",
                    log_format,
                    f"--since={since}",
                    f"--until={until}",
                    "--all" if branch == "HEAD" else branch,
                ]

                output = self._run_git_command(cmd)

                if not output:
                    self.debug_log(f"No commits found for branch {branch}")
                    continue

                for line in output.split("\n"):
                    if not line.strip():
                        continue

                    parts = line.split("|", 4)
                    if len(parts) != 5:
                        continue

                    commit_hash, author_name, author_email, date_str, subject = parts

                    # Skip if we've already seen this commit
                    if commit_hash in all_commits:
                        continue

                    all_commits[commit_hash] = {
                        "hash": commit_hash,
                        "author_name": author_name,
                        "author_email": author_email,
                        "date": date_str,
                        "subject": subject,
                    }

            except Exception as e:
                self.debug_log(f"Error getting commits for branch {branch}: {e}")
                continue

        self.debug_log(f"Total unique commits found: {len(all_commits)}")

        # Filter by author
        filtered_commits = []
        username_lower = username.lower()

        for commit_data in all_commits.values():
            author_name = commit_data["author_name"].lower()
            author_email = commit_data["author_email"].lower()

            # Check if this commit is by the target user
            is_match = False
            if username_lower in author_name or author_name == username_lower:
                is_match = True
            elif username_lower in author_email or author_email.startswith(
                username_lower
            ):
                is_match = True

            if is_match:
                commit_date = pendulum.from_format(
                    commit_data["date"],
                    "YYYY-MM-DD HH:mm:ss Z",  # '2025-07-09 10:57:06 +0200'
                )
                commit = Commit(
                    commit_date=commit_date,
                    commit_msg=commit_data["subject"],
                    commit_hash=commit_data["hash"],
                )
                filtered_commits.append(commit)

        self.debug_log(f"Commits after filtering by author: {len(filtered_commits)}")

        # Sort by date (newest first)
        return sorted(filtered_commits, key=lambda x: x.commit_date, reverse=True)

    def get_git_daily_work(
        self,
        username: str,
        target_date_range: pendulum.Interval,
    ) -> str:
        """Generate a daily work report from git commits"""

        since = target_date_range.start.format("YYYY-MM-DD")
        until = target_date_range.end.format("YYYY-MM-DD")

        self.debug_log(f"Starting get_git_daily_work for user: {username}")
        self.debug_log(
            f"Date range: {target_date_range.start} to {target_date_range.end}"
        )
        self.debug_log(f"Repository path: {self.repo_path}")

        repo_name = self.get_repo_name()
        print(f"Processing repository: {repo_name}")

        commits = self.get_commits_for_repo(username, since, until)

        if not commits:
            return f"No git activity found for {username} in {repo_name} during the specified period."

        # Generate report
        daily_work_summary = f"# Git Activity Report for {username}\n\n"
        daily_work_summary += f"**Repository:** {repo_name}\n"
        daily_work_summary += f"**Period:** {target_date_range.start.format('YYYY-MM-DD')} to {target_date_range.end.format('YYYY-MM-DD')}\n"
        daily_work_summary += f"**Repository Path:** {self.repo_path}\n\n"

        daily_work_summary += f"## Commits ({len(commits)})\n\n"

        for commit in commits:
            daily_work_summary += str(commit)

        daily_work_summary += "\n## Summary\n\n"
        daily_work_summary += f"- **Total Commits**: {len(commits)}\n"

        # Group commits by day
        commits_by_day = {}
        for commit in commits:
            day = commit.commit_date.format("YYYY-MM-DD")
            if day not in commits_by_day:
                commits_by_day[day] = 0
            commits_by_day[day] += 1

        if commits_by_day:
            daily_work_summary += f"- **Days with commits**: {len(commits_by_day)}\n"
            daily_work_summary += f"- **Average commits per day**: {len(commits) / len(commits_by_day):.1f}\n"

            daily_work_summary += "\n### Daily Breakdown\n\n"
            for day in sorted(commits_by_day.keys(), reverse=True):
                daily_work_summary += f"- **{day}**: {commits_by_day[day]} commits\n"

        return daily_work_summary

    def _process_single_repo(
        self, repo_path: str, username: str, since: str, until: str
    ) -> Tuple[str, str, List[Commit], Optional[str]]:
        """Process a single repository and return results for thread-safe processing"""
        try:
            # Create a tracker for this repository
            temp_tracker = GitActivityTracker(repo_path=repo_path, debug=self.debug)

            repo_name = temp_tracker.get_repo_name()
            commits = temp_tracker.get_commits_for_repo(username, since, until)

            return repo_path, repo_name, commits, None

        except Exception as e:
            self.debug_log(f"Error processing repository {repo_path}: {e}")
            return repo_path, os.path.basename(repo_path), [], str(e)

    def get_multiple_repos_daily_work(
        self,
        repo_paths: List[str],
        username: str,
        target_date_range: pendulum.Interval,
    ) -> str:
        """Generate a combined daily work report from multiple git repositories"""

        since = target_date_range.start.format("YYYY-MM-DD")
        until = target_date_range.end.format("YYYY-MM-DD")

        self.debug_log(f"Starting get_multiple_repos_daily_work for user: {username}")
        self.debug_log(
            f"Date range: {target_date_range.start} to {target_date_range.end}"
        )
        self.debug_log(f"Repository paths: {repo_paths}")

        # Generate combined report
        combined_report = f"# Git Activity Report for {username}\n\n"
        combined_report += f"**Period:** {target_date_range.start.format('YYYY-MM-DD')} to {target_date_range.end.format('YYYY-MM-DD')}\n"
        combined_report += f"**Repositories:** {len(repo_paths)} repositories\n\n"

        total_commits = 0
        all_commits_by_day = {}
        repo_summaries = []

        # Process repositories concurrently using ThreadPoolExecutor
        max_workers = min(len(repo_paths), 10)  # Limit to 10 concurrent workers

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all repository processing tasks
            future_to_repo = {
                executor.submit(
                    self._process_single_repo,
                    repo_path,
                    username,
                    since,
                    until,
                ): repo_path
                for repo_path in repo_paths
            }

            all_commits = []

            for future in as_completed(future_to_repo):
                repo_path = future_to_repo[future]
                print(f"Processing repository: {os.path.basename(repo_path)}")

                repo_path_result, repo_name, commits, error = future.result()

                if error:
                    self.debug_log(f"Error processing repository {repo_path}: {error}")
                    repo_summaries.append(
                        f"- **{repo_name}**: Error processing repository"
                    )
                else:
                    if not commits:
                        continue

                    total_commits += len(commits)

                    # Aggregate commits by day
                    for commit in commits:
                        day = commit.commit_date.format("YYYY-MM-DD")
                        if day not in all_commits_by_day:
                            all_commits_by_day[day] = 0

                        all_commits_by_day[day] += 1

                        all_commits.append((day, repo_name, str(commit)))

                    repo_summaries.append(f"- **{repo_name}**: {len(commits)} commits")

        # Add summary section
        combined_report += "## Summary\n\n"
        combined_report += f"- **Total Commits**: {total_commits}\n"
        combined_report += f"- **Total Repositories**: {len(repo_paths)}\n\n"

        all_commits = sorted(all_commits, key=lambda x: x[2], reverse=True)

        structured_commits: dict[str, list[tuple[str, str]]] = {}

        for day, commit_repo_name, commit in all_commits:
            if day not in structured_commits:
                structured_commits[day] = []

            structured_commits[day].append((commit_repo_name, commit))

        report_by_day = {}

        for day, repo_commits in structured_commits.items():
            day_report = self.create_day_report(day, repo_commits)

            filename = f"git_report_multi_{day}.md"
            with open(filename, "w") as f:
                f.write(day_report)

            report_by_day[day] = day_report

        if all_commits_by_day:
            combined_report += f"- **Days with commits**: {len(all_commits_by_day)}\n"
            combined_report += f"- **Average commits per day**: {total_commits / len(all_commits_by_day):.1f}\n"

        combined_report += "\n### Repository Breakdown\n\n"
        for summary in repo_summaries:
            combined_report += summary + "\n"

        if all_commits_by_day:
            combined_report += "\n### Daily Breakdown\n\n"
            for day in sorted(all_commits_by_day.keys(), reverse=True):
                combined_report += f"- **{day}**: {all_commits_by_day[day]} commits\n"

        if total_commits == 0:
            return f"No git activity found for {username} in any repositories during the specified period."

        filename = f"git_report_multi_{target_date_range.start.format('YYYY-MM-DD')}_to_{target_date_range.end.format('YYYY-MM-DD')}.md"
        with open(filename, "w") as f:
            f.write(combined_report)

        return report_by_day

    def create_day_report(self, day: str, repo_commits: List[Tuple[str, str]]) -> str:
        day_report = f"# Git history for {day}\n\n"
        for repo_name, commit in repo_commits:
            repo_name_fmt = repo_name.ljust(45)
            day_report += f"* {repo_name_fmt}: {commit}\n"

        return day_report
