#!/usr/bin/env python3
"""
Test Isolation Quick Fixes

Applies recommended fixes from CODE_ANALYSIS_FINDINGS.md

Usage:
    python apply_fixes.py                    # Show all available fixes
    python apply_fixes.py --fix-2            # Apply fix #2 (login logout)
    python apply_fixes.py --fix-all          # Apply all safe fixes
    python apply_fixes.py --preview          # Show what would change
"""

import sys
from pathlib import Path
import argparse
from dataclasses import dataclass
from typing import Optional

@dataclass
class Fix:
    """Represents a fixable issue"""
    number: int
    name: str
    file: str
    description: str
    risk: str  # LOW, MEDIUM, HIGH
    safe: bool  # Can be auto-applied?
    preview: str  # What will change
    implementation: str  # Code to add/change
    
    def __str__(self):
        return f"FIX #{self.number}: {self.name} ({self.risk} risk, {'auto-applicable' if self.safe else 'manual'})"


FIXES = [
    Fix(
        number=2,
        name="Add logout to login fixture cleanup",
        file="tests/conftest.py",
        risk="HIGH",
        safe=True,
        description="""
        The login fixture logs in but doesn't logout, causing session persistence
        to next test. This adds explicit logout in cleanup.
        """,
        preview="""
BEFORE (lines 273):
    yield page
    #Return returns a value and ends the fixture...

AFTER:
    yield page
    
    # Explicit logout cleanup
    try:
        logger.debug("Logging out in fixture cleanup")
        login_page_instance.click_user_avatar()
        login_page_instance.click_logout_button()
        logger.info("Logout cleanup completed successfully")
    except Exception as e:
        logger.warning(f"Logout cleanup failed (non-critical): {str(e)}")
        """,
        implementation="""
import subprocess
result = subprocess.run([
    "sed", "-i",
    's/yield page$/yield page\\n    \\n    # Explicit logout cleanup\\n    try:\\n        logger.debug("Logging out in fixture cleanup")\\n        login_page_instance.click_user_avatar()\\n        login_page_instance.click_logout_button()\\n        logger.info("Logout cleanup completed successfully")\\n    except Exception as e:\\n        logger.warning(f"Logout cleanup failed (non-critical): {str(e)}")
/',
    "tests/conftest.py"
], check=True)
"""
    ),
    
    Fix(
        number=3,
        name="Clear localStorage/sessionStorage in page fixture",
        file="tests/conftest.py",
        risk="MEDIUM",
        safe=True,
        description="""
        Clears localStorage and sessionStorage at start of each test
        to prevent storage-based state persistence.
        """,
        preview="""
BEFORE (after page.goto):
    try:
        page.goto(ConfigUrl.BASE_URL, timeout=BrowserConfig.NAVIGATION_TIMEOUT)
        logger.debug("Page loaded successfully")
    except Exception as e:

AFTER:
    try:
        page.goto(ConfigUrl.BASE_URL, timeout=BrowserConfig.NAVIGATION_TIMEOUT)
        logger.debug("Page loaded successfully")
        
        # Clear storage to ensure clean test state
        try:
            page.evaluate("localStorage.clear();")
            page.evaluate("sessionStorage.clear();")
            logger.debug("Cleared localStorage and sessionStorage")
        except Exception as e:
            logger.warning(f"Could not clear storage: {str(e)}")
    except Exception as e:
        """,
        implementation="Manual edit required"
    ),
]


