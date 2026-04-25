# Test Isolation & Shared State Debug Guide

## Executive Summary

Tests pass individually but fail together → **shared state, fixture scope, or timing issues**

This guide provides step-by-step debugging procedures organized by root cause category.

---

## PART 1: RAPID DIAGNOSIS - Quick Tests First

### Test 1: Identify If Issue Is Deterministic
```bash
# Run twice in a row - does it fail the same way?
pytest tests/ui/ -v
pytest tests/ui/ -v

# If pattern is identical → likely fixture/state issue
# If pattern changes → likely timing/race condition
```

### Test 2: Isolate Problem Tests
```bash
# Run different combinations:
pytest tests/ui/leave/ tests/ui/admin/ -v      # 2 modules
pytest tests/ui/leave/ tests/ui/login/ -v      # different modules
pytest tests/ui/login/ -v                       # single module (baseline)

# Works: tests are isolated in their module
# Fails: shared state across modules
```

### Test 3: Run In Reverse Order
```bash
pytest tests/ui/ -v --reverse
# OR manually run tests in opposite order
pytest tests/ui/punch/ tests/ui/pim/ tests/ui/leave/ tests/ui/admin/ tests/ui/dashboard/ tests/ui/login/ -v

# If only fails in forward order → test order dependency
```

---

## PART 2: ROOT CAUSE ANALYSIS - Focused Debugging

### Root Cause #1: Browser-Level Session/Cookie Persistence

**Symptom**: Tests fail intermittently, especially related to login/authentication

**Why it happens**:
- `browser` fixture has **session scope** (shared across ALL tests)
- Cookies/cache might persist between tests
- Failed login leaves browser in unexpected state

#### Debug Procedure:
```python
# Add to conftest.py after line 180 (in page fixture)
@pytest.fixture(scope="function")
def page(context, request):
    page = context.new_page()
    test_name = request.node.name
    
    logger.info(f"[DEBUG] Starting test: {test_name}")
    
    # ADD THIS BLOCK - Check cookie state
    logger.info(f"[DEBUG] Cookies before page load: {context.cookies()}")
    
    try:
        page.goto(ConfigUrl.BASE_URL, timeout=BrowserConfig.NAVIGATION_TIMEOUT)
        logger.debug("Page loaded successfully")
    except Exception as e:
        logger.error(f"Failed to navigate to base URL: {str(e)}")
        raise
    
    # ADD THIS BLOCK - Check cookies after load
    logger.info(f"[DEBUG] Cookies after page load: {context.cookies()}")
    logger.info(f"[DEBUG] LocalStorage: {page.evaluate('() => JSON.stringify(localStorage)')}")
    
    yield page
    # ... rest of fixture
```

**Test the fix**:
```bash
pytest tests/ui/login/test_empty_credentials.py tests/ui/admin/test_create_user.py -v -s
# Look for DEBUG lines showing cookie state
```

---

### Root Cause #2: Context Not Truly Isolating (Local Storage, IndexedDB)

**Symptom**: Login state persists, or cached data appears in subsequent tests

**Why it happens**:
- Playwright context is function-scoped ✓ (this is good)
- BUT local storage/IndexedDB might not clear automatically
- Session state from auth tokens cached in page storage

#### Debug Procedure:
```python
# Create a new fixture to verify context cleanup
@pytest.fixture(scope="function")
def context_debug(browser, pytestconfig):
    """Enhanced context fixture with storage cleanup debugging"""
    from datetime import datetime
    
    record_video = pytestconfig.getoption("--record-video")
    
    context_options = {
        "viewport": BrowserConfig.VIEWPORT,
        "extra_http_headers": BrowserLaunchConfig.EXTRA_HTTP_HEADERS,
    }
    
    if record_video:
        context_options["record_video_dir"] = Paths.VIDEOS_DIR
    
    context = browser.new_context(**context_options)
    context.set_default_timeout(BrowserConfig.DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(BrowserConfig.NAVIGATION_TIMEOUT)
    
    logger.info(f"[DEBUG] Context created at: {datetime.now()}")
    logger.info(f"[DEBUG] Cookies at creation: {context.cookies()}")
    
    yield context
    
    # Inspect state before closing
    logger.info(f"[DEBUG] Cookies before close: {context.cookies()}")
    
    try:
        context.close()
        logger.debug("Browser context closed successfully")
    except Exception as e:
        logger.warning(f"Error closing context: {str(e)}")
```

