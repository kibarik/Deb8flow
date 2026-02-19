#!/usr/bin/env python3
"""
Migration script for moving prompts from old to new location.

Usage:
    python scripts/migrate_prompts.py [--dry-run]
"""

import shutil
import argparse
from pathlib import Path


OLD_PROMPTS_DIR = Path("config/prompts")
NEW_PROMPTS_DIR = Path("src/prompts")


def backup_old_prompts():
    """Backup existing old prompts."""
    backup_path = Path("config/prompts.backup")

    if OLD_PROMPTS_DIR.exists():
        if backup_path.exists():
            print(f"Backup already exists: {backup_path}")
            return False

        print(f"Backing up {OLD_PROMPTS_DIR} to {backup_path}")
        shutil.copytree(OLD_PROMPTS_DIR, backup_path)
        return True

    return False


def migrate_role_prompts(dry_run=False):
    """Migrate role prompts from old to new location."""
    old_roles = OLD_PROMPTS_DIR / "roles"
    new_roles = NEW_PROMPTS_DIR / "roles"

    if not old_roles.exists():
        print(f"No old role prompts found at: {old_roles}")
        return 0

    # Create new directory
    if not dry_run:
        new_roles.mkdir(parents=True, exist_ok=True)

    migrated = 0
    for old_file in old_roles.glob("*.txt"):
        new_file = new_roles / f"{old_file.stem}.md"

        if new_file.exists():
            print(f"Skipping (exists): {new_file}")
            continue

        print(f"{'Would migrate' if dry_run else 'Migrating'}: {old_file} -> {new_file}")

        if not dry_run:
            # Read content
            content = old_file.read_text(encoding='utf-8')

            # Write to new location with basic enhancement
            enhanced_content = f"""# {old_file.stem.upper()} Role

*Migrated from {old_file}*

{content}
"""
            new_file.write_text(enhanced_content, encoding='utf-8')

        migrated += 1

    return migrated


def update_config_file(dry_run=False):
    """Update config file to point to new prompt paths."""
    config_file = Path("config/debate_config.yaml")

    if not config_file.exists():
        print(f"Config file not found: {config_file}")
        return

    content = config_file.read_text(encoding='utf-8')

    # Check if already updated
    if "src/prompts" in content:
        print("Config file already references src/prompts")
        return

    print(f"{'Would update' if dry_run else 'Updating'}: {config_file}")

    if not dry_run:
        # Replace old paths with new paths
        content = content.replace("config/prompts/roles", "src/prompts/roles")
        config_file.write_text(content, encoding='utf-8')
        print("Config file updated")


def main():
    parser = argparse.ArgumentParser(description="Migrate prompts to new location")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN MODE - No changes will be made\n")

    # Backup
    if not args.dry_run:
        backup_old_prompts()
    else:
        print("Would backup old prompts\n")

    # Migrate
    migrated = migrate_role_prompts(args.dry_run)

    print(f"\n{'Would migrate' if dry_run else 'Migrated'} {migrated} role prompts")

    # Update config
    update_config_file(args.dry_run)

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")


if __name__ == "__main__":
    main()
