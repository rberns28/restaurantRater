# Restaurant Rater
# Author: Ryan Berns
# Date Created: 2017-08-14

from urllib.request import urlopen
from bs4 import BeautifulSoup
import urllib.request
import re
import requests
import pprint
import json
import csv
from twilio.rest import Client

# Information for the yelp API
accountSID = '*******************************'
authToken = '*******************************'
client = Client(accountSID, authToken)

# Phone number used to text users
myTwilioNumber = '+99999999'


# Use a browser emulator so google allows scrapes
class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"
appId ='**************'
appSecret ='************'
data = {'grant_type': 'client_credentials',
        'client_id': appId,
        'client_secret': appSecret}
token = requests.post('https://api.yelp.com/oauth2/token', data=data)
accessToken = token.json()['access_token']
url = 'https://api.yelp.com/v3/businesses/search'
headers = {'Authorization': 'bearer %s' % accessToken}

# Start app and ask for input information from user
print("Welcome to my restaurant rating app!\n")
userName = input("Please enter your name. (First name and first initial of last name):\t")

# App persists user information in a csv.  When a user logs in again, those same preferences are found and do not need to be entered again.
try:
    reader = csv.reader(open(r'C:\localData\userData.csv'))
    userDirectory={}
    for row in reader:
        if len(row) > 0:
            userDirectory[row[0]] = row[1:]
except FileNotFoundError:
    userDirectory={}

if userName in userDirectory:
    print("Welcome back",userName)
    myCellPhone = userDirectory[userName][0]
    googlePref = int(userDirectory[userName][1])
    yelpPref = int(userDirectory[userName][2])
else:
    phoneNumberMessage = str("Hello, "+userName+". Can you please input your mobile number?  Just numbers! (no dashes please)\t")
    myCellPhone = input(phoneNumberMessage)
    googlePref = input("On a scale of 1 - 3 (3 being the best), how much do you value google reviews?\t")

    # Handle errors if user enters invalid scaling for google
    try:
        googlePref = int(googlePref)
    except ValueError:
        googlePref = input("Please enter as a number. (1,2 or 3). Try again:\t")
    if int(googlePref) > 3:
        googlePref = input("You can only choose 1,2 or 3.  how much do you value google reviews?\t")
    elif int(googlePref) < 1:
        googlePref = input("You can only choose 1,2 or 3.  how much do you value google reviews?\t")    

    # Add yelp review value
    yelpPref = input("On a scale of 1 - 3 (3 being the best), how much do you value yelp reviews?\t")
    
    # Handle errors if user enters invalid scaling for yelp
    try:
        yelpPref = int(yelpPref)
    except ValueError:
        yelpPref = input("Please enter as a number. (1,2 or 3). Try again:\t")
    if int(yelpPref) > 3:
        yelpPref = input("You can only choose 1,2 or 3.  how much do you value yelp reviews?\t")
    elif int(yelpPref) < 1:
        yelpPref = input("You can only choose 1,2 or 3.  how much do you value yelp reviews?\t")   

    userValues = str(myCellPhone+" "+str(googlePref)+" "+str(yelpPref)+" ").split()
    userDirectory[userName] = userValues
    with open(r'C:\localData\userData.csv', 'w') as outfile:
        csv_writer = csv.writer(outfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for k,v in userDirectory.items():
            csv_writer.writerow([k] + v)  
# Extract information from Google and Yelp while ensuring we get a rating back
restart="Y"
while restart=="Y":
    restart="N"
    nm = input("What is the name of the restaurant?\t")
    ask = str("What is the location of "+nm+"?\t")
    loct = input(ask)
    print("")
    nmUp=nm.replace(" ","+")
    loctUp = loct.replace(" ","+")
### Google ###
    query = ("https://www.google.com/search?safe=off&q="+nmUp+"+"+loctUp+"+google+review")
    opener = AppURLopener()

    response = opener.open(query)
    soup = BeautifulSoup(response,'html.parser')

    # Rating
    output = soup.find('span', {'class':'_kgd'})

    if output==None:
        print("We can\'t find that restaurant.  Please try again.")
        restart="Y"
    else:
        restart="N"
    # Number of Reviews
    output2 = soup.find('span', {'style': 'color:#777'})
    # Error handling in case the app cannot find the restaurant on google reviews
    try:
        output2Tmp = ''.join(re.findall(r'\d',str(output2.get_text())))
    except AttributeError:
        print('Sorry. We can\'t find that restaurant on google. Please check to make sure you inputted the restaurant correctly.\n')

### YELP ###
    params = {'location': loct,
              'term': nm,
              'limit': '1'
             }

    resp = requests.get(url=url, params=params, headers=headers)

    outputY = resp.json()
    subsetList = outputY['businesses']
    # Error handling in case the app cannot find the restaurant on yelp
    try:
        subsetDict = dict(subsetList[0])
    except IndexError:
        print('Sorry. We can\'t find that restaurant on yelp. Please check to make sure you inputted the restaurant correctly.\n')
        restart="Y"

def yourRating(yelpPref=yelpPref,googlePref=googlePref):
    ratio = float(googlePref/yelpPref)
    googleNum = (float(output.get_text())*float(output2Tmp)*ratio)
    yelpNum = (float(subsetDict['rating'])*float(subsetDict['review_count']))
    den = ((float(output2Tmp)*ratio)+float(subsetDict['review_count']))
    yourRtng = round(((googleNum+yelpNum)/den),2)
    return yourRtng

yourRtng = yourRating()
# Print Output to screen
print("Based on your preferences, our recommended rating for", subsetDict['name'],"is",yourRtng,".\n\n")
print("########## Google ##########")
print("Rating:\t",output.get_text())
print("Total reviews:\t",output2Tmp)
print("")
print("######### Yelp ##########")
print("Rating:\t",subsetDict['rating'])
print("Total reviews:\t",subsetDict['review_count'])
print("")
print("Address:")
for i in subsetDict['location']['display_address']:
    print(i)
print(subsetDict['display_phone'])
if subsetDict['is_closed']==True:
    print("Unfortunately",subsetDict['name'],"closed and no longer exists.") 

# Build Text Output for text message
restaurant_nm = subsetDict['name']
yourRtngFormatted = str(yourRtng)
googleRtng = output.get_text()
yelpRtng = str(subsetDict['rating'])
yelpCnt = str(subsetDict['review_count'])
restaurantPhone = subsetDict['display_phone']
address = ""
for i in subsetDict['location']['display_address']:
    address += str(i+"\n")
txtOutput = str(restaurant_nm+"\nRecommended Rating:\t"+yourRtngFormatted+"\nGoogle\n"+"Rating:\t"+googleRtng+"\nTotal reviews:\t"+output2Tmp+"\n\nYelp\n"+"Rating:\t"+yelpRtng+"\nTotal reviews:\t"+yelpCnt+"\n\n"+address+"\n"+restaurantPhone)

# Send Text Message
try:
    message = client.messages.create(body=txtOutput, from_=myTwilioNumber, to=myCellPhone)
except:
    print("If the app creator wasn\'t so cheap, you would\'ve been texted this information to your mobile phone as well.\nHope you enjoy your meal!")
