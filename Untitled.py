#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup as bs
import re
from selenium import webdriver
import pandas as pd


from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#import csv

def create_driver(headless=True, implicit_wait=2):
    """
    # Firefox
    opts = webdriver.firefox.options.Options()
    opts.headless = headless
    #driver = webdriver.Firefox(options=opts)
    """
    opts = webdriver.chrome.options.Options()
    opts.headless = headless
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(implicit_wait)
    return driver

#enter rottentomatoes url, hamilton is used for example
main_url = "https://www.rottentomatoes.com/m/hamilton_2020/reviews"
driver = create_driver(headless=False)
driver.get(main_url)

professor_soup = bs(driver.page_source, "html.parser")

#gets names from driver using bs based on classifier and the tag
def get_names(classifier, name_specific):
    reviewer_names = professor_soup.find_all(classifier, name_specific)
    names = [name.string for name in reviewer_names]
    return names

#gets reviews from driver using bs based on classifier and the tag
def get_reviews(classifier, review_specific):
    movie_review_text = professor_soup.find_all(classifier, review_specific)
    reviews = [review.string for review in movie_review_text]
    return reviews

#guesses gender based on first name based on the online genderize.io api 
def gender_guesser(name_list):
    def gender_guesser_per_ten(name_list_ten):
        #new url for gender guesser website
        gender_guesser_url = "https://api.genderize.io/?name[]="
        
        tot_count = 1
        for name in name_list_ten:
            gender_guesser_url += name
            if tot_count != len(name_list_ten): 
                gender_guesser_url += "&name[]="
                tot_count += 1
                
        gg_driver = create_driver(headless=False)
        gg_driver.get(gender_guesser_url)

        #new html parser
        gg_soup = bs(gg_driver.page_source, "html.parser")

        #creating lists for return statements
        gender_list_final = []
        gender_list_final_accuracy = []

        #get the full text from api and split it up
        gender_list = gg_soup.find("pre")
        gender_list_string = gender_list.string
        gender_list_split = gender_list_string.split("},{")
        gender_percent_split = gender_list_string.split("probability")[1:]

        #find gender from first split
        for split in gender_list_split:
            if "female" in split:
                gender_list_final.append("female")
            elif "male" in split:
                gender_list_final.append("male")
            else:
                gender_list_final.append("unknown")

        #find accuracy from second split and make into a float
        for split in gender_percent_split:
            if split[1:4] == ":0,":
                gender_list_final_accuracy.append(0)
            else:
                out_of_one = float(split[2:6])
                gender_list_final_accuracy.append(out_of_one)
            
        return [gender_list_final, gender_list_final_accuracy]
    
    #divides the list by sections of ten names for the api to parse through
    def ten_split(name_list):
        gen_list_reorg = []
        counter,tot_count = 0, 0
        gen_list_temp = []
        for name in name_list:
            gen_list_temp.append(name)
            counter += 1
            tot_count += 1
            if counter == 10 or tot_count == len(name_list) :
                gen_list_reorg.append(gen_list_temp)
                gen_list_temp = []
                counter = 0 
        return gen_list_reorg
                
    #if more than ten, divides it up, and sends to api by list of tens 
    #WARNING: It will open a new tab for every ten names on list
    if len(name_list) > 10:
        gen_final = []
        gen_final_acc = []
        by_ten = ten_split(name_list)
        
        for each in by_ten:
            temp = gender_guesser_per_ten(each)
            
            gen_final += temp[0]
            gen_final_acc += temp[1]
            
        return [gen_final, gen_final_acc]
            
    else:
        
        return gender_guesser_per_ten(name_list)
            
#gets names from driver
names = get_names("a","unstyled bold articleLink")

#split names into first and last
first_names = []
last_names = []
for name in names:
    name_split = name.split(' ')
    first_names += [name_split[0]]
    last_names += [name_split[1]]

#get reviews
reviews = get_reviews("div", "the_review")

#cleaning up the reviews, getting rid of white space and stuff
new_review = []
for review in reviews:
    new_review_sentence = review[37:-33]
    new_review.append(new_review_sentence)

#gets the gender for each name, but PLS BE WARNED it opens up another tab as well
gender_accuracy = gender_guesser(first_names)

#compiles Data into a Pandas Dataframe

data = {"first name":first_names, "last name": last_names, "text":new_review, "gender":gender_accuracy[0], "gender accuracy":gender_accuracy[1]}
x = pd.DataFrame(data, columns = ["first name", "last name", "text", "gender", "gender accuracy"])

#Use this to display the dataframe if wanted
#print(x)

#dataframe needs to be written to a csv


