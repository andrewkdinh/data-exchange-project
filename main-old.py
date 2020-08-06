from bs4 import BeautifulSoup as bs
import re
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from typing import List

PATH = r'C:\Users\jsonn\Documents\Python\selenium\chromedriver.exe' #needed to put r to not get unicode error, this line is from that youtube tutorial

GRADING_SCALE = {4.0:'A', 3.7: 'A-',
                3.3: 'B+', 3.0: 'B', 2.7: 'B-', 
                2.3: 'C+', 2: 'C', 1.7:'C-',
                1.3:'D+', 1:'D', 0.7:'D-', 
                0:'F'}
GRADING_SCALE_REVERSED = {letter:num for num, letter in GRADING_SCALE.items()}

def main(professor_url: str, courses_wanted: List[str], courses_not_wanted: List[str]):
    driver = create_driver(headless=False)
    try:
        driver.get(professor_url)
        # Click cookie button
        button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "FullPageModal__StyledCloseButton-sc-17feuxe-1")))
        driver.execute_script("arguments[0].click();", button)
        #Click load more button
        try:
            while True:
                button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CLASS_NAME, "Buttons__BlackButton-sc-19xdot-1")))
                driver.execute_script("arguments[0].click();", button)
        except:
            pass
        professor_soup = bs(driver.page_source, "html.parser")
    except:
        driver.quit()
        raise(Exception)
    driver.quit()

    # Scrape reviews, ratings, and difficulties
    course_names = professor_soup.find_all("div","RatingHeader__StyledClass-sc-1dlkqw1-2 hBbYdP")
    names = [name.string for name in course_names][::2]
    course_reviews = professor_soup.find_all("div", "Comments__StyledComments-dzzyvm-0 dEfjGB")
    reviews = [review.string for review in course_reviews][1:] #we don't want most helpful rating because it's repeated 
    print("Total number of reviews:", len(reviews))
    #print(len(names), len(reviews)) i need to figure out why reviews is half the length of names 
    #the length of names is resolved. the source code for some reason had stuff listed twice
    course_ratings_difficulty = professor_soup.find_all("div", re.compile("RatingValues__RatingValue-sc-6dc747-3"))
    #ratingvalues with 747-3 are course rating and difficulty
    ratings, difficulties = [rating.string for rating in course_ratings_difficulty[::2]], [difficulty.string for difficulty in course_ratings_difficulty[1::2]]
    
    # Scrape likes, dislikes, timestamps
    likes_and_dislikes = professor_soup.find_all("div", "RatingFooter__HelpTotal-ciwspm-2 kAVFzA")
    likes_and_dislikes = [int(like.text) for like in likes_and_dislikes][2:]
    #print(len(likes_and_dislikes)/2)
    like_dislike_dict = {}
    for review in reviews:
        like_dislike_dict[review] = likes_and_dislikes[:2]
        like_dislike_dict[review].append(sum(likes_and_dislikes[:2]))
        likes_and_dislikes = likes_and_dislikes[2:]   
    #dictionary values show number of likes, dislikes, and total votes per review
    review_times = professor_soup.find_all('div', "TimeStampStyledTimeStamp-sc-9q2r30-0 bXQmMr RatingHeaderRatingTimeStamp-sc-1dlkqw1-3 BlaCV")
    times = [review.text for review in review_times][::2]

    # Scrape grades
    divs_soup = professor_soup.find_all("div", "CourseMeta__StyledCourseMeta-x344ms-0")
    divs = [div.text for div in divs_soup]
    grades_list = []

    # All the stuff
    average_rating, average_difficulty, index, ratings_list, difficulties_list = 0, 0, 0, [], [] #by course wanted for if filter_type true
    ratings_count = {x:0 for x in range(1,6)}
    difficulty_count = {x:0 for x in range(1,6)}

    if courses_wanted: #because the other option was "" #some implicit booleanness
        for name, review, rating, difficulty in zip(names, reviews, ratings, difficulties):
            #print(name)
            if any([name in course for course in courses_wanted]):
                #print(review, rating, difficulty, '\n')
                ratings_list.append(rating)
                difficulties_list.append(difficulty)
                if float(rating) in ratings_count:
                    ratings_count[float(rating)] +=1
                else:
                    ratings_count[float(rating)] = 1
                if float(difficulty) in difficulty_count:
                    difficulty_count[float(difficulty)] +=1
                else:
                    difficulty_count[float(difficulty)] = 1
                average_rating += float(rating)
                average_difficulty += float(difficulty)
                index +=1
        for index, div in enumerate(divs):
            if any([names[index] in course for course in courses_wanted]):
                grade_isolator(div, grades_list)
    else: #for filtering out courses
        for name, review, rating, difficulty in zip(names, reviews, ratings, difficulties):
            #print(name)
            if not any([name in course for course in courses_not_wanted]):# i.e. class should NOT be CS61A filtered
                #print(review, rating, difficulty, '\n')
                ratings_list.append(rating)
                difficulties_list.append(difficulty)
                if float(rating) in ratings_count:# or difficulty in difficulty_count:
                    ratings_count[float(rating)] +=1
                else:
                    ratings_count[float(rating)] = 1
                if float(difficulty) in difficulty_count:
                    difficulty_count[float(difficulty)] +=1
                else:
                    difficulty_count[float(difficulty)] = 1
                average_rating += float(rating)
                average_difficulty += float(difficulty)
                index +=1   
        for index, div in enumerate(divs):
            if not any([names[index] in course for course in courses_not_wanted]):
                grade_isolator(div, grades_list)
    try:
        print("Average rating under filters: {} \nAverage difficulty under filters: {}".format(average_rating/index, average_difficulty/index))
        print("Max/min rating under filters: {}, {} \nMax/min difficulty under filters: {}, {}".format(max(ratings_list), min(ratings_list), max(difficulties_list), min(difficulties_list)))
    except ZeroDivisionError:
        pass
    print("Average grade: {}".format(avg(grades_list)))

    # Gender classifiers
    gender = {0:0, 1:0 } #0 female, 1 male
    she_series, he_series = ('she','her','hers'),("he","him","his")
    for review in [review.lower() for review in reviews]:
        for word in review.split():
            if word in she_series:
                #print(word)
                gender[0] +=1
            if word in he_series:
                #print(word)
                gender[1] +=1
    if gender[0] == gender[1]:
        print("gender inconclusive")
    else:
        reverse = {val: key for key, val in gender.items()}
        print("gender: {}".format(reverse[max(reverse.keys())]))

