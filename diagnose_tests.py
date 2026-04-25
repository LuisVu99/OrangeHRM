#!/usr/bin/env python3
"""
Automated Test Isolation Diagnostics Script

This script systematically tests your test suite to identify:
- Shared state between tests
- Fixture scope issues
- Test order dependencies
- Parallel execution conflicts

Usage:
    python diagnose_tests.py
    python diagnose_tests.py --verbose
    python diagnose_tests.py --fix-suggestions
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import re

class TestDiagnostician:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {}
        self.project_root = Path(__file__).parent
        
    def run_pytest(self, test_path: str, extra_args: str = "") -> Tuple[bool, str]:
        """Run pytest and capture output"""
        cmd = f"pytest {test_path} -v --tb=short {extra_args}"
        
        if self.verbose:
            print(f"→ Running: {cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_root)
            )
            output = result.stdout + result.stderr
            passed = result.returncode == 0
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        except Exception as e:
            return False, str(e)
    
    def count_passed_failed(self, output: str) -> Tuple[int, int]:
        """Parse pytest output for pass/fail counts"""
        # Look for "X passed, Y failed" pattern
        match = re.search(r'(\d+) passed(?:, (\d+) failed)?', output)
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2)) if match.group(2) else 0
            return passed, failed
        return 0, 0
    
    def test_1_single_modules(self):
        """Test 1: Run each test module individually"""
        print("\n" + "="*70)
        print("TEST 1: Individual Module Execution (Baseline)")
        print("="*70)
        print("This identifies if tests fail in isolation or only together\n")
        
        modules = [
            "tests/ui/login",
            "tests/ui/admin",
            "tests/ui/pim",
            "tests/ui/leave",
            "tests/ui/punch",
            "tests/ui/dashboard",
        ]
        
        results = {}
        for module in modules:
            print(f"Testing {module}...", end=" ", flush=True)
            passed, output = self.run_pytest(module)
            results[module] = (passed, output)
            
            p_count, f_count = self.count_passed_failed(output)
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} ({p_count}p, {f_count}f)")
        
        self.results['test_1'] = results
        return results
    
    def test_2_two_module_combinations(self):
        """Test 2: Run module pairs to detect cross-module issues"""
        print("\n" + "="*70)
        print("TEST 2: Two-Module Combinations (Interaction Test)")
        print("="*70)
        print("Tests if modules interfere with each other\n")
        
        modules = [
            "tests/ui/login",
            "tests/ui/admin", 
            "tests/ui/pim",
        ]
        
        results = {}
        for i, mod1 in enumerate(modules):
            for mod2 in modules[i+1:]:
                combo = f"{mod1} + {mod2}"
                print(f"Testing {combo}...", end=" ", flush=True)
                passed, output = self.run_pytest(f"{mod1} {mod2}")
                results[combo] = (passed, output)
                
                p_count, f_count = self.count_passed_failed(output)
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"{status} ({p_count}p, {f_count}f)")
        
        self.results['test_2'] = results
        return results
    
    def test_3_reverse_execution(self):
        """Test 3: Run tests in reverse order"""
        print("\n" + "="*70)
        print("TEST 3: Reverse Order Execution (Order Dependency Test)")
        print("="*70)
        print("If only forward order fails, there's test order dependency\n")
        
        # Forward order
        order_forward = "tests/ui/login tests/ui/admin tests/ui/pim tests/ui/leave tests/ui/punch tests/ui/dashboard"
        
        # Reverse order  
        order_reverse = "tests/ui/dashboard tests/ui/punch tests/ui/leave tests/ui/pim tests/ui/admin tests/ui/login"
        
        print("Running in FORWARD order...", end=" ", flush=True)
        passed_fwd, output_fwd = self.run_pytest(order_forward)
        p_fwd, f_fwd = self.count_passed_failed(output_fwd)
        status_fwd = "✓ PASS" if passed_fwd else "✗ FAIL"
        print(f"{status_fwd} ({p_fwd}p, {f_fwd}f)")
        
        print("Running in REVERSE order...", end=" ", flush=True)
        passed_rev, output_rev = self.run_pytest(order_reverse)
        p_rev, f_rev = self.count_passed_failed(output_rev)
        status_rev = "✓ PASS" if passed_rev else "✗ FAIL"
        print(f"{status_rev} ({p_rev}p, {f_rev}f)")
        
        results = {
            'forward': (passed_fwd, output_fwd),
            'reverse': (passed_rev, output_rev)
        }
        
        self.results['test_3'] = results
        return results
    
    def test_4_full_suite(self):
        """Test 4: Full test suite execution"""
        print("\n" + "="*70)
        print("TEST 4: Full Test Suite Execution")
        print("="*70)
        print("Tests the complete suite as it would run in CI/CD\n")
        
        print("Running full tests/ui/...", end=" ", flush=True)
        passed, output = self.run_pytest("tests/ui/")
        p_count, f_count = self.count_passed_failed(output)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} ({p_count}p, {f_count}f)")
        
        self.results['test_4'] = (passed, output)
        return passed, output
    
    def analyze_results(self):
        """Analyze all results and provide diagnosis"""
        print("\n" + "="*70)
        print("DIAGNOSIS & ROOT CAUSE ANALYSIS")
        print("="*70)
        
        # Extract results
        test_1_results = self.results.get('test_1', {})
        test_2_results = self.results.get('test_2', {})
        test_3_results = self.results.get('test_3', {})
        test_4_passed, test_4_output = self.results.get('test_4', (None, ""))
        
        # Test 1 Analysis
        all_individual_pass = all(passed for passed, _ in test_1_results.values())
        failing_modules = [mod for mod, (passed, _) in test_1_results.items() if not passed]
        
        print("\n1. TEST ISOLATION ANALYSIS")
        print("-" * 70)
        
        if all_individual_pass:
            print("✓ All individual modules PASS")
            print("  → Tests are stable in isolation")
        else:
            print("✗ Some modules FAIL individually:")
            for mod in failing_modules:
                print(f"    - {mod}")
            print("  → FIX THESE FIRST before investigating test interaction issues")
            return
        
        # Test 2 Analysis
        print("\n2. CROSS-MODULE INTERACTION ANALYSIS")
        print("-" * 70)
        
        failing_combos = [combo for combo, (passed, _) in test_2_results.items() if not passed]
        
        if not failing_combos:
            print("✓ All module pair combinations PASS")
            print("  → Modules don't directly interfere with each other")
        else:
            print("✗ Some combinations FAIL:")
            for combo in failing_combos:
                print(f"    - {combo}")
            print("  → ROOT CAUSE: Likely #2 (Context/Browser state) or #3 (Login session leak)")
        
        # Test 3 Analysis
        print("\n3. TEST EXECUTION ORDER DEPENDENCY ANALYSIS")
        print("-" * 70)
        
        test_3_fwd, test_3_fwd_out = test_3_results.get('forward', (None, ""))
        test_3_rev, test_3_rev_out = test_3_results.get('reverse', (None, ""))
        
        if test_3_fwd == test_3_rev:
            print("✓ Forward and reverse order have SAME result")
            print("  → No execution order dependency")
        else:
            print("✗ Forward and reverse order have DIFFERENT results")
            fwd_status = "PASS" if test_3_fwd else "FAIL"
            rev_status = "PASS" if test_3_rev else "FAIL"
            print(f"  → Forward: {fwd_status}, Reverse: {rev_status}")
            print("  → ROOT CAUSE: Likely #4 (Race condition/Timing) or #5 (Test data lingering)")
        
        # Test 4 Analysis
        print("\n4. FULL SUITE ANALYSIS")
        print("-" * 70)
        
        if test_4_passed:
            print("✓ Full test suite PASSES")
            print("  → No persistent issue detected")
        else:
            print("✗ Full test suite FAILS")
            p_count, f_count = self.count_passed_failed(test_4_output)
            print(f"  → {f_count} test(s) failed")
        
        # Summary diagnosis
        print("\n" + "="*70)
        print("ROOT CAUSE MOST LIKELY:")
        print("="*70)
        
        diagnosis = []
        confidence = 0
        
        if all_individual_pass and test_4_passed:
            diagnosis.append("No issue detected")
            confidence = 100
        elif all_individual_pass and not test_4_passed:
            # Full suite fails, but individuals pass
            if failing_combos:
                diagnosis.append("ROOT CAUSE #2/#3: Browser/Context/Login session reuse")
                diagnosis.append("  - Browser is session-scoped, context/page are function-scoped")
                diagnosis.append("  - Session cookies might persist between tests")
                diagnosis.append("  - Login state not properly isolated")
                confidence = 85
            else:
                diagnosis.append("ROOT CAUSE #1/#4: Timing/Race condition or parallel execution")
                diagnosis.append("  - Tests work individually and in pairs")
                diagnosis.append("  - But fail in full suite (more async operations)")
                confidence = 70
        
        for line in diagnosis:
            print(line)
        
        print(f"\nConfidence Level: {confidence}%")
        
        # Recommended next steps
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        
        if not diagnosis or diagnosis[0] == "No issue detected":
            print("✓ Your tests appear to be properly isolated")
            print("  → Run 'pytest tests/ui/ -v' again to confirm consistency")
        else:
            print("\nRefer to TEST_ISOLATION_DEBUG_GUIDE.md for detailed fix procedures")
            print("\nQuick fixes to try:")
            if "session" in diagnosis[0].lower():
                print("  1. In conftest.py, change browser fixture scope from 'session' to 'function'")
                print("  2. Add explicit logout to login fixture cleanup")
                print("  3. Clear localStorage/sessionStorage between tests")
            elif "race" in diagnosis[0].lower() or "timing" in diagnosis[0].lower():
                print("  1. Add page.wait_for_load_state('networkidle') after navigation")
                print("  2. Increase default timeout in config.py")
                print("  3. Check for async operations not properly awaited")
    
    def run_all_diagnostics(self):
        """Run complete diagnostic suite"""
        print("\n" + "="*80)
        print(" ORANGEHRM PLAYWRIGHT TEST ISOLATION DIAGNOSTIC")
        print("="*80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.project_root}")
        
        try:
            self.test_1_single_modules()
            self.test_2_two_module_combinations()
            self.test_3_reverse_execution()
            self.test_4_full_suite()
            self.analyze_results()
            
        except KeyboardInterrupt:
            print("\n\n⚠ Diagnostics interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n✗ Error during diagnostics: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        print("\n" + "="*80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Diagnose test isolation issues in OrangeHRM Playwright suite"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output including full pytest commands"
    )
    parser.add_argument(
        "-f", "--fix-suggestions",
        action="store_true",
        help="Show code fix suggestions in output"
    )
    
    args = parser.parse_args()
    
    diagnostician = TestDiagnostician(verbose=args.verbose)
    diagnostician.run_all_diagnostics()


if __name__ == "__main__":
    main()