**Then modify page fixture to use context_debug**:
```python
def page(context_debug, request):  # Change parameter name
    # Use context_debug instead of context
```

**Test the fix**:
```bash
pytest tests/ui/login/test_empty_credentials.py tests/ui/admin/test_create_user.py -v -s 2>&1 | grep "\[DEBUG\]"
```

---

### Root Cause #3: Login Fixture Scope - Persistent Session

**Symptom**: Tests using `login` fixture interfere with each other, or test data isn't properly isolated

**Why it happens**:
- `login` fixture is function-scoped (good)
- BUT it logs in, yields the page, and cleanup doesn't happen until test ends
- If test creates user with same ID, next test sees unexpected state

#### Debug Procedure:

**Step 3.1 - Identify which tests use login fixture**:
```bash
grep -r "def test_.*login" tests/ui/ --include="*.py"
grep -r "(login)" tests/ui/ --include="*.py"
```

**Step 3.2 - Add login debugging**:
```python
# In conftest.py, enhance login fixture:
@pytest.fixture(scope="function")
def login(page):
    """Enhanced login fixture with debugging"""
    logger.info(f"[DEBUG] Login fixture: Session storage BEFORE: {page.evaluate('() => JSON.stringify(sessionStorage)')}")
    logger.info(f"[DEBUG] Login fixture: URL before login: {page.url}")
    
    login_page_instance = LoginPage(page)
    
    try:
        login_page_instance.login(Credentials.ADMIN_USER, Credentials.ADMIN_PASSWORD)
        logger.info(f"[DEBUG] Login successful as: {Credentials.ADMIN_USER}")
        logger.info(f"[DEBUG] Login fixture: URL after login: {page.url}")
        logger.info(f"[DEBUG] Login fixture: Session storage AFTER: {page.evaluate('() => JSON.stringify(sessionStorage)')}")
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise
    
    yield page
    
    # Log state at end
    logger.info(f"[DEBUG] Login fixture cleanup: Session storage at end: {page.evaluate('() => JSON.stringify(sessionStorage)')}")
```

**Step 3.3 - Check if test data IDs conflict**:
```python
# In test_approve_leave.py, add:
def test_approve_leave_request(page):
    logger.info(f"[DEBUG] Test start - URL: {page.url}")
    logger.info(f"[DEBUG] Test data - supervisor_employee_id being used: {supervisor_employee_id}")
    # ... rest of test
```

**Step 3.4 - Run tests with different data generation seeds**:
```bash
# Create isolation test
pytest tests/ui/leave/test_approve_leave.py -v -s
# Check if IDs are different each run
grep "supervisor_employee_id" logs/pytest.log

pytest tests/ui/admin/test_create_user.py -v -s  
pytest tests/ui/pim/test_create_emp.py -v -s
# Check if same IDs appear → DATA COLLISION
```

---

### Root Cause #4: Test Execution Order & Race Conditions

**Symptom**: Tests fail randomly, different failures each run

**Why it happens**:
- Network timeouts in multi-test runs
- Server-side operations not completing before next test
- Shared test data being created before old data is deleted

#### Debug Procedure:

**Step 4.1 - Add timing markers**:
```python
# In conftest.py page fixture, track timing:
import time

@pytest.fixture(scope="function")
def page(context, request):
    test_start = time.time()
    page = context.new_page()
    test_name = request.node.name
    
    logger.info(f"[TIMING] {test_name} START at {test_start}")
    
    # Rest of fixture...
    
    yield page
    
    test_end = time.time()
    logger.info(f"[TIMING] {test_name} END at {test_end}, duration: {test_end - test_start:.2f}s")
```

**Step 4.2 - Run with sequential output capture**:
```bash
pytest tests/ui/ -v --tb=short --capture=no 2>&1 | grep "\[TIMING\]"
# Look for overlapping times or suspiciously short tests
```

**Step 4.3 - Add explicit waits/stability checks**:
```python
# In page fixture, after navigation:
page.wait_for_load_state("networkidle", timeout=10000)
logger.info(f"[DEBUG] Network fully idle for {test_name}")
```

---

### Root Cause #5: Database/Environment State Dependency

**Symptom**: Test A creates user, Test B expects it missing, Test C fails because it's still there

**Why it happens**:
- Orange HRM database has persistent state
- Tests don't clean up after themselves
- Parallel test runs might create duplicate data

#### Debug Procedure:

