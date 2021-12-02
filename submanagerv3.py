

# Subreddit Manager v.3  by u/BuckRowdy.

#  Added ability to add usernotes upon mod actions. 

# This bot manages your unmoderated queue and reports queue.
# It approves or removes posts according to an algorithm.



# Import lots of modules

import sys
import config
import time
import praw
from time import localtime 
from datetime import datetime as dt, timedelta as td, date
import logging
import traceback
import pmtw


### Define variables and set up logging.

#Create and configure logger
logging.basicConfig(filename="/home/pi/bots/unmod/std.log",
                    format='%(asctime)s %(message)s', filemode='w')

#Create an object
logger=logging.getLogger()

#Set the threshold of logger to INFO
logger.setLevel(logging.INFO)

# Define the subreddit that you are working on.
sub_name = 'mod'

# Number of seconds to sleep between scans (3600 = 1 hour)
sleep_seconds = 300 


# Read the mod list from r/mod from a separate function.
q = open("/home/pi/bots/submanager/modList.txt", "r") 
modList = q.read()
q.close()   

######################################

###  Set up functions.


###  Defines the reddit login function
def redditLogin():

    print('Subreddit Manager is starting up - v.3')
    time.sleep(1)
    print('Connecting to reddit...')
    
    try:
        reddit = praw.Reddit(   user_agent = 'Subreddit Manager Bot v.3 by u/buckrowdy',
                                username = config.username,
                                password = config.password,
                                client_id = config.client_id,
                                client_secret = config.client_secret)


    except Exception as e:
        print(f'\t### ERROR - Could not login.\n\t{e}')

    print(f'Logged in as: {reddit.user.me()}')
    return reddit



### Define time functions for getting timestamps needed as a reference.
def printCurrentTime():
    currentSysTime = time.localtime()
    print('      ')
    print(time.strftime('%a, %B %d, %Y | %H:%M:%S', currentSysTime))



###  Fetch submissions in the unmoderated queue.
def getLatestSubmissions(subreddit):

    print('     ')
    print(f'Starting up...')
    print('------------------------------------------------------------------------')
    submissions = subreddit.mod.unmoderated(limit=1000)
    return submissions


###  Fetch reports in the mod queue.
def getLatestReports(subreddit):
    reports = subreddit.mod.reports(limit=200)
    return reports


