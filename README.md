# Daily Work Recorder

A Python tool for tracking and reporting daily work activities from git repositories. This project provides two implementations:

1. **GitHub API Version** (`record.py`) - Fetches data from GitHub API across multiple repositories in an organization
2. **Git CLI Version** (`record_git_cli.py`) - Uses local git commands to analyze the current repository

## Features

### GitHub API Version (`record.py`)

- Fetches commits across multiple repositories in a GitHub organization
- Supports filtering by specific repositories
- Tracks commits, pull requests, and reviews
- Requires GitHub API token
- Works with remote repositories without local clones

### Git CLI Version (`record_git_cli.py`)

- Analyzes commits in the current local git repository
- Works with any git repository (GitHub, GitLab, Bitbucket, etc.)
- No API tokens required
- Faster for single repository analysis
- Works offline with local git history

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd daily-work-recorder
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
GITHUB_USERNAME=your-username
DEBUG=false

# For GitHub API version only:
GITHUB_TOKEN=your-github-token
GITHUB_ORG=your-organization
GITHUB_REPO_FILTER=repo1,repo2  # Optional: comma-separated list
```

## Usage

### Git CLI Version (Recommended for single repository)

The Git CLI version is simpler and works with any git repository:

```bash
# Run from within any git repository
python record_git_cli.py

# Or specify a different repository path
python record_git_cli.py --repo-path /path/to/your/repo

# With custom date range and username
python record_git_cli.py --repo-path ~/Projects/my-app --username johndoe --start-date 2025-01-01 --end-date 2025-01-15

# Show all available options
python record_git_cli.py --help
```

**Command Line Options:**

- `--repo-path` / `-r`: Path to the git repository (default: current directory)
- `--username` / `-u`: Git username to filter by (default: from GITHUB_USERNAME env var)
- `--start-date` / `-s`: Start date for the report (YYYY-MM-DD format)
- `--end-date` / `-e`: End date for the report (YYYY-MM-DD format)
- `--debug` / `-d`: Enable debug mode

Or use the example script:

```bash
python example_usage_git_cli.py
```

**Key Features:**

- Works with any git repository on your machine
- Automatically detects git repository in current directory or parent directories
- Analyzes all branches for commits
- Generates detailed reports with daily breakdowns
- No external API dependencies

### GitHub API Version (For multiple repositories)

For analyzing multiple repositories in a GitHub organization:

```bash
python record.py
```

Or use the example script:

```bash
python example_usage.py
```

**Requirements:**

- GitHub Personal Access Token with appropriate permissions
- Access to the GitHub organization
- Internet connection

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Common settings
GITHUB_USERNAME=your-username
DEBUG=false

# Git CLI version only
REPO_PATH=/path/to/your/repo  # Optional: repository path

# GitHub API version only
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_ORG=your-organization-name
GITHUB_REPO_FILTER=repo1,repo2,repo3  # Optional: specific repositories
```

### GitHub Token Setup (API version only)

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with these scopes:
   - `repo` - Full control of private repositories
   - `read:org` - Read organization membership
   - `read:user` - Read user profile data

## Output

Both versions generate markdown reports with:

- **Summary statistics** (total commits, active days, etc.)
- **Detailed commit list** with timestamps, messages, and links
- **Daily breakdown** showing commits per day
- **Repository information** and date ranges

Example output:

```markdown
# Git Activity Report for username

**Repository:** my-project
**Period:** 2025-01-01 to 2025-01-15
**Repository Path:** /path/to/repo

## Commits (42)

- `2025-01-15 10:30:00` **Add new feature** (abc1234) by John Doe
- `2025-01-14 16:45:00` **Fix bug in authentication** (def5678) by John Doe
...

## Summary

- **Total Commits**: 42
- **Days with commits**: 8
- **Average commits per day**: 5.3

### Daily Breakdown

- **2025-01-15**: 3 commits
- **2025-01-14**: 7 commits
...
```

## Comparison: Git CLI vs GitHub API

| Feature | Git CLI | GitHub API |
|---------|---------|------------|
| **Setup** | Simple | Requires API token |
| **Speed** | Fast | Slower (API calls) |
| **Repositories** | Single (via path) | Multiple |
| **Offline** | Yes | No |
| **Git Providers** | Any | GitHub only |
| **Branch Analysis** | All branches | All branches |
| **PR/Review Data** | No | Yes |
| **Dependencies** | Git CLI only | Internet + API access |

## Development

### Project Structure

```
daily-work-recorder/
├── record.py                 # GitHub API implementation
├── record_git_cli.py         # Git CLI implementation
├── example_usage.py          # GitHub API examples
├── example_usage_git_cli.py  # Git CLI examples
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .env                      # Environment variables (create this)
```

### Testing

Run the example scripts to test both implementations:

```bash
# Test Git CLI version (must be in a git repository)
python example_usage_git_cli.py

# Test GitHub API version (requires API token)
python example_usage.py
```

## Common Issues

### Git CLI Version

1. **"No git repository found"**
   - Ensure you're running the script from within a git repository
   - Check that `.git` folder exists in current or parent directories
   - Use `--repo-path` to specify a different repository location

2. **"No git repository found at: /path/to/repo"**
   - Verify the path exists and contains a `.git` folder
   - Check file permissions for the repository directory
   - Use absolute paths or properly expand `~` in paths

3. **No commits found**
   - Verify the date range includes your commits
   - Check that your git author name/email matches the username filter

### GitHub API Version

1. **"Error: GITHUB_TOKEN environment variable not set"**
   - Create a GitHub Personal Access Token
   - Add it to your `.env` file

2. **"No repositories found"**
   - Verify organization name is correct
   - Check that your token has `read:org` permission
   - Ensure you're a member of the organization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