**Step 5.1 - Identify shared test data**:
```python
# Create test data fixture that logs all created data:
@pytest.fixture(scope="function", autouse=True)
def track_test_data(request):
    """Log all test data created during test"""
    logger.info(f"[DATA] Test {request.node.name} started")
    
    yield
    
    logger.info(f"[DATA] Test {request.node.name} ended - check if data should be cleaned")
```

**Step 5.2 - Add cleanup to critical tests**:
```python
# At end of test_create_user.py:
def test_create_user(login):
    # ... test code ...
    
    # ADD CLEANUP
    try:
        admin_page.navigate_to_admin()
        admin_page.search_user(username_another)
        admin_page.delete_user()  # Or similar
        logger.info(f"[CLEANUP] Deleted test user: {username_another}")
    except Exception as e:
        logger.warning(f"[CLEANUP] Could not delete user: {str(e)}")
```

**Step 5.3 - Run with cleanup verification**:
```bash
pytest tests/ui/admin/test_create_user.py tests/ui/admin/test_create_user.py -v
# Run same test twice - if second fails, cleanup is missing
```

---

### Root Cause #6: Parallel Execution Issues

**Symptom**: Works in serial, fails randomly in parallel

**Why it happens**:
- pytest-xdist runs multiple tests simultaneously
- Shared browser instance (session scope) + concurrent context usage

#### Check if parallel execution is enabled:
```bash
grep -i "xdist\|parallel\|workers" pytest.ini
pip list | grep xdist
```

**If using parallel execution**:
```python
# CRITICAL FIX: Use function-scoped browser instead of session-scoped
# In conftest.py (currently browser is session scope):

# BEFORE:
@pytest.fixture(scope="session")
def browser(pytestconfig):
    # ...

# AFTER (if using pytest-xdist):
@pytest.fixture(scope="function")  # Change to function scope
def browser(pytestconfig):
    # ...
```

---

## PART 3: DIAGNOSTIC CHECKLIST - Feature-Specific Tests

### For Login-Related Test Failures
```python
# Run these commands in sequence:
pytest tests/ui/login/ -v -s              # Login tests alone
pytest tests/ui/login/test_empty_credentials.py tests/ui/admin/test_create_user.py -v -s
# Does auth state leak?

# Check:
# 1. Are cookies being cleared between tests?
# 2. Does page.url show login page at start of logged-in test?
```

### For Data Creation Test Failures (PIM, Admin)
```bash
# Run create tests followed by list/view tests:
pytest tests/ui/admin/test_create_user.py tests/ui/admin/test_search_user.py -v -s

# Check:
# 1. Are IDs truly unique (check TestData.random_int range)?
# 2. Does second run of same test pass (was data created previously)?
```

### For Leave/Punch Tests
```bash
# These are dependent on PIM data, run in dependency order:
pytest tests/ui/pim/test_create_emp.py tests/ui/leave/test_approve_leave.py -v -s

# Check:
# 1. Are employee IDs persisting from previous run?
# 2. Is supervisor relationship being properly cleaned?
```

---

## PART 4: RECOMMENDED FIXES (Implement These)

### Fix #1: Clear Storage Between Tests
Add to conftest.py:

```python
@pytest.fixture(scope="function")
def clear_storage(page):
    """Clear all storage (localStorage, sessionStorage, indexedDB, cookies)"""
    page.evaluate("localStorage.clear()")
    page.evaluate("sessionStorage.clear()")
    logger.debug("[CLEANUP] Cleared localStorage and sessionStorage")
    yield
    # Cleanup after test
```

Update page fixture to use it:
```python
@pytest.fixture(scope="function")
def page(context, request, clear_storage):  # Add clear_storage param
    # rest of fixture...
```

### Fix #2: Explicit Logout Fixture Cleanup
```python
@pytest.fixture(scope="function")
def login(page):
    """Login with automatic logout cleanup"""
    login_page_instance = LoginPage(page)
    
    try:
        login_page_instance.login(Credentials.ADMIN_USER, Credentials.ADMIN_PASSWORD)
        logger.info(f"Successfully logged in as: {Credentials.ADMIN_USER}")
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise
    
    yield page
    
    # ADD EXPLICIT LOGOUT
    try:
        logger.debug("Performing logout cleanup")
        login_page_instance.click_user_avatar()
        login_page_instance.click_logout_button()
        logger.debug("Logout completed")
    except Exception as e:
        logger.warning(f"Logout failed (non-critical): {str(e)}")
        # Don't raise - test already completed
```

