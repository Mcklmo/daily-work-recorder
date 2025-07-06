#!/usr/bin/env python3
"""
Example usage of the GitHub Daily Work Recorder with repository filtering.
"""

import os
import pendulum
from dotenv import load_dotenv
from record import GitHubActivityTracker

load_dotenv()


def example_filtered_report():
    """Example of generating a report for specific repositories"""

    # Configuration
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "mcklmo")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    ORG_NAME = os.getenv("GITHUB_ORG", "BC-Technology")

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        return

    # Initialize tracker
    tracker = GitHubActivityTracker(GITHUB_TOKEN, ORG_NAME)

    # Example 1: Filter for specific repositories
    print("=" * 80)
    print("Example 1: Filtering for heads-backend and heads-frontend")
    print("=" * 80)

    # Create date range for last 7 days
    today = pendulum.now()
    week_ago = today.subtract(days=7)
    period = pendulum.interval(week_ago, today)

    repository_filter = ["heads-backend", "heads-frontend"]

    report = tracker.get_github_daily_work(
        username=GITHUB_USERNAME,
        target_date_range=period,
        repository_filter=repository_filter,
    )

    print(report)

    # Save to file
    filename = f"example_filtered_report_{today.format('YYYY-MM-DD')}.md"
    with open(filename, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")

    # Example 2: Process all repositories (no filter)
    print("\n" + "=" * 80)
    print("Example 2: Processing all repositories")
    print("=" * 80)

    report_all = tracker.get_github_daily_work(
        username=GITHUB_USERNAME,
        target_date_range=period,
        repository_filter=None,  # No filter - process all repos
    )

    print(report_all)

    # Example 3: Single repository
    print("\n" + "=" * 80)
    print("Example 3: Single repository - heads-backend only")
    print("=" * 80)

    single_repo_filter = ["heads-backend"]

    report_single = tracker.get_github_daily_work(
        username=GITHUB_USERNAME,
        target_date_range=period,
        repository_filter=single_repo_filter,
    )

    print(report_single)


def example_custom_date_ranges():
    """Example of different date range options"""

    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "mcklmo")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    ORG_NAME = os.getenv("GITHUB_ORG", "BC-Technology")

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        return

    tracker = GitHubActivityTracker(GITHUB_TOKEN, ORG_NAME)
    repository_filter = ["heads-backend", "heads-frontend"]

    print("=" * 80)
    print("Example: Different Date Ranges")
    print("=" * 80)

    # Yesterday only
    today = pendulum.now()
    yesterday = today.subtract(days=1)
    yesterday_period = pendulum.interval(yesterday, today)

    print(f"Yesterday: {yesterday_period.start.format('YYYY-MM-DD')}")

    # Last week
    week_ago = today.subtract(weeks=1)
    week_period = pendulum.interval(week_ago, today)

    print(
        f"Last week: {week_period.start.format('YYYY-MM-DD')} to {week_period.end.format('YYYY-MM-DD')}"
    )

    # Specific date range
    start_date = pendulum.parse("2024-01-01")
    end_date = pendulum.parse("2024-01-31")
    custom_period = pendulum.interval(start_date, end_date)

    print(
        f"Custom range: {custom_period.start.format('YYYY-MM-DD')} to {custom_period.end.format('YYYY-MM-DD')}"
    )

    # Generate report for yesterday (as example)
    report = tracker.get_github_daily_work(
        username=GITHUB_USERNAME,
        target_date_range=yesterday_period,
        repository_filter=repository_filter,
    )

    print("\n" + "-" * 40)
    print("Sample Report (Yesterday):")
    print("-" * 40)
    print(report)


if __name__ == "__main__":
    print("GitHub Daily Work Recorder - Example Usage")
    print("This script demonstrates different ways to use repository filtering.")
    print()

    # Run examples
    example_filtered_report()
    print("\n" + "=" * 80)
    example_custom_date_ranges()
