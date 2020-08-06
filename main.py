from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup as bs
import re
from typing import List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv
from datetime import datetime

from pprint import pprint

PATH = r'C:\Users\jsonn\Documents\Python\selenium\chromedriver.exe' #needed to put r to not get unicode error, this line is from that youtube tutorial

GRADING_SCALE = {4.0:'A', 3.7: 'A-',
                3.3: 'B+', 3.0: 'B', 2.7: 'B-', 
                2.3: 'C+', 2: 'C', 1.7:'C-',
                1.3:'D+', 1:'D', 0.7:'D-', 
                0:'F'}
GRADING_SCALE_REVERSED = {letter:num for num, letter in GRADING_SCALE.items()}

class Professor:
    """Professor"""
    curr_id = 0
    csv_header = ['id', 'last_name', 'first_name', 'department', 'url']

    def __init__(self, last_name: str, first_name: str, department: str , url: str):
        self.id = Professor.curr_id
        Professor.curr_id += 1
        self.last_name = last_name
        self.first_name = first_name
        self.department = department
        self.url = url

    def to_csv_row(self):
        return [self.id, self.last_name, self.first_name, self.department, self.url]

    def __repr__(self):
        return str(self.last_name + ", " + self.first_name)

class Review:
    """Review"""
    curr_id = 0
    csv_header = ['id', 'professor_id', 'content']

    def __init__(self, professor_id: int, content: str, sentiment: dict, attrs: dict):
        assert(all(key in sentiment for key in ['pos', 'compound', 'neg', 'neu']))

        self.id = Review.curr_id
        Review.curr_id += 1

        self.professor_id = professor_id
        self.content = content
        self.sentiment = sentiment
        self.attrs = attrs

    def to_csv_row(self):
        return [self.id, self.professor_id, self.content]

    def __repr__(self):
        return str(self.content)

def create_driver(headless: bool=True, implicit_wait: int=2) -> webdriver:
    """Creates and returns a Selenium driver object"""
    # Firefox
    opts = webdriver.firefox.options.Options()
    opts.headless = headless
    driver = webdriver.Firefox(options=opts)
    """
    opts = webdriver.chrome.options.Options()
    opts.headless = headless
    driver = webdriver.Chrome(PATH, options=opts)
    driver.implicitly_wait(implicit_wait)
    """
    return driver

def average_grade(grades: List[str]) -> float:
    """Given a list of grades as numbers (i.e. A is a 4) returns the average grade as a letter.
    This function rounds down.
    average_grade([4.3,2.3,4,3.7,3.3]), where the mean is 3.52, rounds up to an A-
    average_grade([4,3,3,4,4,2.7]), where the mean is 3.449, rounds down to a b+"""
    number_grade = round(sum(grades) / len(grades), 1)
    for grade in GRADING_SCALE:
        if number_grade >= grade -.2: #starts with a, so if the average grade is >= 3.8
            return GRADING_SCALE[grade]
        
def grade_to_number(letter: str) -> float:
    """Converts a letter grade to a float"""
    if letter == "A+": #this is not really right but it's fine, there's no difference between the two
        letter = "A"
    return GRADING_SCALE_REVERSED[letter]

def grade_isolator(line: str, grades: List[str]):
    """make grades list"""
    if "Grade" in line:
        parts = line.split("Grade: ") 
        moreparts = parts[1].split("Text")
        grades.append(moreparts[0])
    else:
        grades.append('Z')  
        
def avg(grades: List[str]):
    """get average grade"""
    glist = []
    for grade in grades:
        if grade in GRADING_SCALE.values() or grade == "A+":
            glist.append(grade_to_number(grade))
    return average_grade(glist) if glist else 0 #if there were no grades 

