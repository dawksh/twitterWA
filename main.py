from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
import tweepy
from deta import Deta
import os

app = Flask(__name__)
authh = Deta().Base("authtw")
db = Deta().Base("watw")
@app.route('/bot', methods=['POST'])
def bot():

    auth = tweepy.OAuthHandler(os.getenv('key'), os.getenv('secret'))
    incoming_msg = request.values.get('Body').lower()
    sender = request.values.get('From')
    resp = MessagingResponse()
    msg = resp.message()
    print(incoming_msg)
    responded = False
    s = db.get(sender)
    auth.set_access_token(s["access_token"], s["secret"])
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser()) 
    if incoming_msg[:6] == "tweet ":
        if len(incoming_msg[6:].split("///")) > 1:
                y = incoming_msg[6:].split("///")
                x = api.update_status(status=y[0])
                status = x
                print(status)
                i = 1
                while i <= len(y):
                    status = api.update_status(status=y[1], in_reply_to_status_id=status["id"])
                    i += 1
                msg.body("""Tweeted the thread, great work!
                
                Here it is: https://twitter.com/""" + x["user"]["screen_name"] + "/" + x["id_str"])           
        elif len(incoming_msg[6:]) > 280:
                msg.body("""The message you wanted to tweet has more than 280 characters (""" + str(len(incoming_msg[6:])) + """)
                
Please break down your message into a thread by using "///" to indicate beginning of each new tweet, or reduce the length of the original one.""")                
        
        else:    
            print("tweeting...")  
            x = api.update_status(status=incoming_msg[5:])
            msg.body("""Tweeted! https://twitter.com/""" + x["user"]["screen_name"] + "/status/" + x["id_str"] + """
            
Like this bot? Buy me a coffee at https://buymeacoffee.com/ayshptk""")
            responded = True

    if incoming_msg[:4] == "auth":
        r = auth.get_authorization_url()
        authh.put({"rt": r[52:]}, sender)
        msg.body("Step 1: Go to the following URL and authorise :" + r + " After, that, send CODE followed by the code you get")
        responded = True

    if incoming_msg[:5] == "code ":
        auth.request_token["oauth_token"] = authh.get(sender)["rt"]
        auth.request_token["oauth_token_secret"] = incoming_msg[5:]
        verifier = incoming_msg[5:]
        auth.get_access_token(str(verifier))
        db.put({"access_token" : auth.access_token, "secret" : auth.access_token_secret}, sender)
        msg.body("""Account was connected! 
                
To tweet, send the word 'tweet' followed by a space and then your tweet.
                
Like this bot? Buy me a coffee at https://buymeacoffee.com/ayshptk""")   
        responded = True
    if not responded:
        if len(incoming_msg) == 7:
            try:
                int(incoming_msg)
                auth.request_token["oauth_token"] = authh.get(sender)["rt"]
                auth.request_token["oauth_token_secret"] = incoming_msg
                auth.get_access_token(str(incoming_msg))
                db.put({"access_token" : auth.access_token, "secret" : auth.access_token_secret}, sender)
                msg.body("""Account was connected! 
                
To tweet, send the word 'tweet' followed by a space and then your tweet.
                
Like this bot? Buy me a coffee at https://buymeacoffee.com/ayshptk""")                             
            except:
                msg.body("Sorry, an error occured. Send a quick text to me at https://wa.me/+919987054354 and I'll fix it ASAP, thanks!") 
    return str(resp)


if __name__ == '__main__':
    app.run()