###  Check fetched submissions against an algorithm consisting of several conditions. 
def checkSubmissions(submissions):

    try: 

        print(f"Processing submissions now...")

        for submission in submissions:

            #Define the current time and then intervals for later conditions.
            now = time.time()
            onehour = (now -  3600.0)
            twohours = (now - 7200.0)
            twelvehours = (now - 43200.0)
            eighteen = (now - 64800.0)
            week = (now - 604800.0)

            
 
            ### Report conditions 

            # Report posts that are downvoted to 20% within one hour but not reported.
            if submission.created_utc <= onehour and submission.upvote_ratio <= 0.20 and submission.user_reports == 0:
                submission.report(reason='<!> This submission is getting downvoted very quickly.  Please review.')
                continue

            # Reports submissions that reach 400 karma within two hours.
            elif submission.created_utc < twohours and submission.user_reports == 0 and submission.score >= 400 and not submission.spam and not submission.approved and not submission.removed:
                printCurrentTime()
                submission.report(reason='<!> This submission is rising quickly but has not been evaluated.  Please review.')
                print('    ')
                print(f'<!> Reported post - {submission.ups} - /u/{submission.title} - r/{submission.subreddit}.<!>\n')
                continue    

            
            ### Remove conditions 

            # Remove posts that are downvoted below .08%.
            elif submission.upvote_ratio <= 0.08:
                t_message = f'Hello u/{submission.author}.\nYour post to r/{submission.subreddit} doesn\'t appear to be a good fit for this community and has been removed. Please review the subreddit [guidelines.](http://reddit.com/r/{submission.subreddit}/about/rules)\n\n'
                x_footer = f"\n\n*If you feel this was done in error, or would like better clarification or need further assistance, please [message the moderators.](https://www.reddit.com/message/compose?to=/r/{submission.subreddit}&subject=Question regarding the removal of this submission by /u/{submission.author}&message=I have a question regarding the removal of this submission: {submission.permalink})*"
                comment_text = t_message + x_footer
                post_submission = r.submission(id=submission.id)
                this_comment = post_submission.reply(comment_text)
                this_comment.mod.distinguish(how='yes', sticky=True)
                this_comment.mod.lock()
                submission.mod.remove()
                continue

            # Remove spam profile posts (reported/downvoted posts). One report could be an automod filter hence greater than 1.
            elif submission.num_reports > 1 and submission.upvote_ratio <= 0.25:
                r_message = f'Hello u/{submission.author}.\nYour post to r/{submission.subreddit} has been removed. Please review the subreddit [guidelines.](http://reddit.com/r/{submission.subreddit}/about/rules)\n\n'
                n_footer = f"\n\n*If you feel this was done in error, or would like better clarification or need further assistance, please [message the moderators.](https://www.reddit.com/message/compose?to=/r/{submission.subreddit}&subject=Question regarding the removal of this submission by /u/{submission.author}&message=I have a question regarding the removal of this submission: {submission.permalink})*"
                comment_text = r_message + n_footer
                post_submission = r.submission(id=submission.id)
                this_comment = post_submission.reply(comment_text)
                this_comment.mod.distinguish(how='yes', sticky=True)
                this_comment.mod.lock()
                submission.mod.remove(mod_note='removed as spam')
                submission.mod.lock()
                notes = pmtw.Usernotes(r, submission.subreddit)
                link = f'{submission.permalink}'
                n = pmtw.Note(user=f'{submission.author}', note='Spam', link=link, warning='spam')
                notes.add_note(n)
                print(f'r/{submission.subreddit}')
                print(f'<!!> Removed reported post by /u/{submission.author} - {submission.title}')
                print(f'<!!> https://reddit.com{submission.permalink}')
                print('   ')
                continue

            # Remove downvoted week old posts to clean up the sub's front page. If a post can't get at least one upvote in a week it doesn't need to be on the sub.
            elif submission.created_utc < week and submission.upvote_ratio <= 0.25 and submission.num_reports == 0 and not submission.spam and not submission.removed and not submission.approved:
                submission.mod.remove(mod_note="week old spam")
                print('    ')
                print(f'<!> [Removed week old post - with {submission.score} score] <!>')
                printCurrentTime()
                print(f'r/{submission.subreddit} - /u/{submission.author}')
                print(f'Title: {submission.title}')
                print(f'https://reddit.com{submission.permalink}')
                print ('    ')
                continue


            ###  Approve Conditions

            #  Check if submission author is a moderator and approve.  Mod list imported from a separate function.
            elif str(submission.author) in modList:
                submission.mod.approve()
                continue

            # Approve anything in the queue that gets to 600 upvotes with no reports.
            elif submission.user_reports == 0 and submission.score > 599 and not submission.spam and not submission.approved and not submission.removed:
                submission.mod.approve()
                print(f'[Approved post in {submission.subreddit}] with score of {submission.ups}')
                print(f'Title: {submission.title} - /u/{submission.author}')
                print(f'link: {submission.permalink}')
                printCurrentTime()
                print('    ')
                continue

            # Check if post is older than 18 hours, has at least one upvote, no reports, and approve.
            elif submission.created_utc < eighteen and submission.score >= 1 and submission.num_reports == 0 and not submission.spam and not submission.approved and not submission.removed:
                #printCurrentTime()
                submission.mod.approve()
                print(f'Approved Post 18hrs - r/{submission.subreddit} |{submission.score} ^| - u/{submission.author}')
                continue    

            #  Approve week old posts that don't get upvoted, but don't get downvoted either.
            elif submission.created_utc < week and submission.score == 1 and submission.num_reports == 0 and not submission.spam and not submission.removed:
                submission.mod.approve()
                print(f'Approved Post 7days - r/{submission.subreddit} |{submission.score} ^| - u/{submission.author}')

            else:
                continue

        print('Done') 
    except Exception as e:
        print(e)
        traceback.print_exc()


