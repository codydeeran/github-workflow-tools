import argparse
import os
import re
from git import Repo
from typing import Union


RELEASE_BRANCHES: list = ["main", "develop", "release", "master"]
BASE_PREFIX: str = "v"
BASE_START_VERSION: int = 0


def print_banner(
    repo_name: str, branch_name: str, latest_tag: str, build_number: str
) -> None:
    print()
    print("Determine Version Utility")
    print("=" * 80)
    print(f"Repository: {repo_name}")
    print(f"Branch: {branch_name}")
    print(f"Release Tag: {latest_tag}")
    print(f"GitHub Build Number: {build_number}")
    print("=" * 80)
    print()


def print_exit_banner(
    repo_name: str,
    branch_name: str,
    latest_version: str,
    latest_tag: str,
    build_number: str,
) -> None:
    print()
    print("Determine Version Utility Completed!")
    print("=" * 80)
    print(f"Repository: {repo_name}")
    print(f"Branch: {branch_name}")
    print(f"Release Tag: {latest_tag}")
    print(f"Full Version: {latest_version}")
    print(f"GitHub Build Number: {build_number}")
    print("=" * 80)
    print()


def determine_version(
    branch_name: str, latest_tag_number: int, build_number: str, prefix: str
) -> Union[str, str, bool]:
    create_new_tag: bool = False

    if branch_name.lower() in RELEASE_BRANCHES:
        latest_tag_number += 1
        create_new_tag = True

    full_tag: str = f"{prefix}{latest_tag_number}.{build_number}"
    short_tag: str = f"{prefix}{latest_tag_number}"

    return full_tag, short_tag, create_new_tag


def main(prefix: str, start_version: str) -> None:
    current_repository: Repo = Repo(".")
    current_repository_name: str = current_repository.working_tree_dir.split("/")[-1]
    current_branch: str = current_repository.active_branch.name

    repo_tags = sorted(
        current_repository.tags, key=lambda t: t.commit.committed_datetime
    )

    latest_tag = repo_tags[-1] if repo_tags else start_version
    latest_tag_number: int = 0

    if repo_tags:
        tag_match = re.search("[0-9].*", latest_tag.__str__())

        if tag_match:
            latest_tag_number: int = int(tag_match.group(0).split(".")[0])

    github_build_number: str = (
        os.getenv("GITHUB_BUILD_NUMBER")
        if os.getenv("GITHUB_BUILD_NUMBER", None)
        else "69"
    )

    print_banner(
        current_repository_name, current_branch, latest_tag, github_build_number
    )

    full_version, short_version, create_new_tag = determine_version(
        current_branch, latest_tag_number, github_build_number, prefix
    )
    print(f"Updated Full Version: {full_version}")
    print(f"Updated Short Version: {short_version}")

    print(
        f"Setting updated full version {full_version} to new_tag environment variable..."
    )
    os.system(f"echo 'new_full_tag={full_version}' >> $GITHUB_ENV")
    os.system(f"echo 'new_short_tag={short_version}' >> $GITHUB_ENV")

    if create_new_tag:
        print(f"Creating Tag {short_version}...")
        new_tag = current_repository.create_tag(
            short_version, message="Tag created by Determine Version Workflow"
        )
        print(f"Created Tag {new_tag}.")

        try:
            print(f"Pushing tag {new_tag} to {current_repository_name}...")
            current_repository.remote("origin").push(new_tag)
            print(f"Tag {new_tag} pushed to {current_repository_name} successfully!")
        except Exception as error:
            print(f"Failed to push tag to origin: {error}")
            exit(1)

    print_exit_banner(
        current_repository_name,
        current_branch,
        full_version,
        short_version,
        github_build_number,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Determine Version",
        description="Utility for handling version with GitHub Actions",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        help=f"Custom prefix to tag. Default is '{BASE_PREFIX}'.",
        default=BASE_PREFIX,
    )
    parser.add_argument(
        "-sv",
        "--start-version",
        help="Custom starting version. Default is latest tag or 0 if no tags are found.",
        default=BASE_START_VERSION,
    )
    args = parser.parse_args()

    main(args.prefix, args.start_version)
