# Creates a csv with a list of professors for a specific department

from bs4 import BeautifulSoup as bs
import re
from selenium import webdriver
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import csv

def create_driver(headless=True, implicit_wait=2):
    """
    # Chrome
    opts = webdriver.chrome.options.Options()
    opts.headless = headless
    driver = webdriver.Chrome(options=opts)
    """
    opts = webdriver.firefox.options.Options()
    opts.headless = headless
    driver = webdriver.Firefox(options=opts)

    driver.implicitly_wait(implicit_wait)
    return driver

def main():
    # Assumes that school is UC Berkeley
    main_url = "https://www.ratemyprofessors.com/search.jsp?queryBy=schoolId&schoolName=University+of+California+Berkeley&schoolID=1072&queryoption=TEACHER&sort=alphabetical"
    driver = create_driver(headless=True)
    try:
        driver.get(main_url)

        # Click cookie button
        button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "big-close")))
        driver.execute_script("arguments[0].click();", button)

        # Click load more button
        """
        try:
            while True:
                button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".progressbtnwrap > .content")))
                driver.execute_script("arguments[0].click();", button)
        except:
            pass
        """

        # Get professor info
        soup = bs(driver.page_source, "html.parser")
        professors_lis = soup.find_all('li', {'id': re.compile(r'my-professor-[\d]+?')})
        professors = []
        for professor_li in professors_lis:
            url = 'https://www.ratemyprofessors.com' + professor_li.find_all('a', {'href': re.compile(r'/ShowRatings[^"]+?')})[0].attrs['href'].split("&showMyProfs")[0]
            name = re.compile("(?<!^)\\s+(?=\\d)(?!.\\s)").split(professor_li.find_all('span', {'class': 'name'})[0].text)[0]
            lastName, firstName = name.split(", ")
            # professors.append({'first_name': firstName, 'last_name': lastName, 'url': url})
            professors.append([firstName, lastName, url])

        # Write to csv
        header = ['first_name', 'last_name', 'url']
        with open('professors.csv', 'wt') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(header)
            csv_writer.writerows(professors)
    except:
        pass
    driver.quit()

if __name__ == "__main__":
    main()