# Set up a ban phrase for custom mod reports.
def banPhrase(subreddit):
    
    ban_phrase = "!ban"

    try:

        print('Checking for ban phrase...')
        for item in subreddit.mod.modqueue(limit=None):
            

            for i in item.mod_reports:
                if i[0] and ban_phrase in i[0]:
                    print(f"REMOVE ITEM {item.fullname}")
                    item.mod.remove()
                    item.mod.lock()


                    if str(item.fullname).startswith('t1'):
                        print (f"banned {item.author}")
                        ban_sub = item.subreddit.display_name
                        banned_message = f"Please read this entire message before sending a reply. This **comment** may have fully or partially contributed to your ban: [{item.body}]({item.permalink}). **So what comes next?**  Modmails with an accusatory, or inflammatory tone will not get a reply.  You may request an appeal of your ban but immediate replies to the ban message with an angry tone will not be given priority.  Sending messages to individual mods outside of modmail is not allowed. [Please read our rules before contacting us.](http://reddit.com/r/{item.subreddit}/about/rules)"
                        r.subreddit(ban_sub).banned.add(f'{item.author}', ban_reason='bot_ban', ban_message=f'{banned_message}', note=f'{item.permalink}')
                        notes = pmtw.Usernotes(r, item.subreddit)
                        link = f'{item.permalink}'
                        n = pmtw.Note(user=f'{item.link_author}', note='Ban', link=link)
                        notes.add_note(n)

                    elif str(item.fullname).startswith('t3'):
                        print (f"banned {item.author}")
                        ban_sub = item.subreddit.display_name
                        banned_message = f"Please read this entire message before sending a reply. This **Submission** may have fully or partially contributed to your ban: [{item.title}]({item.permalink}). **So what comes next?**  Modmails with an accusatory, or inflammatory tone will not get a reply.  You may request an appeal of your ban but immediate replies to the ban message with an angry tone will not be given priority.  Sending messages to individual mods outside of modmail is not allowed. [Please read our rules before contacting us.](http://reddit.com/r/{item.subreddit}/about/rules)"
                        r.subreddit(ban_sub).banned.add(f'{item.author}', ban_reason='bot_ban',ban_message=f'{banned_message}', note=f'{item.permalink}')
                        notes = pmtw.Usernotes(r, item.subreddit)
                        link = f'{item.permalink}'
                        n = pmtw.Note(user=f'{item.link_author}', note='Ban', link=link)
                        notes.add_note(n)

    except Exception as e:
        print(e)
        traceback.print_exc()            

    print("Done")
    time.sleep(2)
            