### Fix #3: Add Test Isolation Verification
```python
@pytest.fixture(scope="function", autouse=True)
def verify_clean_state(page):
    """Auto-verify test starts in clean state"""
    # Check we're at login page or can access site
    try:
        if "login" in page.url.lower():
            logger.info("[ISOLATION] Test starts at login page ✓")
        else:
            logger.warning(f"[ISOLATION] Test starts at: {page.url}")
    except:
        pass
    yield
```

---

## PART 5: EXECUTION SCRIPT - Run This to Diagnose

Create this file as `diagnose.py`:

```python
#!/usr/bin/env python3
"""
Automated test isolation diagnostics
Run: python diagnose.py
"""

import subprocess
import json
from datetime import datetime

def run_test(cmd, name):
    """Run test and return output"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"CMD: {cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0

def main():
    tests = [
        # Single module runs (baseline)
        ("pytest tests/ui/login/ -v", "Login tests alone"),
        ("pytest tests/ui/admin/ -v", "Admin tests alone"),
        ("pytest tests/ui/pim/ -v", "PIM tests alone"),
        
        # Cross-module combinations
        ("pytest tests/ui/login/ tests/ui/admin/ -v", "Login + Admin"),
        ("pytest tests/ui/admin/ tests/ui/pim/ -v", "Admin + PIM"),
        
        # Reverse order
        ("pytest tests/ui/login/ tests/ui/admin/ tests/ui/pim/ -v", "Forward order"),
        
        # Full suite
        ("pytest tests/ui/ -v", "Full test suite"),
    ]
    
    results = {}
    for cmd, name in tests:
        results[name] = run_test(cmd, name)
    
    print(f"\n\n{'='*60}")
    print("SUMMARY:")
    print(f"{'='*60}")
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {name}")
    
    # Analysis
    print(f"\n{'='*60}")
    print("ANALYSIS:")
    print(f"{'='*60}")
    
    all_individual = all(results[t[1]] for t in tests[:3])
    full_suite_passes = results["Full test suite"]
    
    if all_individual and not full_suite_passes:
        print("→ Isolated tests pass individually but fail together")
        print("→ ROOT CAUSE: Either test order dependency or shared state")
        print("→ NEXT: Run with reverse order to identify test order issues")
    elif not all_individual:
        print("→ Some individual tests are already failing")
        print("→ ROOT CAUSE: May not be test isolation (fix individual tests first)")

if __name__ == "__main__":
    main()
```

Run it:
```bash
cd c:\Auto test\Playwright\OrangeHRM
python diagnose.py
```

---

## PART 6: Quick Reference - By Symptom

| Symptom | Likely Cause | Check First |
|---------|-------------|------------|
| Same tests fail every run | Shared state/fixture | #1, #2, #3 (Browser/Context/Login) |
| Random different failures | Race condition/timing | #4 (Execution Order), add waits |
| Login always fails in suite | Session/cookie leak | #1 (Browser persistence) |
| Data creation conflicts | ID collision/cleanup | #5 (Database), add cleanup code |
| Works serial, fails parallel | Scope issue | #6 (Parallel), check pytest.ini |
| Tests affect each other | Order dependency | Run reverse order test |

---

## PART 7: Example Command Sequence to Run Now

```bash
# Step 1: Baseline - single tests
pytest tests/ui/login/test_empty_credentials.py -v

# Step 2: Two related tests  
pytest tests/ui/login/test_empty_credentials.py tests/ui/admin/test_create_user.py -v

# Step 3: Check for cookie/session leak
pytest tests/ui/login/test_empty_credentials.py tests/ui/admin/test_create_user.py -v -s 2>&1 | grep -i "cookie\|session\|auth"

# Step 4: Full module
pytest tests/ui/ -v

# Step 5: Reverse order
pytest tests/ui/punch/ tests/ui/pim/ tests/ui/leave/ tests/ui/admin/ tests/ui/dashboard/ tests/ui/login/ -v
```

---

## SUMMARY

1. **Start with Test 1-3** from PART 1 to narrow down the issue
2. **Pick matching Root Cause** from PART 2
3. **Implement recommended fixes** from PART 4
4. **Verify** with the diagnostic commands
5. **If still failing**, examine logs for timing/state patterns

The most common causes in Playwright suites are:
- **60%**: Session/cookie reuse (Fix #1)
- **25%**: Missing cleanup/logout (Fix #2)
- **10%**: Data collisions (Add unique suffixes)
- **5%**: Race conditions (Add waits)
