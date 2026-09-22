import os
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

os.makedirs('deliverables/screenshots', exist_ok=True)
options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1600,1000')

driver = webdriver.Edge(options=options)
try:
    # 1. Landing Page Top
    driver.get('http://localhost:5173/')
    time.sleep(2)
    driver.save_screenshot('deliverables/screenshots/01_landing_page.png')
    print('1. Landing page captured')

    # 1b. Landing Page Features
    driver.execute_script("window.scrollTo(0, 900);")
    time.sleep(1)
    driver.save_screenshot('deliverables/screenshots/01b_landing_features.png')
    print('1b. Landing features captured')

    # 2. Login Page
    driver.get('http://localhost:5173/login')
    time.sleep(1.5)
    driver.save_screenshot('deliverables/screenshots/02_login_page.png')
    print('2. Login page captured')

    # Click Student quick-login
    for b in driver.find_elements(By.TAG_NAME, 'button'):
        if 'student' in b.text.lower():
            b.click()
            break
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(2.5)

    # 3. Student Dashboard
    driver.save_screenshot('deliverables/screenshots/03_student_dashboard.png')
    print('3. Student dashboard captured')

    # 4. Student Chat - Active Q&A
    driver.get('http://localhost:5173/student/chat')
    time.sleep(2)
    chat_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder*="Ask UniAssist"]')
    chat_input.send_keys("What are the hostel in-time rules and regulations?")
    time.sleep(0.5)
    send_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    send_btn.click()
    print('Sent chat query, waiting for AI response...')
    time.sleep(6) # wait for Azure / mock AI response
    driver.save_screenshot('deliverables/screenshots/04_student_chat_active.png')
    print('4. Active student chat captured')

    # 5. Document AI - Storage tab
    driver.get('http://localhost:5173/student/document-ai')
    time.sleep(2)
    driver.save_screenshot('deliverables/screenshots/05_document_ai_storage.png')
    print('5. Document AI storage captured')

    # 5b. Document AI - Instant Q&A tab
    for btn in driver.find_elements(By.TAG_NAME, 'button'):
        if 'instant' in btn.text.lower():
            btn.click()
            time.sleep(1.5)
            break
    driver.save_screenshot('deliverables/screenshots/05b_document_ai_qa.png')
    print('5b. Document AI Instant Q&A captured')

    # 6. Student Complaints
    driver.get('http://localhost:5173/student/complaints')
    time.sleep(2)
    driver.save_screenshot('deliverables/screenshots/06_complaints.png')
    print('6. Complaints captured')

    # 7. Student Profile
    driver.get('http://localhost:5173/student/profile')
    time.sleep(1.5)
    driver.save_screenshot('deliverables/screenshots/07_profile.png')
    print('7. Profile captured')

    # 8. Admin Login & Dashboard
    driver.get('http://localhost:5173/login')
    time.sleep(1.5)
    for b in driver.find_elements(By.TAG_NAME, 'button'):
        if 'admin' in b.text.lower():
            b.click()
            break
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(3)
    driver.save_screenshot('deliverables/screenshots/08_admin_dashboard.png')
    print('8. Admin dashboard captured')

except Exception as e:
    print('Error during capture:', e)
finally:
    driver.quit()

print('All screenshots captured successfully!')
