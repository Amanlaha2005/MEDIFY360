from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

CHROME_DRIVER_PATH = r"C:\Users\amanl\Downloads\chromedriver-win64\chromedriver.exe"

options = Options()
options.add_argument("--user-data-dir=C:\\selenium\\ChromeProfile")  # saves login
options.add_argument("--profile-directory=Default")

service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://web.whatsapp.com/")
print("✅ Chrome opened successfully! Scan QR if needed.")
