# OrangeHRM Framework - Quick Reference Card

## Setup & Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Setup environment
cp .env.example .env
# Edit .env file if needed
```

## Running Tests

```bash
# All tests
pytest tests/ui/ -v

# Specific test file
pytest tests/ui/login/test_login.py -v

# Specific test function
pytest tests/ui/login/test_login.py::test_login -v

# With specific browser
pytest tests/ui/ --browser-name firefox -v
pytest tests/ui/ --browser-name webkit -v

# With video recording
pytest tests/ui/ --record-video -v

# Different environment
pytest tests/ui/ --env staging -v
pytest tests/ui/ --env prod -v

# Using test markers
pytest tests/ui/ -m "smoke" -v
pytest tests/ui/ -m "not slow" -v
pytest tests/ui/ -m "critical" -v

# Parallel execution (4 workers)
pytest tests/ui/ -n 4 -v

# Stop on first failure
pytest tests/ui/ -x -v

# Show print statements
pytest tests/ui/ -s -v

# With full output
pytest tests/ui/ -vv --tb=short

# Generate Allure report
pytest tests/ui/ -v --alluredir=reports/allure-results

# Generate HTML report
pytest tests/ui/ --html=reports/report.html --self-contained-html
```

## Allure Reporting

```bash
# Generate Allure report
allure generate --clean -o reports/allure-report reports/allure-results

# Open in browser
allure open reports/allure-report

# Generate and open in one command
allure generate --clean -o reports/allure-report reports/allure-results && allure open reports/allure-report
```

## Creating a New Test

```python
def test_my_feature(page):
    """
    Test: Description of what this test does.
    
    Preconditions:
    - List preconditions here
    
    Steps:
    1. Step one
    2. Step two
    3. Step three
    
    Expected Result:
    - Expected outcome
    """
    # Arrange
    login_page = LoginPage(page)
    feature_page = MyFeaturePage(page)
    
    # Act
    login_page.enter_username("Admin")
    login_page.enter_password("admin123")
    login_page.click_login_button()
    login_page.assert_dashboard_page_loads()
    
    feature_page.navigate_to_feature()
    feature_page.perform_action()
    
    # Assert
    feature_page.assert_success()
```

## Creating a New Page Object

```python
from pages.base_page import BasePage
from pages.locators.my_page import MyPageLocators
from helpers.logger import get_logger

logger = get_logger(__name__)

class MyPage(BasePage):
    """Page object for My Feature."""
    
    def __init__(self, page):
        super().__init__(page)
        self.locators = MyPageLocators()
    
    def navigate_to_my_page(self):
        """Navigate to my page."""
        self.navigate("https://example.com/my-page")
        logger.info("Navigated to my page")
    
    def click_element(self):
        """Click on element."""
        self.click(self.locators.ELEMENT)
        logger.debug("Element clicked")
    
    def assert_page_loaded(self):
        """Assert page is loaded."""
        self.assert_visible(self.locators.HEADER)
        logger.info("My page loaded")
```

## Creating Locators

```python
# pages/locators/my_page.py

class MyPageLocators:
    """Locators for My Page."""
    
    # Header elements
    HEADER = "h1.page-title"
    TITLE = "//h1[contains(text(), 'My Page')]"
    
    # Form elements
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "button[type='submit']"
    
    # Messages
    SUCCESS_MESSAGE = "div.success-message"
    ERROR_MESSAGE = "div.error-message"
    
    # Lists
    USER_ROWS = "table tbody tr"
    USER_NAME_CELLS = "table tbody tr td:nth-child(2)"
```

## Using Logging

```python
from helpers.logger import get_logger

logger = get_logger(__name__)

# In your code
logger.debug("Detailed debug information")     # Console: NO, File: YES
logger.info("Important step completed")        # Console: YES, File: YES
logger.warning("Warning message")              # Console: YES, File: YES
logger.error("Error occurred")                 # Console: YES, File: YES
```

## Using Custom Exceptions

```python
from helpers.exceptions import (
    ElementNotVisibleException,
    ElementNotClickableException,
    TimeoutException,
    NavigationException,
    AssertionFailedException
)

# In try-except blocks
try:
    element.click()
except ElementNotClickableException as e:
    logger.error(f"Click failed: {e}")
    # Handle the error
```

## Configuration via Environment

```bash
# Set individual variables
export ADMIN_USER=testadmin
export ADMIN_PASSWORD=testpass123
export HEADLESS=True
export ENVIRONMENT=staging

# Or create .env file
cat > .env << EOF
ADMIN_USER=testadmin
ADMIN_PASSWORD=testpass123
HEADLESS=True
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
EOF
```

## Accessing Configuration

```python
from config import ConfigUrl, BrowserConfig, Credentials, Paths

# URLs
url = ConfigUrl.BASE_URL
url = ConfigUrl.LOGIN_URL

# Browser settings
timeout = BrowserConfig.DEFAULT_TIMEOUT
headless = BrowserConfig.HEADLESS
viewport = BrowserConfig.VIEWPORT

