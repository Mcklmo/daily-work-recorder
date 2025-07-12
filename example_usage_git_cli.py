#!/usr/bin/env python3
"""
Example usage of the Git CLI-based activity tracker.

This script demonstrates how to use the GitActivityTracker to generate
activity reports from the current git repository.
"""

import pendulum
import os
from dotenv import load_dotenv

# Import the new Git CLI implementation
from record_git_cli import GitActivityTracker


def main():
    # Load environment variables
    load_dotenv()

    # Get configuration from environment variables
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "mcklmo")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Git CLI Activity Tracker Example")
    print(f"=" * 40)

    # Example: Just use the current directory first, then show how to use different paths
    print("Example 1: Using current repository")
    print("-" * 40)

    try:
        # Initialize the tracker (current directory)
        tracker = GitActivityTracker(debug=DEBUG)

        # Get repository info
        repo_name = tracker.get_repo_name()
        print(f"Repository: {repo_name}")
        print(f"Repository Path: {tracker.repo_path}")
        print()

        # Example 1: Last 7 days
        print("Activity in the last 7 days")
        print("-" * 20)

        today = pendulum.today()
        week_ago = today.subtract(days=7)
        period = pendulum.interval(week_ago, today)

        print(
            f"Period: {period.start.format('YYYY-MM-DD')} to {period.end.format('YYYY-MM-DD')}"
        )

        report = tracker.get_git_daily_work(GITHUB_USERNAME, period)

        # Save report
        filename = f"git_report_last_7_days_{repo_name}.md"
        with open(filename, "w") as f:
            f.write(report)
        print(f"Report saved to: {filename}")
        print()

        # Example 2: Current month
        print("Activity in the current month")
        print("-" * 20)

        start_of_month = pendulum.now().start_of("month")
        end_of_month = pendulum.now().end_of("month")
        monthly_period = pendulum.interval(start_of_month, end_of_month)

        print(
            f"Period: {monthly_period.start.format('YYYY-MM-DD')} to {monthly_period.end.format('YYYY-MM-DD')}"
        )

        monthly_report = tracker.get_git_daily_work(GITHUB_USERNAME, monthly_period)

        # Save monthly report
        monthly_filename = (
            f"git_report_monthly_{repo_name}_{start_of_month.format('YYYY-MM')}.md"
        )
        with open(monthly_filename, "w") as f:
            f.write(monthly_report)
        print(f"Monthly report saved to: {monthly_filename}")
        print()

        # Example 3: Custom date range
        print("Custom date range")
        print("-" * 20)

        custom_start = pendulum.parse("2025-01-01")
        custom_end = pendulum.parse("2025-01-15")
        custom_period = pendulum.interval(custom_start, custom_end)

        print(
            f"Period: {custom_period.start.format('YYYY-MM-DD')} to {custom_period.end.format('YYYY-MM-DD')}"
        )

        custom_report = tracker.get_git_daily_work(GITHUB_USERNAME, custom_period)

        # Save custom report
        custom_filename = f"git_report_custom_{repo_name}_{custom_start.format('YYYY-MM-DD')}_to_{custom_end.format('YYYY-MM-DD')}.md"
        with open(custom_filename, "w") as f:
            f.write(custom_report)
        print(f"Custom report saved to: {custom_filename}")

        print("\nExample 1 completed successfully!")

    except ValueError as e:
        print(f"Error: {e}")
        print(
            "Please run this script from within a git repository or its subdirectories."
        )
        return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1

    print("\n" + "=" * 40)
    print("Example 2: Using a different repository path")
    print("-" * 40)

    # Example with different repository path
    # Change this to an actual repository path on your system
    example_repo_path = os.path.expanduser("~/Projects/another-repo")

    print(f"Trying to analyze repository at: {example_repo_path}")
    print("(This will likely fail unless you have a repo at this path)")
    print()

    try:
        # Initialize the tracker with a specific repository path
        tracker = GitActivityTracker(repo_path=example_repo_path, debug=DEBUG)

        # Get repository info
        repo_name = tracker.get_repo_name()
        print(f"Repository: {repo_name}")
        print(f"Repository Path: {tracker.repo_path}")

        # Generate a quick report
        today = pendulum.today()
        week_ago = today.subtract(days=7)
        period = pendulum.interval(week_ago, today)

        report = tracker.get_git_daily_work(GITHUB_USERNAME, period)

        filename = f"git_report_external_{repo_name}.md"
        with open(filename, "w") as f:
            f.write(report)
        print(f"Report saved to: {filename}")

    except ValueError as e:
        print(f"Expected error: {e}")
        print(
            "To use this feature, change the 'example_repo_path' variable to point to a valid git repository."
        )
    except Exception as e:
        print(f"An error occurred: {e}")

    print("\nTo analyze a different repository, you can:")
    print("1. Update the 'example_repo_path' variable in this script")
    print(
        "2. Use command line arguments: python record_git_cli.py --repo-path /path/to/repo"
    )
    print("3. Set the REPO_PATH environment variable")

    return 0


if __name__ == "__main__":
    exit(main())
