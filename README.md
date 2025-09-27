# BCT Git Activity Tracker for Notion

This CLI tool scans your local directories for git repositories, finds commits for a given day, and creates a work record for that day in Notion.

## Prerequisites

- Python 3.12
- Notion API key
- Notion database id

### Environment Variables

Can be added to a `.env` file in the root of the project.

```env
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
```

### Initialize virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### All supported arguments

```bash
python3 src/main.py --help

usage: main.py [-h] -r WORK_REPOSITORY_PATH -g GIT_USERNAME -p NOTION_PROJECT -n NOTION_USER_NAME [-dh DURATION_HOURS] [-d DATE] [-s START_DATE] [-e END_DATE]
               [-dw DAYS_OF_WEEK]

BCT Git activity tracker for Notion

options:
  -h, --help            show this help message and exit
  -r WORK_REPOSITORY_PATH, --work-repository-path WORK_REPOSITORY_PATH
                        Path to the work repository. This will be scanned recursively for git repositories. Each git repository will be scanned for commits. Each commit will be added to the work record.
  -g GIT_USERNAME, --git-username GIT_USERNAME
                        git username to filter by. This will be used to filter the git repositories.
  -p NOTION_PROJECT, --notion-project NOTION_PROJECT
                        Notion project name. This will be used to find the project in our Time Registration Codes database and add it to the work record.
  -n NOTION_USER_NAME, --notion-user-name NOTION_USER_NAME
                        Notion user name. This will be used to find your user in the Notion database and add it to the work record.
  -dh DURATION_HOURS, --duration-hours DURATION_HOURS
                        Work duration in hours (default: 0)
  -d DATE, --date DATE  Date of the work (YYYY-MM-DD) (default: empty)
  -s START_DATE, --start-date START_DATE
                        Start date of the work (YYYY-MM-DD) (default: empty)
  -e END_DATE, --end-date END_DATE
                        End date of the work (YYYY-MM-DD) (default: empty)
  -dw DAYS_OF_WEEK, --days-of-week DAYS_OF_WEEK
                        Days of the week to include in the work (default: 0,1,2,3,4,5,6)
```

### Example Usage

```bash
python3 src/main.py --date 2025-07-18 --work-repository-path /Users/moritzmarcushonscheidt/Projects/ --git-username mcklmo --notion-project "Heads" --notion-user-name "Moritz Marcus Hönscheidt" --duration-hours 0
```

### Usage with start and end date

```bash
python3 src/main.py --start-date 2025-09-28 --end-date 2025-09-28 --work-repository-path /Users/moritzmarcushonscheidt/Projects/ --git-username mcklmo --notion-project "Heads" --notion-user-name "Moritz Marcus Hönscheidt" --duration-hours 0
```

### Example Output

The output is also written to a markdown file in the current directory.

```markdown
# Git history for 2025-07-18

* ACE.Pythonscrapers.gme                       : `2025-07-18 14:49:51` (232daec24410a4b78f31459c452d9f57f9bdd653) **[DO-716] migrate to new ftps server**
* ACE.PythonScrapers.Southpool                 : `2025-07-18 13:23:32` (771601e124b2b540e64e093e4cd9d3be1e1f4227) **[DATAP-6733] extend schedule to 12:44-13.30**
* ACE.PythonScrapers.isone                     : `2025-07-18 09:39:05` (7c4ad639bcffd4ec320aa776ed79dbc43aea8c3f) **Revert "[test] add new schedule for debugging"**
* ACE.PythonScrapers.Southpool                 : `2025-07-18 09:33:40` (e0d73bdad809d26086f824e41a288a1d9d0a9c5e) **[DATAP-6733] fix broken cron job**
* ACE.PythonScrapers.meteocontrol              : `2025-07-18 07:40:25` (0b2293cacc30071f1f55c9263046f82eea56fb92) **[alert2333582] raise ttl and request timeout**
```