###  Check items in the reports queue for highly reported items. 
def checkModqueue(reports):
    print('Checking reports...')
    #reported_items = subreddit.mod.reports(limit=200)


    try:
        
        for item in reports:


            # Approve items that have been reviewed and reports were ignored, but post was not approved.
            if item.ignore_reports == True and item.approved == False:
                item.mod.approve()
                print(f"{item.id} had ignored reports and was approved.")
                contactMe = r.redditor("BuckRowdy").message(f"{item.id} was approved", f"Item {item.id} at http://reddit.com{item.permalink} had reports ignored but was not approved.")
                print("Message sent!")

            # Remove comments with a -12 score and 2 reports.
            elif item.num_reports >= 2 and item.score <= -12:
                item.mod.remove()
                item.mod.lock()
                #item.subreddit.message("I removed something for being highly downvoted & reported.", f"FYI I removed this item because it was downvoted to -12 and reported: [{item}](https://reddit.com{item.permalink}) *This was performed by an automated script, please check to ensure this action was correct.*\n---*[^(Review my post removals)](https://reddit.com/r/mod/about/log/?type=removelink&mod=ghostofbearbryant)*")
                print(f'r/{item.subreddit}')
                print(f"I removed this highly reported item. https://reddit.com{item.permalink}\n")
                logging.info(f'Downvote/Reports user: /u/{item.author} -- {item.subreddit} - {item.permalink}')
                notes = pmtw.Usernotes(r, item.subreddit)
                link = f'{item.permalink}'
                n = pmtw.Note(user=f'{item.author}', note='Report Removal', link=link)
                notes.add_note(n)

            # Remove items with 5 reports.
            elif item.num_reports >= 5:
                item.mod.remove()
                item.mod.lock()
                item.subreddit.message("I removed an item for being highly reported.", f"FYI I removed this item because it got reported 5 times: [{item}](https://reddit.com{item.permalink}) *This was performed by an automated script, please check to ensure this action was correct.*\n\n---\n\n*[^(Review my post removals)](https://reddit.com/r/mod/about/log/?type=removelink&mod=ghostofbearbryant)* -- *[[^Subreddit](http://reddit.com/r/ghostofbearbryant)*")
                print(f'r/{item.subreddit}')
                print(f"I removed this highly reported item. https://reddit.com{item.permalink}")
                print('        ')
                print(f'> Author: {item.author}\n Title: {item.title}\n Score: {item.ups}\n')
                print('        ')
                print(f'Reports: {item.mod_reports} mod reports, {item.user_reports} user reports')
                logging.info(f'Highly Reported user: /u/{item.author} -- {item.subreddit} - {item.permalink}')
                notes = pmtw.Usernotes(r, item.subreddit)
                link = f'{item.permalink}'
                n = pmtw.Note(user=f'{item.author}', note='Report Removal', link=link)
                notes.add_note(n)

            else:
                continue

    except Exception as e:
        print(e)
        traceback.print_exc()            

    print("Done")
    time.sleep(2)        



def removeOnPhrase(subreddit):

    remove_phrase = "T-Shirt spam"
    too_old = (60*60*24) # 24 hours
    

    try:

        print(f"Checking for T-Shirt spam...")
        for item in subreddit.mod.modqueue(limit=None):
            #if (time.time() - item.created_utc) > too_old:
                #print(f"item in queue {item.id} too old")
                #break

            if item.banned_by:
                # already removed
                continue

            for i in item.user_reports:
                if i[0] and remove_phrase in i[0]:
                    print(f"REMOVE ITEM {item.fullname}")
                    item.mod.remove()
                    item.mod.lock()

            for i in item.mod_reports:
                if i[0] and remove_phrase in i[0]:
                    print(f"REMOVE ITEM {item.fullname}")
                    item.mod.remove()
                    item.mod.lock()
                    #ban_sub = item.subreddit_name_prefixed
                    #notes = pmtw.Usernotes(r, item.subreddit)
                    #link = f'{item.permalink}'
                    #n = pmtw.Note(user=f'{item.author}', note='T-Shirt Spam', link=link)
                    #notes.add_note(n)        

    except Exception as e:
        print(e)
        traceback.print_exc()

    print("Done")
    time.sleep(2)



