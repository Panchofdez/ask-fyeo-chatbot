from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up headless Chrome browser
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Open the website
    driver.get("https://ask-fyeo.streamlit.app")
    time.sleep(3)  # Wait for page to load

    # Click the button (Modify selector accordingly)
    buttons = driver.find_element(By.TAG_NAME, "button")
    for button in buttons:
        if button.is_displayed():  # Ignore hidden buttons
            button.click()
            print("Button clicked successfully!")
            break

    

finally:
    # Close browser
    driver.quit()