class FixApplier:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent
        self.conftest_path = self.project_root / "tests" / "conftest.py"
        
    def show_all_fixes(self):
        """Display all available fixes"""
        print("\n" + "="*80)
        print("AVAILABLE TEST ISOLATION FIXES")
        print("="*80 + "\n")
        
        for fix in FIXES:
            safety = "✓ AUTO-APPLICABLE" if fix.safe else "⚠ REQUIRES MANUAL EDIT"
            print(f"\n{fix}")
            print(f"  Safety: {safety}")
            print(f"  Risk Level: {fix.risk}")
            print(f"  File: {fix.file}")
            print("\n" + fix.description.strip())
            
    def show_fix_preview(self, fix_num: int):
        """Show preview of what fix will change"""
        fix = next((f for f in FIXES if f.number == fix_num), None)
        if not fix:
            print(f"✗ Fix #{fix_num} not found")
            return False
            
        print(f"\n{'='*80}")
        print(f"FIX #{fix.number}: {fix.name}")
        print(f"{'='*80}\n")
        print(fix.preview)
        return True
    
    def apply_fix(self, fix_num: int, dry_run: bool = False):
        """Apply a specific fix"""
        fix = next((f for f in FIXES if f.number == fix_num), None)
        if not fix:
            print(f"✗ Fix #{fix_num} not found")
            return False
        
        if not fix.safe:
            print(f"\n⚠ Fix #{fix.number} requires MANUAL editing")
            print(f"  File: {fix.file}")
            print(f"  Please refer to CODE_ANALYSIS_FINDINGS.md for details")
            return False
        
        print(f"\nApplying Fix #{fix.number}: {fix.name}...")
        
        if dry_run:
            print("[DRY RUN] Would apply changes to:", fix.file)
            print(fix.preview)
            return True
        
        # Check file exists
        target_file = self.project_root / fix.file.lstrip("tests/")
        if not target_file.exists():
            print(f"✗ File not found: {target_file}")
            return False
        
        # Apply fix based on number
        if fix.number == 2:
            return self._apply_fix_2(target_file)
        elif fix.number == 3:
            return self._apply_fix_3(target_file)
        else:
            print(f"✗ Auto-apply not implemented for fix #{fix.number}")
            return False
    
    def _apply_fix_2(self, conftest_path: Path) -> bool:
        """Apply Fix #2: logout in login fixture"""
        try:
            content = conftest_path.read_text()
            
            # Find the login fixture and its yield statement
            if "@pytest.fixture(scope=\"function\")\ndef login(page):" not in content:
                print("✗ Could not find login fixture")
                return False
            
            # Find where to insert the logout code
            logout_code = '''    
    # Explicit logout cleanup
    try:
        logger.debug("Logging out in fixture cleanup")
        login_page_instance.click_user_avatar()
        login_page_instance.click_logout_button()
        logger.info("Logout cleanup completed successfully")
    except Exception as e:
        logger.warning(f"Logout cleanup failed (non-critical): {str(e)}")'''
            
            # Check if already applied
            if "Explicit logout cleanup" in content:
                print("✓ Fix #2 already applied")
                return True
            
            # Find "yield page" in login fixture and replace it
            import re
            pattern = r'(def login\(page\):.*?yield page)'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                print("✗ Could not locate insertion point in login fixture")
                return False
            
            # Insert logout code after yield page
            new_content = content.replace(
                "yield page\n    #Return returns",
                "yield page" + logout_code + "\n    #Return returns"
            )
            
            if new_content == content:
                print("⚠ Could not apply fix (text not found, please update manually)")
                return False
            
            conftest_path.write_text(new_content)
            print("✓ Fix #2 applied successfully")
            print("  Added logout cleanup to login fixture")
            return True
            
        except Exception as e:
            print(f"✗ Error applying fix #2: {e}")
            return False
    
    def _apply_fix_3(self, conftest_path: Path) -> bool:
        """Apply Fix #3: clear storage in page fixture"""
        try:
            content = conftest_path.read_text()
            
            # Check if already applied
            if "localStorage.clear" in content:
                print("✓ Fix #3 already applied")
                return True
            
            storage_clear_code = '''
        
        # Clear storage to ensure clean test state
        try:
            page.evaluate("localStorage.clear();")
            page.evaluate("sessionStorage.clear();")
            logger.debug("Cleared localStorage and sessionStorage")
        except Exception as e:
            logger.warning(f"Could not clear storage: {str(e)}")'''
            
            # Find where to insert (after page.goto)
            import re
            pattern = r'(page\.goto\(ConfigUrl\.BASE_URL.*?\n\s+logger\.debug\("Page loaded successfully"\))'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                print("✗ Could not locate page.goto in page fixture")
                return False
            
            # Insert after the logger.debug line
            insertion_point = match.group(1)
            new_insertion = insertion_point + storage_clear_code
            
            new_content = content.replace(insertion_point, new_insertion)
            
            if new_content == content:
                print("⚠ Could not apply fix (text not found)")
                return False
            
            conftest_path.write_text(new_content)
            print("✓ Fix #3 applied successfully")
            print("  Added localStorage/sessionStorage clearing to page fixture")
            return True
            
        except Exception as e:
            print(f"✗ Error applying fix #3: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Apply recommended test isolation fixes"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all available fixes"
    )
    parser.add_argument(
        "--preview",
        type=int,
        metavar="FIX_NUMBER",
        help="Preview what a fix will change"
    )
    parser.add_argument(
        "--apply",
        type=int,
        metavar="FIX_NUMBER",
        help="Apply a specific fix"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available fixes (short form)"
    )
    
    args = parser.parse_args()
    
    applier = FixApplier()
    
    if not args.apply and not args.preview and not args.list and not args.show_all:
        # Default: show everything
        args.show_all = True
    
    if args.show_all:
        applier.show_all_fixes()
        print("\n" + "="*80)
        print("TO APPLY FIXES:")
        print("="*80)
        print("  python apply_fixes.py --apply 2  # Apply Fix #2 (recommended first)")
        print("  python apply_fixes.py --apply 3  # Apply Fix #3")
        print("  python apply_fixes.py --preview 2  # See what Fix #2 will do")
        print("  python apply_fixes.py --dry-run --apply 2  # Dry run of Fix #2")
        print("\n")
        return
    
    if args.list:
        print("\nAvailable fixes:")
        for fix in FIXES:
            print(f"  Fix #{fix.number}: {fix.name} ({fix.risk} risk)")
        print("\n")
        return
    
    if args.preview:
        applier.show_fix_preview(args.preview)
        return
    
    if args.apply:
        success = applier.apply_fix(args.apply, dry_run=args.dry_run)
        if success:
            print("\n✓ Fix applied successfully!")
            print("  Run: pytest tests/ui/ -v")
            print("  to verify the fix works\n")
        else:
            print("\n✗ Fix could not be applied automatically")
            print("  Please manually edit according to CODE_ANALYSIS_FINDINGS.md\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