def checkModLog(subreddit):

    now = time.time()
    fiveMinutes= (now  - 300)

    try:

        r.validate_on_submit = True

        print(f"Checking the mod log for removed items...")
        for log in r.subreddit("mod").mod.log(limit=200):

            keyphrase = "Dont say -tard"

            if log.created_utc <= fiveMinutes :
                print(f"Item {log.action} in r/{log.subreddit} is too old")
                break

            elif keyphrase in log.details:
                sub_name = "ghostofbearbryant"
                title = f"Ret*rd Filter in r/{log.subreddit} for /u/{log.target_author}."
                selftext = f"Action: {log.action}\n\nTitle: {log.target_title}\n\nBody: {log.target_body}\n\nDetails: {log.details}\n\nLink: http://reddit.com{log.target_permalink}"
                r.subreddit(sub_name).submit(title, selftext)
                print(f"Action: >{log.action}< was posted in the log sub.") 

            elif log.mod == "Anti-Evil+Operations": 
                sub_name = "ghostofbearbryant"
                title = f"Action logged by u/{log.mod} in r/{log.subreddit}. "
                selftext = f"Action: {log.action}\n\nTitle: {log.target_title}\n\nBody: {log.target_body}\n\nDetails: {log.details}\n\nLink: http://reddit.com{log.target_permalink}"
                r.subreddit(sub_name).submit(title, selftext)
                print(f"Action: >{log.action}< was posted in the log sub.")     
            
            elif log.action == "removelink" and log.mod == "ghostofbearbryant":
                sub_name = "ghostofbearbryant"
                title = f"Post Removed for author u/{log.target_author} in r/{log.subreddit}. "
                selftext = f"Action: {log.action}\n\nTitle: {log.target_title}\n\nBody: {log.target_body}\n\nDetails: {log.details}\n\nLink: http://reddit.com{log.target_permalink}"
                r.subreddit(sub_name).submit(title, selftext)
                print(f"Action: >{log.action}< was posted in the log sub.")
                ban_sub = log.subreddit
                notes = pmtw.Usernotes(r, r.subreddit(sub_name))
                link = f'{log.target_permalink}'
                n = pmtw.Note(user=f'{log.target_author}', note='T-Shirt Spam', link=link)
                notes.add_note(n) 




            elif log.action == "removecomment" and log.mod == "ghostofbearbryant":
                sub_name = "ghostofbearbryant"
                title = f"Comment Removed in r/{log.subreddit} originally posted by /u/{log.target_author}"
                selftext = f"Action: {log.action}\n\nComment: {log.target_body}\n\nAuthor: /u/{log.target_author}\n\nDetails: {log.details}\n\nLink: http://reddit.com{log.target_permalink}"
                r.subreddit(sub_name).submit(title, selftext)
                print(f"Action: >{log.action}< was posted in the log sub.")

            elif log.action == "banuser" and log.mod == "ghostofbearbryant":
                a_string = f'{log.description}'
                description = a_string[9:]
                sub_name = "ghostofbearbryant"
                title = f"User u/{log.target_author} banned in r/{log.subreddit}."
                selftext = f"Action: {log.action}\n\nAuthor: /u/{log.target_author}\n\nDetails: {log.details}\n\nLink: http://reddit.com{description}"
                r.subreddit(sub_name).submit(title, selftext)
                print(f"Action: >{log.action}< was posted in the log sub.")
                

            else:
                continue

    except Exception as e:
        print(e)
        traceback.print_exc()

    print("Done")
    time.sleep(3)
    print("Finishing up...\n")



### Fetch the number of items left in each queue.
def howManyItems(subreddit):

    submissions = subreddit.mod.unmoderated(limit=1000)
    reported_items = subreddit.mod.reports(limit=200)
    num = len(list(reported_items))
    unmod = len(list(submissions))
    print(f'There are {num} reported items and {unmod} unmoderated posts remaining.')
    print('------------------------------------------------------------------------')



######################################



### Bot starts here

if __name__ == "__main__":

    try:
            # Connect to reddit and return the object
            r = redditLogin()

            # Connect to the sub
            subreddit = r.subreddit(sub_name)

    except Exception as e:
        print('\t\n### ERROR - Could not connect to reddit.')
        sys.exit(1)
 

    # Loop the bot
    while True:

        try:
            # Get the latest submissions after emptying variable
            submissions = None
            printCurrentTime()
            submissions = getLatestSubmissions(subreddit)
            reports = getLatestReports(subreddit)
            

        except Exception as e:
            print('\t### ERROR - Could not get posts from reddit')

        # If there are posts, start scanning
        if not submissions is None:


            # Once you have submissions, run all the bot functions.
            checkSubmissions(submissions)
            checkModqueue(reports)
            removeOnPhrase(subreddit)
            banPhrase(subreddit)
            checkModLog(subreddit)
            howManyItems(subreddit)


        # Loop every X seconds (5 minutes, currently.)
        sleep_until = (dt.now() + td(0, sleep_seconds)).strftime('%H:%M:%S')
        print(f'Be back around {sleep_until}.') 
        print('    ')

        time.sleep(sleep_seconds)
