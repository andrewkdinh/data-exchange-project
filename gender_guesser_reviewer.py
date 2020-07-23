"""This will take the gender of the reviewer (cell 2) and the review itself (cell 7). It will paste the review
into http://www.hackerfactor.com/GenderGuesser.php#Analyze. Then, it will get the verdict. If the verdict was right (using cell 2), then 
we add increment some number and then take the average after we do this for all of the reviews. """

"""part 1: getting the info from cell 2 and cell 7 for each person
ze and jacob"""
import csv

prof_reviews = open('Professor Review Survey (Responses) - Form Responses 1.csv')
reader = csv.DictReader(prof_reviews)
#print(reader)
data = []
for row in reader:
#	data[row["What is your gender?"]] = [row["Write a review of the professor."]]
    data.append((row["What is your gender?"], row["Write a constructive and honest review of the professor."]))
print(data)
"""part 2: putting each (review) individually into hackerfactor.com 
The stuff coming in will be a list of (reviewer's gender, review)
positive = male, negative = female for formal and informal dictionary """
formal_check = [] #to see if either formal or informal is more accurate 
informal_check = [] #for zeros and ones 
formal_dict = {}
informal_dict = {}
formal_dict['a']= 6
formal_dict['above']= 4
formal_dict['and']= -4
formal_dict['are']= 28
formal_dict['around']= 42
formal_dict['as']= 23
formal_dict['at']= 6
formal_dict['be']= -17
formal_dict['below']= 8
formal_dict['her']= -9
formal_dict['hers']= -3
formal_dict['if']= -47
formal_dict['is']= 8
formal_dict['it']= 6
formal_dict['many']= 6
formal_dict['me']= -4
formal_dict['more']= 34
formal_dict['myself']= -4
formal_dict['not']= -27
formal_dict['said']= 5
formal_dict['she']= -6
formal_dict['should']= -7
formal_dict['the']= 7
formal_dict['these']= 8
formal_dict['to']= 2
formal_dict['was']= -1
formal_dict['we']= -8
formal_dict['what']= 35
formal_dict['when']= -17
formal_dict['where']= -18
formal_dict['who']= 19
formal_dict['with']= -52
formal_dict['your']= -17

informal_dict['actually']= -49
informal_dict['am']= -42
informal_dict['as']= 37
informal_dict['because']= -55
informal_dict['but']= -43
informal_dict['ever']= 21
informal_dict['everything']= -44
informal_dict['good']= 31
informal_dict['has']= -33
informal_dict['him']= -73
informal_dict['if']= 25
informal_dict['in']= 10
informal_dict['is']= 19
informal_dict['like']= -43
informal_dict['more']= -41
informal_dict['now']= 33
informal_dict['out']= -39
informal_dict['since']= -25
informal_dict['so']= -64
informal_dict['some']= 58
informal_dict['something']= 26
informal_dict['the']= 17
informal_dict['this']= 44
informal_dict['too']= -38
informal_dict['well']= 15

formal_two = [] #list of inconclusive guesses
def formal_guess(review):
	"""score review formally. 
	"""
	score = 0
	for word in [word.lower() for word in review.split()]:
		if word in formal_dict:
			score += formal_dict[word]
	if score > 0: 
		return "Male"
	if score < 0: 
		return "Female"
	else:
		formal_two.append(2)

informal_two = []
def informal_guess(review):
	score = 0
	for word in [word.lower() for word in review.split()]:
		if word in informal_dict:
			score += informal_dict[word]
	if score > 0: 
		return "Male"
	if score < 0: 
		return "Female"
	else:
		informal_two.append(2)

for gender, review in data:
	if formal_guess(review) == gender:
		formal_check.append(1)
	else:
		formal_check.append(0)
	if informal_guess(review) == gender:
		informal_check.append(1)
	else:
		informal_check.append(0)

"""part 3: calculate average of rights and wrongs (finding accuracy of the dictionary)"""
formal_accuracy, informal_accuracy = sum(formal_check) / len(formal_check), sum(informal_check) / len(informal_check)
print(formal_accuracy, informal_accuracy, "there were {} formal unknowns and {} informal unknowns".format(len(formal_two),len(informal_two)))
