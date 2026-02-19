---
work_package_id: WP08
title: Backward Compatibility and Migration
lane: "doing"
dependencies: []
base_branch: main
base_commit: 0f9e2870e2835886b05c648157cf30abe994f298
created_at: '2026-02-19T07:17:40.950956+00:00'
subtasks: [T042, T043, T044, T045, T046, T047]
shell_pid: "79918"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP08: Backward Compatibility and Migration

## Objective

Ensure backward compatibility with existing `config/prompts/roles/` files, add fallback logic, create migration guide, and update documentation.

## Context

Users may have:
- Existing `config/prompts/roles/` files
- Custom prompts they've created
- Existing workflows that depend on old paths

We need to:
1. Add fallback to old prompt paths
2. Create migration script
3. Add deprecation warnings
4. Update documentation
5. Ensure no regressions

## Implementation Guidance

### T042: Add Fallback Logic to PromptLoader

**Purpose:** Fall back to old prompt paths if new ones don't exist.

**Steps:**

1. Update `PromptLoader._load_file()` in `prompt_loader.py`:
   ```python
   def _load_file(self, prompt_id: str, file_path: str) -> None:
       """Load a single prompt file into cache with fallback."""
       path = self._resolve_path(file_path)

       if not path.exists():
           # Try fallback to old location
           old_path = self._resolve_path(
               file_path.replace("src/prompts", "config/prompts")
           )

           if old_path.exists():
               logger.warning(
                   f"Using deprecated prompt path for {prompt_id}: {old_path}. "
                   f"Please migrate to: {path}"
               )
               path = old_path
           else:
               raise FileNotFoundError(
                   f"Prompt file not found: {path}\n"
                   f"Also checked deprecated location: {old_path}"
               )

       content = path.read_text(encoding='utf-8').strip()

       if not content:
           raise ValueError(f"Prompt file is empty: {path}")

       with self._lock:
           self._cache[prompt_id] = content

       logger.debug(f"Loaded prompt: {prompt_id} from {path}")
   ```

**Files:**
- `src/shared/debate/application/prompt_loader.py` (modify, ~20 lines)

**Validation:**
- [ ] Falls back to old location if new doesn't exist
- [ ] Logs warning when using deprecated path
- [ ] Error message includes both paths checked
- [ ] New location is preferred

---

### T043: Create Migration Script

**Purpose:** Create script to migrate old prompts to new location.

**Steps:**

1. Create `scripts/migrate_prompts.py`:
   ```python
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

       print(f"\n{'Would migrate' if args.dry_run else 'Migrated'} {migrated} role prompts")

       # Update config
       update_config_file(args.dry_run)

       if args.dry_run:
           print("\nRun without --dry-run to apply changes")


   if __name__ == "__main__":
       main()
   ```

**Files:**
- `scripts/migrate_prompts.py` (new, ~120 lines)

**Validation:**
- [ ] Script backs up originals
- [ ] Script migrates role prompts
- [ ] Script updates config file
- [ ] Dry-run mode works
- [ ] Script is executable

---

### T043-T047: Remaining Tasks

**T044: Add Deprecation Warnings** - Already done in T042

**T045: Update README:**

1. Update `README.md`:
   ```markdown
   ## Prompt Management

   Deb8flow uses file-based prompts for easy customization.

   ### Prompt Location

   All prompts are stored in `src/prompts/`:
   - `debate/stages/` - Individual stage prompts
   - `debate/judge/` - Judge evaluation prompts
   - `debate/context/` - Context templates
   - `analysis/` - Takeaway analysis prompts
   - `roles/` - Agent role descriptions

   ### Editing Prompts

   1. Navigate to `src/prompts/`
   2. Open the relevant `.md` file
   3. Edit the prompt content
   4. Run debates - changes take effect immediately

   ### Template Variables

   Prompts support variables using `{variable}` syntax:
   - `{question}` - Debate question
   - `{topic}` - PRD topic
   - `{prd_content}` - Full PRD
   - `{language}` - Output language
   - `{recent_context}` - Recent messages

   ### Migration

   If you have prompts in the old `config/prompts/` location:
   ```bash
   python scripts/migrate_prompts.py
   ```

   The system will automatically fall back to old locations if needed.
   ```

**Files:**
- `README.md` (modify, add ~40 lines)

**T046: Create PROMPTS.md Guide:**

1. Create `PROMPTS.md`:
   ```markdown
   # Prompt Management Guide

   ## Quick Start

   Edit any prompt in `src/prompts/` and run debates - changes take effect immediately.

   ## Prompt Structure

   ### Debate Stages

   Each debate stage has separate PRO and CON prompts:
   - `opening_pro.md` / `opening_con.md` - Opening statements
   - `rebuttal_pro.md` / `rebuttal_con.md` - Rebuttals
   - `counter_pro.md` / `counter_con.md` - Counter-arguments
   - `final_pro.md` / `final_con.md` - Final arguments

   ### Judge

   `judge/verdict.md` - Judge evaluation and verdict

   ### Analysis

   - `analysis/system_prompt.md` - Analyst system prompt
   - `analysis/takeaway_analysis.md` - Takeaway generation

   ### Roles

   `roles/*.md` - Agent role descriptions (TPM, CPO, CFO, CTO, BDM)

   ## Template Variables

   | Variable | Description | Example |
   |----------|-------------|---------|
   | `{question}` | Debate question | "Should we build this?" |
   | `{topic}` | PRD excerpt | First 500 chars |
   | `{prd_content}` | Full PRD | Complete content |
   | `{language}` | Language | "en", "ru" |
   | `{recent_context}` | Recent messages | Last exchanges |
   | `{pro_prompt}` | PRO role | TPM description |
   | `{con_prompt}` | CON role | Opponent description |

   ## Adding New Stages

   1. Create prompt file: `src/prompts/debate/stages/clarification_pro.md`
   2. Add to config: `config/debate_config.yaml`
   3. Update orchestrator to use new stage
   4. Test with `--mode standard`

   ## Best Practices

   - Be specific about word counts
   - Require evidence-based arguments
   - Emphasize professional tone
   - Include examples in prompts
   - Test changes with sample debates
   ```

**Files:**
- `PROMPTS.md` (new, ~60 lines)

**T047: Run Integration Tests:**

Run full test suite to verify no regressions:
```bash
pytest tests/ -v
```

---

## Definition of Done

- [ ] Fallback logic works for old paths
- [ ] Migration script exists and works
- [ ] Deprecation warnings are logged
- [ ] README is updated
- [ ] PROMPTS.md guide exists
- [ ] Integration tests pass
- [ ] No regressions in existing functionality

---

## Reviewer Guidance

**Check these specific items:**
1. Fallback doesn't break new location preference
2. Migration script backs up before changes
3. Dry-run mode works correctly
4. Documentation is clear and helpful
5. All tests pass
6. No breaking changes for existing users

**Files to Review:**
- `src/shared/debate/application/prompt_loader.py` (fallback logic)
- `scripts/migrate_prompts.py`
- `README.md`
- `PROMPTS.md`
- Test results

---

## Migration Checklist

For users upgrading:
- [ ] Backup existing prompts
- [ ] Run migration script
- [ ] Verify config file updated
- [ ] Test debate execution
- [ ] Check for deprecation warnings
- [ ] Update custom prompt references
