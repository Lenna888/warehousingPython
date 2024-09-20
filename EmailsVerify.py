"""
ACTIVITY EMAIL VERIFICATION APIS CONSUMPTION
Author: Laura E. Latorre
Creation Date: 18/09/2024
Last Modified: 19/09/2024

Use of APIs

Dependencies:
    - Module: pymongo.mongo_client, requests and json
"""

import time

from configMongo import config
from pymongo.mongo_client import MongoClient
import requests, json

"""
Connection string allowing access to the database.

    URI:‘mongodb+srv://lelp990720:B7BWgqBdQodOXRwu@atlascluster.mt0t5.mongodb.net/?retryWrites=true&w=majority&appName=AtlasCluster’,
    DATABASE:‘email_apis’,
    COLLECTION:‘email_verified’
"""

#MongoAtlas configuration parameters
clientConnection =MongoClient(config['URI'])
databaseAccess=clientConnection[config['DATABASE']]
collectionAccess = databaseAccess[config['COLLECTION']]



class EmailDataResearch:
    """
    Definition of the EmailDataResearch class
    """
    pass

    def __init__(self):
        """
        References to the objects being manipulated, in this case the list of emails that are retrieved
        from the government page and the emails verified in both the email verification API and the in the GitHub API
        """
        self.emailsList=[]
        self.emailsVerified=[]
        self.emailsGitHub=[]

    def getEmail(self):
        """
        Method for obtaining emails from the Government's free data API.
        """
        #Data is obtained from a get method, in this case a data limit of 40 is used.
        responseEmail = requests.get("https://www.datos.gov.co/resource/jtnk-dmga.json?$limit=40")
        responseJson= responseEmail.json()
        #For loop that iterates over the list of emails obtained from the JSON, each of those emails is added to the emailList.
        for email in range(len(responseJson)):
            self.emailsList.append(responseJson[email]["email_address"])
            print(responseJson[email]["email_address"])


    def validateEmails(self):
        """
        Method for verifying emails in Apilayer.
        """
        print(self.emailsList)
        api_key="nGuYnmo83j9rlnB41XyHoyDjL04ynmj3"
        for email in self.emailsList:
            responseEmailVerified = requests.get(f"https://api.apilayer.com/email_verification/check?email={email}&apikey={api_key}")
            emailsJson=responseEmailVerified.json()
            self.emailsVerified.append(email) if emailsJson["disposable"] == "true" and emailsJson["smtp_check"] == "true" else None
            print(f"Email: {emailsJson["email"]} \nSMTP Check: {emailsJson["smtp_check"]} \nDisposable: {emailsJson["disposable"]}")
            repos = self.checkGithub(emailsJson["email"])
            if repos:
                self.emailsGitHub.append({"email": emailsJson["email"], "repos": repos})
                print(f"Repositorios disponibles: {self.checkGithub(emailsJson["email"])}")
            else:
                print(f"No GitHub account found for {emailsJson['email']}")


    @staticmethod
    def checkGithub(email):
        """
        Checks if the email's username part is associated with a GitHub account.
        """
        username = email.split('@')[0]  # Assume the part before "@" is the GitHub username
        url = f"https://api.github.com/users/{username}/repos"
        responseGithub = requests.get(url)
        time.sleep(1)  # Avoid exceeding API rate limits
        repos = responseGithub.json()  # Parse the GitHub response
        if responseGithub.status_code == 200 and repos:
            print(f"GitHub Repos for {username}: {[repo['name'] for repo in repos]}")
            return [repo['name'] for repo in repos]  # Return the names of the repos
        return None  # Return None if no repos are found

    def saveData(self):
        """
        Method for storing the data in MongoDB Atlas.
        """
        for email in self.emailsList:
            document = {
                'email': email,
                'verified': email in self.emailsVerified,
                'repos': next((e['repos'] for e in self.emailsGitHub if e['email'] == email), None)
            }
            responseSave = collectionAccess.insert_one(document)
            print(f"Data saved for {email}. Document ID: {responseSave.inserted_id}")


try:
    test = EmailDataResearch()
    test.getEmail()
    test.validateEmails()
    test.saveData()
except Exception as e:
        print(e)