def create_driver(headless=True, implicit_wait=2):
    """
    Creates and returns a Selenium driver object
    """
    """
    # Firefox
    opts = webdriver.firefox.options.Options()
    opts.headless = headless
    driver = webdriver.Firefox(options=opts)
    """
    opts = webdriver.chrome.options.Options()
    opts.headless = headless
    driver = webdriver.Chrome(PATH, options=opts)
    driver.implicitly_wait(implicit_wait)
    return driver

def average_grade(grades: List[str]) -> float:
    """given a list of grades as numbers (i.e. A is a 4) returns the average grade as a letter.
    This function rounds down.
    average_grade([4.3,2.3,4,3.7,3.3]), where the mean is 3.52, rounds up to an A-
    average_grade([4,3,3,4,4,2.7]), where the mean is 3.449, rounds down to a b+"""
    number_grade = round(sum(grades) / len(grades), 1)
    for grade in GRADING_SCALE:
        if number_grade >= grade -.2: #starts with a, so if the average grade is >= 3.8
            return GRADING_SCALE[grade]
        
def grade_to_number(letter: str) -> float:

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

if __name__ == "__main__":
    professor_url = "https://www.ratemyprofessors.com/ShowRatings.jsp?tid=1621181"
    courses_wanted = input("Enter a comma-delimited list of specific classes to look for, otherwise leave blank: ").split(",")
    courses_wanted = [] if courses_wanted == [''] else courses_wanted
    courses_not_wanted = input("Enter a comma-delimited list of specific classes to avoid, otherwise leave blank: ").split(",")
    courses_not_wanted = [] if courses_wanted == [''] else courses_wanted

    main(professor_url, courses_wanted, courses_not_wanted)
