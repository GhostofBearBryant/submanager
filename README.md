# SubManager

Manage your reddit unmoderated queue and reports queue.  

The bot that runs on u/ghostofbearbryant is a subreddit manager bot that monitors the reports and unmoderated queues every five minutes.  It has a third function that scans the mod log and creates a new post for each removed post and comment.  

Ghost runs on 75-ish subreddits currently.  It manages things so that you can focus on the reports queue.  Some posts on the sub will be reported by the bot for you to review.  Your unmoderated queue will only have posts that are 18 hours old or newer, or posts that are downvoted to 0 and are less than 7 days old leaving you less to deal with so you can review new posts.

It monitors items in both the reports and unmoderated queues. Here is a description of the conditions it uses. 

**Reports Queue**

Every 5 minutes the bot cycles through the last 200 reported items. 

- Any item that has 'Ignore Reports' but *is not approved* will be approved.  This is very niche, but does happen sometimes.

- Any item downvoted to -12 with 2 or more reports will be removed and logged.  This function targets comments and can be adjusted.

- Any item receiving 5 reports will be removed, locked, and logged.  A generic removal comment will be posted with a link to the rules and a link to modmail with a prefilled subject line. A mod discussion will be sent with a link to the item.  **Note:** Automoderator has this same ability *except* [if a mod has approved the content previously](https://imgur.com/KPO4orL) but it still continues to build reports. 

**Unmoderated Queue**

The last 1000 items in the unmoderated queue are checked every 5 minutes. Posts will either be approved, removed, or reported according to the following set of conditions. 

Any post can be made exempt from the following set of conditions by approving it which will remove it from the unmoderated queue. 

- **Report Conditions**

 Posts that will be reported:

 - Posts that are not approved and reach 400 karma within two hours.
 - Posts that are downvoted to 20% within one hour but not reported.

- **Remove Conditions**

 Posts that will be removed:

 - Posts that are downvoted to .08% or lower.  A generic removal comment will be stickied with a link to modmail for an appeal.  

 - Comments that are downvoted to -12 and have 2 or more reports.  A post will be made in the sub to log it.  

 - Posts that are downvoted to 25% or lower and have 2 reports.  These posts are usually spam. A post will be made in the sub to log it.  

 - Posts that are older than one week and have an upvote ratio of .50%  or lower.  If a post can't manage to get to above 50% upvote ratio within one week it is not contributing quality content to the sub.  Any post can be removed from this condition by approving it. 
     
- **Approve Conditions**

 Posts that will be approved:
 
 - Posts made by a moderator of the subreddit but not approved by them. 

 - Any post that gets 600 upvotes without being user reported.  

 - Any post that is older than 18 hours, has a score of 1 or more, and is not reported.  In that time frame a post will likely *be* reported and even if it is bot approved it can still be reported. 




**Ban via Custom Report**

This function allows mods to ban a user for a post or comment via a custom report on the item.  Report posts or comments using the phrase ```!ban``` and only that phrase.  Remember the bot runs every five minutes and takes about 30 seconds to run through a cycle.  A ban message will be sent similar to the flair_helper ban message in each sub.  The message includes a link to the thing they got banned for.  

**Mod Log**

The bot will check the mod log for removed comments and posts as well as bans issued via the ban phrase and will log each one with a post in this sub with the details and a link to the item.
