# GitHub Daily Work Recorder

An automated tool to generate comprehensive daily summaries of your GitHub work within organization repositories, including commits, pull requests, reviews, and comments.

## Features

- **Comprehensive Activity Tracking**: Captures commits, PRs (created/merged), reviews, and comments
- **Organization Repository Support**: Works with private repositories within your organization
- **Date Range Filtering**: Generate reports for specific dates or date ranges
- **Markdown Output**: Professional formatted reports suitable for client billing
- **Detailed Summaries**: Includes links to commits, PRs, and activity counts

## Requirements

- Python 3.7+
- GitHub Personal Access Token with appropriate permissions
- Access to organization repositories

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Create a GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Set the following scopes:
   - `repo` - Full control of private repositories
   - `read:org` - Read org and team membership, read org projects
   - `read:user` - Read user profile data

### 2. Set Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_ORG=your_organization_name
```

**Example:**

```bash
GITHUB_USERNAME=mcklmo
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_ORG=BC-Technology
```

## Usage

### Basic Usage

Run the script to generate a report for the last day:

```bash
python record.py
```

### Programmatic Usage

```python
from record import GitHubActivityTracker
import pendulum
import os

# Initialize tracker
tracker = GitHubActivityTracker(
    github_token=os.getenv("GITHUB_TOKEN"),
    org_name="your-org-name"
)

# Create date range (last 7 days)
end_date = pendulum.now()
start_date = end_date.subtract(days=7)
period = start_date.date().period(end_date.date())

# Generate report
report = tracker.get_github_daily_work("your-username", period)
print(report)
```

### Custom Date Ranges

```python
import pendulum

# Specific date
date = pendulum.parse("2024-01-15")
period = date.date().period(date.date())

# Date range
start = pendulum.parse("2024-01-01")
end = pendulum.parse("2024-01-31")
period = start.date().period(end.date())

# Last week
today = pendulum.now()
last_week = today.subtract(weeks=1)
period = last_week.date().period(today.date())
```

## Output Format

The tool generates a comprehensive Markdown report including:

- **Repository-level breakdown** of all activities
- **Commits** with messages, SHA, and links
- **Pull Requests** (created, merged, reviewed)
- **Comments** on PRs with previews
- **Summary statistics** for the reporting period

### Sample Output

```markdown
# GitHub Activity Report for username

**Organization:** BC-Technology
**Period:** 2024-01-15 to 2024-01-16

## Repository: project-name

### Commits (3)

- **Fix authentication bug** ([abc1234](https://github.com/org/repo/commit/abc1234))
- **Add user validation** ([def5678](https://github.com/org/repo/commit/def5678))

### Pull Requests Created (1)

- **#123**: Implement new feature ([Link](https://github.com/org/repo/pull/123))

## Summary

- **Total Commits**: 3
- **Total PRs Created**: 1
- **Total PRs Merged**: 0
- **Total Reviews**: 2
- **Total Comments**: 4
```

## API Endpoints Used

This tool uses the following GitHub REST API endpoints:

- `/orgs/{org}/repos` - List organization repositories
- `/repos/{owner}/{repo}/commits` - Get commits by author and date
- `/repos/{owner}/{repo}/pulls` - Get pull requests
- `/search/issues` - Search for reviewed PRs
- `/repos/{owner}/{repo}/pulls/{number}/reviews` - Get PR reviews
- `/repos/{owner}/{repo}/issues/{number}/comments` - Get PR comments

## Troubleshooting

### Common Issues

1. **"No repositories found"**

   - Ensure your token has `read:org` scope
   - Verify you're a member of the organization
   - Check the organization name is correct

2. **"Error fetching commits"**

   - Ensure your token has `repo` scope
   - Verify the repository exists and you have access
   - Check if the repository is empty

3. **Rate limiting**
   - The tool includes pagination to handle large datasets
   - GitHub API has rate limits (5000 requests/hour for authenticated users)
   - The tool will fail gracefully if limits are exceeded

### Required Permissions

Your GitHub token must have access to:

- Private repositories in the organization
- Organization membership information
- User profile data

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables for sensitive data
- Consider using GitHub Apps for production deployments
- Regularly rotate your Personal Access Tokens

## License

This project is provided as-is for personal and professional use.
