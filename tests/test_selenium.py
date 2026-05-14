import pytest
import multiprocessing
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from app import app, db

PORT = 5005

def run_server():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        # Seed test data if needed
    app.run(port=PORT, use_reloader=False)

@pytest.fixture(scope="module")
def server():
    # Start the Flask app in a separate process
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    time.sleep(2)  # Give the server a moment to start
    
    yield
    
    # Terminate the server process after tests finish
    server_process.terminate()
    server_process.join()

@pytest.fixture(scope="module")
def browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()

def test_home_page_title(server, browser):
    """Test 1: Check the home page title"""
    browser.get(f"http://localhost:{PORT}/")
    assert "LowResGram" in browser.title

def test_navigation_to_login(server, browser):
    """Test 2: Navigate from home to login page"""
    browser.get(f"http://localhost:{PORT}/")
    login_link = browser.find_element(By.LINK_TEXT, "Log In")
    login_link.click()
    
    # Wait for URL to change to login
    WebDriverWait(browser, 10).until(EC.url_contains("/login"))
    assert "Log in inside your universe." in browser.page_source or "Sign in" in browser.page_source

def test_invalid_login(server, browser):
    """Test 3: Attempt to login with invalid credentials"""
    browser.get(f"http://localhost:{PORT}/login")
    
    username_input = browser.find_element(By.NAME, "username")
    password_input = browser.find_element(By.NAME, "password")
    
    username_input.send_keys("nonexistentuser")
    password_input.send_keys("wrongpassword")
    password_input.send_keys(Keys.RETURN)
    
    # Wait for flash message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Invalid username or password')]"))
    )
    assert "Invalid username or password" in browser.page_source

def test_successful_signup(server, browser):
    """Test 4: User sign up flow"""
    browser.get(f"http://localhost:{PORT}/signup")
    
    username_input = browser.find_element(By.NAME, "username")
    email_input = browser.find_element(By.NAME, "email")
    password_input = browser.find_element(By.NAME, "password")
    
    username_input.send_keys("seleniumtest")
    email_input.send_keys("selenium@test.com")
    password_input.send_keys("password123")
    password_input.send_keys(Keys.RETURN)
    
    # Should redirect to interests
    WebDriverWait(browser, 10).until(EC.url_contains("/interests"))
    assert "interests" in browser.current_url.lower()

def test_draw_page_access_after_login(server, browser):
    """Test 5: Check if logged-in user can access drawing canvas"""
    # Assuming user is already logged in from previous test,
    # let's just go to /draw
    browser.get(f"http://localhost:{PORT}/draw")
    
    # Wait for canvas to load
    canvas = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "canvas"))
    )
    assert canvas is not None
