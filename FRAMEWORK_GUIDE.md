"""
README: OrangeHRM Automation Framework

Professional-grade test automation framework for OrangeHRM using Playwright and Pytest.

## Features

✅ **Enterprise-Ready Architecture**
- Page Object Model (POM) with single-responsibility principle
- Comprehensive error handling with custom exceptions
- Centralized logging and reporting
- Environment-based configuration management

✅ **Stability & Reliability**
- Explicit wait handling with proper timeout management
- Network-aware page load detection
- Retry mechanism support
- Screenshot and video capture for debugging

✅ **Maintainability**
- Clean code principles (SOLID)
- Consistent naming conventions
- Professional documentation and docstrings
- No hardcoded values - configuration driven

✅ **Scalability**
- Easy to add new page objects and tests
- Supports multiple environments (dev, staging, prod)
- Framework hooks for custom reporting
- Proper fixture organization for test isolation

✅ **CI/CD Ready**
- Environment variable support
- Headless and headed mode
- Video recording for failed tests
- Comprehensive Allure reporting

---

## Project Structure

```
.
├── config.py                    # Framework configuration (environment-based)
├── pytest.ini                   # Pytest configuration with markers
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── README.md                    # This file
│
├── pages/                       # Page Object Models
│   ├── base_page.py            # Base class with common methods
│   ├── login_page.py           # Login page object
│   ├── admin_page.py           # Admin section page object
│   ├── pim_page.py             # Personnel Info Management page object
│   ├── leave_page.py           # Leave management page object
│   ├── punch_page.py           # Time & Attendance page object
│   ├── dashboard_page.py       # Dashboard page object
│   └── locators/               # Locator classes for elements
│       ├── login.py
│       ├── admin.py
│       ├── pim.py
│       ├── leave.py
│       ├── punch.py
│       └── dashboard.py
│
├── tests/                       # Test files
│   ├── conftest.py             # Pytest fixtures and configuration
│   ├── ui/                     # UI/Browser Automation Tests
│   │   ├── admin/              # Admin user management tests
│   │   ├── login/              # Login and authentication tests
│   │   ├── dashboard/          # Dashboard tests
│   │   ├── pim/                # Employee management tests
│   │   ├── leave/              # Leave management tests
│   │   └── punch/              # Attendance/punctuation tests
│   └── api/                    # API Tests
│
├── helpers/                     # Utility modules
│   ├── logger.py               # Centralized logging setup
│   ├── exceptions.py           # Custom exception classes
│   ├── test_data.py            # Test data generation (Faker)
│   ├── allure_helper.py        # Allure report utilities
│   ├── auth.py                 # Authentication helpers
│   └── __init__.py
│
├── logs/                       # Log files (created at runtime)
├── reports/                    # Test reports
│   └── allure-results/         # Allure report data
├── videos/                     # Video recordings (on failure)
├── screenshots/                # Screenshot captures
└── resources/                  # Test resources (images, files, etc.)
```

---

## Getting Started

### 1. Setup Environment

```bash
# Clone or navigate to project
cd c:\Auto\ test\Playwright\OrangeHRM

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Configure Environment Variables

```bash
# Copy example and edit
cp .env.example .env

# Edit .env with your settings
# Important: Never commit .env with real credentials!
```

### 3. Run Tests

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run specific test module
pytest tests/ui/login/ -v

# Run with specific browser
pytest tests/ui/login/ --browser-name firefox -v

# Run with video recording
pytest tests/ui/login/ --record-video -v

# Run with specific environment
pytest tests/ui/login/ --env staging -v

# Run with tag filtering
pytest tests/ui/ -v -m "not slow"

# Run with Allure reporting
pytest tests/ui/ -v --alluredir=reports/allure-results

# Generate HTML reports
allure generate --clean -o reports/allure-report reports/allure-results
```

---

## Configuration Management

### Using Environment Variables

The framework supports configuration via .env file for security:

```env
# Application URLs
BASE_URL=https://opensource-demo.orangehrmlive.com/web/index.php
ENVIRONMENT=dev

# Credentials (from environment, not hardcoded)
ADMIN_USER=Admin
ADMIN_PASSWORD=admin123

# Browser Settings
HEADLESS=False
DEFAULT_TIMEOUT=20000
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Logging
LOG_LEVEL=INFO
```

### Multi-Environment Support

```bash
# Run against staging
pytest tests/ui/ --env staging -v

# Run against production
pytest tests/ui/ --env prod -v
```

---

## Logging System

### Centralized Logging

Logs are written to both **console** and **file** automatically:

- **Console**: INFO level (interactive watching)
- **File** (`logs/automation.log`): DEBUG level (detailed troubleshooting)

### Using Logging in Code

```python
from helpers.logger import get_logger

logger = get_logger(__name__)

logger.info("Test step completed")
logger.debug("Detailed debug information")
logger.warning("Warning message")
logger.error("Error message")
```

---

## Custom Exception Handling

Framework provides specific exceptions for better error handling:

```python
from helpers.exceptions import (
    ElementNotVisibleException,
    ElementNotClickableException,
    TimeoutException,
    NavigationException,
    AssertionFailedException
)

# These provide meaningful error messages for debugging
```

---

## Page Object Model (POM) Guidelines

### Creating a New Page Object

```python
from pages.base_page import BasePage
from pages.locators.my_page import MyPageLocators
from helpers.logger import get_logger

logger = get_logger(__name__)

class MyPage(BasePage):
    \"\"\"Page object for My Feature.\"\"\"
    
    def __init__(self, page):
        super().__init__(page)
        self.locators = MyPageLocators()
    
    def navigate_to_my_page(self):
        \"\"\"Navigate to my page.\"\"\"
        self.navigate(self.locators.MY_PAGE_URL)
        logger.info("Navigated to my page")
    
    def click_element(self):
        \"\"\"Click on element.\"\"\"
        self.click(self.locators.ELEMENT)
        logger.debug("Element clicked")
    
    def assert_page_loaded(self):
        \"\"\"Assert page is loaded.\"\"\"
        self.assert_visible(self.locators.HEADER)
        logger.info("My page loaded successfully")
```

### Best Practices

1. **One Method = One Action**: Each method should do one thing
2. **Meaningful Names**: Method names should describe the action clearly
3. **Explicit Waits**: Always wait for elements before interaction
4. **Error Handling**: Use custom exceptions for better debugging
5. **Logging**: Log important actions and state changes
6. **Reusability**: Create helper methods for common operations

---

## Writing Tests

### Test Structure (Arrange-Act-Assert)

```python
def test_user_login(page):
    \"\"\"Test: User can login with valid credentials.\"\"\"
    
    # Arrange - Setup
    login_page = LoginPage(page)
    test_user = "Admin"
    test_password = "admin123"
    
    # Act - Execute
    login_page.enter_username(test_user)
    login_page.enter_password(test_password)
    login_page.click_login_button()
    
    # Assert - Verify
    login_page.assert_dashboard_page_loads()
```

### Test Documentation

```python
def test_create_employee(page):
    \"\"\"
    Test: Create a new employee in PIM.
    
    Preconditions:
    - User is logged in with admin credentials
    
    Steps:
    1. Navigate to PIM
    2. Click Add Employee
    3. Enter employee details
    4. Save employee
    
    Expected Result:
    - Success message displays
    - Employee appears in employee list
    \"\"\"
    # Test code...
```

---

## Fixtures Guide

### Page Fixture

Automatically provided by conftest.py:

```python
def test_something(page):
    # page is automatically created and navigates to base URL
    # screenshots and artifacts are automatically attached on failure
    pass
```

### Context Fixture

Browser context with proper isolation:

```python
def test_something(context, page):
    # New context per test ensures isolation
    pass
```

### Browser Fixture

Single browser instance for all tests (session scope):

```python
# Reused across all tests for performance
# Handles setup/teardown automatically
```

### API Fixtures

For API tests with automatic cleanup:

```python
def test_with_user(page, user_fixture):
    user_id, user_data = user_fixture
    # User automatically deleted after test
```

---

## Allure Reporting

### Generate Reports

```bash
# Generate Allure report
allure generate --clean -o reports/allure-report reports/allure-results

# Open report in web browser
allure open reports/allure-report
```

### Custom Attachments

```python
from helpers.allure_helper import AllureHelper

# Attach screenshot
AllureHelper.attach_screenshot(page, "my_screenshot")

# Attach video
AllureHelper.attach_video("path/to/video.webm", "my_video")

# Attach text
AllureHelper.attach_text("Status", "Test passed successfully")
```

---

## Troubleshooting

### Common Issues

**1. Element Not Found**
```
Check:
- Correct locator in locators.py file
- Element actually exists on page
- Timing issue - add explicit waits
```

**2. Timeout Errors**
```
Solutions:
- Increase DEFAULT_TIMEOUT in config.py
- Check network connectivity
- Verify page load completeness
- Look at screenshots in reports/
```

**3. Flaky Tests**
```
Best Practices:
- Use explicit waits instead of sleep()
- Wait for network to be idle
- Ensure proper element visibility checking
- Use videos to diagnose timing issues
```

**4. Element Not Clickable**
```
Debug Steps:
- Check if element is visible
- Check if element is in viewport
- Look for overlays or modals
- Review videos/screenshots for state
```

---

## Performance Tips

1. **Session-Scoped Browser**: Reuse browser across tests
2. **Function-Scoped Context**: New context per test for isolation  
3. **Explicit Waits**: Better than arbitrary delays
4. **Parallel Execution**: Use pytest-xdist

```bash
# Run tests in parallel (4 workers)
pytest tests/ui/ -n 4
```

---

## Continuous Integration

### GitHub Actions / Jenkins Example

```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    playwright install

- name: Run tests
  run: |
    pytest tests/ui/ -v --alluredir=reports/allure-results
    
- name: Generate reports
  run: allure generate --clean -o reports/allure-report reports/allure-results
```

---

## Standards & Best Practices

### Naming Conventions

- **Test Files**: `test_<feature>.py`
- **Test Methods**: `test_<action>_<expected_outcome>`
- **Page Objects**: `<FeatureName>Page`
- **Locators**: `<ELEMENT_NAME>`
- **Methods**: `action_element()` (verb-noun pattern)

### Code Quality

- All code must have docstrings
- Follow PEP 8 style guide
- No hardcoded values (use config)
- No print() statements (use logger)
- Comprehensive error handling
- Custom exceptions for specific scenarios

### Test Isolation

- Each test must be independent
- Proper setup/teardown
- No test data pollution
- Clean up created resources

---

## Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Allure Documentation](https://docs.qameta.io/allure/)
- [POM Best Practices](https://test-automation.guru/page-object-model/)

---

## Support & Contribution

For issues, questions, or improvements:

1. Check existing documentation
2. Review logs and screenshots in failure artifacts
3. Consult Allure reports for test history
4. Check framework code comments

---

**Framework Version**: 2.0 (Professional Grade)
**Last Updated**: 2024
**Maintenance**: Regular updates for stability and new features