def get_professors(main_url: str = "https://www.ratemyprofessors.com/search.jsp?queryBy=schoolId&schoolName=University+of+California+Berkeley&schoolID=1072&queryoption=TEACHER&sort=alphabetical", 
                    department_cookies: List[str] = ["Computer Science", "Electrical Engineering"]) -> List[Professor]:
    """
    Returns a list of professors in certain department(s)
    
    NOTE: Assumes UC Berkeley and EECS departments
    """
    driver = create_driver(headless=True)
    professor_id = 0
    professors = []
    try:
        # Set cookie for specific department
        driver.get("https://www.ratemyprofessors.com/robots.txt")
        department_cookies = ["Computer Science", "Electrical Engineering"]
        first_run = True
        for cookie in department_cookies:
            driver.add_cookie({"name": "department", "value": cookie, "path": "/", })
            driver.get(main_url)

            if first_run:
                # Click cookie button
                button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "big-close")))
                driver.execute_script("arguments[0].click();", button)
                first_run = False

            # Click load more button
            try:
                while True:
                    button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".progressbtnwrap > .content")))
                    driver.execute_script("arguments[0].click();", button)
            except:
                pass

            # Get professor info
            soup = bs(driver.page_source, "html.parser")
            professors_lis = soup.find_all('li', {'id': re.compile(r'my-professor-[\d]+?')})
            for professor_li in professors_lis:
                url = 'https://www.ratemyprofessors.com' + professor_li.find_all('a', {'href': re.compile(r'/ShowRatings[^"]+?')})[0].attrs['href'].split("&showMyProfs")[0]
                name = re.compile("\\d").split(professor_li.find_all('span', {'class': 'name'})[0].text, 1)[0]
                last_name, first_name = [name.strip() for name in name.split(", ")]
                professors.append(Professor(last_name, first_name, cookie, url))
                professor_id += 1
    except Exception as e:
        driver.quit()
        raise(e)
    driver.quit()
    return professors

def get_reviews(professor: Professor) -> List[Review]:
    """Returns a list of reviews for a certain professor"""
    driver = create_driver(headless=True)
    try:
        driver.get(professor.url)
        # Click cookie button
        button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "CCPAModal__StyledCloseButton-sc-10x9kq-2")))
        driver.execute_script("arguments[0].click();", button)
        #Click load more button
        try:
            while True:
                button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CLASS_NAME, "Buttons__BlackButton-sc-19xdot-1")))
                driver.execute_script("arguments[0].click();", button)
        except:
            pass
        professor_soup = bs(driver.page_source, "html.parser")
    except Exception as e:
        driver.quit()
        raise(e)
    driver.quit()

    analyzer = SentimentIntensityAnalyzer()
    reviews = []
    for rating in professor_soup.select("ul#ratingsList > li"):
        content = rating.find_all('div', {'class': re.compile(r'Comments__StyledComments-.+-\d')})
        if len(content) != 0: # Sometimes, they're ad div's
            attrs = {}
            content = content[0].text
            rating_values = rating.find_all('div', {'class': re.compile(r'RatingValues__RatingValue-sc-.+-\d')})
            attrs['quality'] = float(rating_values[0].text)
            attrs['difficulty'] = float(rating_values[1].text)
            attrs['class'] = rating.find('div', {'class': re.compile(r'RatingHeader__StyledClass-sc-.+-\d')}).text
            likes_dislikes = rating.find_all('div', {'class': re.compile(r'RatingFooter__HelpTotal-.+-\d')})
            attrs['likes'] = int(likes_dislikes[0].text)
            attrs['dislikes'] = int(likes_dislikes[1].text)
            attrs['emotion'] = rating.find('div', {'class': re.compile(r'EmotionLabel__StyledEmotionLabel-sc-.+-\d')}).text[1:]
            date_str = re.sub(r'(st|nd|rd|th)', '', rating.find('div', {'class': re.compile(r'TimeStamp__StyledTimeStamp-sc-.+-\d')}).text)
            attrs['date'] = datetime.strptime(date_str, '%b %d, %Y')
            rating_tags = rating.find_all('span', {'class': re.compile(r'Tag-.+-\d')})
            attrs['rating_tags'] = [rating_tag.text for rating_tag in rating_tags]

            meta_items = rating.find_all('div', {'class': re.compile(r'MetaItem__StyledMetaItem-.+-\d')})
            meta_items_types = {'for credit': 'for_credit', 'attendance': 'attendance', 'would take again': 'would_take_again', 'grade': 'grade', 'textbook': 'textbook'}
            for item in meta_items:
                for meta_item_type in meta_items_types:
                    if meta_item_type in item.text.lower():
                        attrs[meta_items_types[meta_item_type]] = ' '.join(item.text.split()[len(meta_item_type.split()):]).lower()
                        break
            reviews.append(Review(professor.id, content, analyzer.polarity_scores(content), attrs))
    return reviews

def filter(reviews: List[Review], courses_wanted: List[str] = None, courses_not_wanted: List[str] = None) -> (List[Review], List[Review]):
    """Takes in a list of reviews and returns (kept_reviews, discarded_reviews)"""
    # TODO: FIXME
    kept_reviews, discarded_reviews = reviews[:], []
    return (kept_reviews, discarded_reviews)

def main():
    pass

if __name__ == "__main__":
    professors = get_professors()
    reviews = get_reviews(professors[0])
    # Print example review (first review for John Denero)
    pprint([reviews[0].content, reviews[0].sentiment, reviews[0].attrs])