# Credentials
user = Credentials.ADMIN_USER
password = Credentials.ADMIN_PASSWORD

# Paths
screenshots_dir = Paths.SCREENSHOTS_DIR
logs_dir = Paths.LOGS_DIR
```

## Available Base Page Methods

```python
# Navigation
self.navigate(url)

# Clicks & Filling
self.click(locator)
self.fill(locator, text)
self.type_text(locator, text, delay=0.1)

# Waiting
self.wait_for_element_visible(locator)
self.wait_for_element_hidden(locator)
self.wait_for_load_page()
self.wait_thread_sleep(seconds)

# Getting Values
self.get_text(locator)
self.get_attribute(locator, attribute_name)
self.is_visible(locator)
self.is_enabled(locator)

# Assertions
self.assert_visible(locator)
self.assert_hidden(locator)
self.assert_text(locator, expected_text)
self.assert_text_contain(locator, substring)
self.assert_is_enabled(locator)
self.assert_is_disabled(locator)
self.assert_is_selected(locator)

# File Upload
self.upload_file(locator, path)

# Keyboard
self.press_key(key, locator=None)
self.keyboard(key)

# Debugging
self.take_screenshot(name)
self.debug_pause()
```

## Test Markers

```bash
# Smoke tests
pytest tests/ui/ -m "smoke" -v

# Critical tests
pytest tests/ui/ -m "critical" -v

# Not slow
pytest tests/ui/ -m "not slow" -v

# API tests
pytest tests/api/ -m "api" -v

# UI tests
pytest tests/ui/ -m "ui" -v

# Combined
pytest tests/ui/ -m "ui and critical and not slow" -v
```

## Debugging Failed Tests

```bash
# Show output
pytest tests/ui/login/test_login.py -s -v

# Show full tracebacks
pytest tests/ui/login/test_login.py --tb=long -v

# Stop on first failure
pytest tests/ui/ -x -v

# Show local variables on exception
pytest tests/ui/ -l -v

# Drop to debugger on failure
pytest tests/ui/ --pdb -v

# Log level debug
pytest tests/ui/ -v --log-cli-level=DEBUG
```

## Checking Logs

```bash
# View live logs
tail -f logs/automation.log

# Search logs
grep "ERROR\|CRITICAL" logs/automation.log

# Last 100 lines
tail -100 logs/automation.log

# Search for specific test
grep "test_login" logs/automation.log
```

## Common Issues & Solutions

### Element Not Found
```bash
# Check if element exists with waits
pytest tests/ui/ -s -v --log-cli-level=DEBUG
# Review screenshot in reports/
```

### Timeout Errors
```bash
# Increase timeout in .env
DEFAULT_TIMEOUT=30000
NAVIGATION_TIMEOUT=40000
```

### Flaky Tests
```bash
# Run with video recording to see what happens
pytest tests/ui/ --record-video -v
# Check videos/ folder for insights
```

### Element Not Clickable
```bash
# Check visibility and element state
logger.debug(f"Element visible: {page.is_visible(locator)}")
logger.debug(f"Element enabled: {page.locator(locator).is_enabled()}")
```

## File Locations Reference

```
logs/                          # Test logs
  └── automation.log           # Main log file

reports/                       # Test reports
  └── allure-results/         # Allure report data
  └── report.html             # HTML report

videos/                        # Test videos (on failure)

screenshots/                   # Test screenshots

resources/                     # Test resources (images, files)

.env                          # Environment configuration (create from .env.example)
```

## Command Aliases (Optional)

Create these in your shell profile:

```bash
# Bash/Zsh
alias pytest-ui='pytest tests/ui/ -v'
alias pytest-smoke='pytest tests/ui/ -m smoke -v'
alias pytest-report='pytest tests/ui/ -v && allure generate --clean -o reports/allure-report && allure open'

# Windows (PowerShell) - Create alias in profile
Function pytest-ui { pytest tests/ui/ -v }
Function pytest-smoke { pytest tests/ui/ -m smoke -v }
```

## Tips & Tricks

```bash
# Count total tests
pytest tests/ui/ --collect-only -q | tail -1

# List all test markers
pytest --markers

# Save test results to file
pytest tests/ui/ -v > test_results.txt

# Parallel with verbose output
pytest tests/ui/ -n 4 -v

# Combine HTML and Allure reports
pytest tests/ui/ --html=reports/report.html --self-contained-html --alluredir=reports/allure-results

# Run specific test class
pytest tests/ui/admin/test_create_user.py::TestUserCreation -v

# Run tests matching pattern
pytest -k "login" -v  # All tests with "login" in name
```

---

**For more information:**
- 📖 Read `FRAMEWORK_GUIDE.md`
- 📊 Check `OPTIMIZATION_REPORT.md`
- ⚙️ See `config.py` for all options
- 📝 Review `pages/base_page.py` for available methods
