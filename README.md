#Inthe.AM Calendar Sync

##What does it do?
This script gets around a longstanding bug in how Google Calendar handles importing iCal feeds. Instead of relying on that functionality, inthe.am users can use this script that bypasses the issue and gets new events from your task list onto your calendar almost instantly.

##Installation Instructions

1. Download the zip file, extract to same folder.

2. Download requests, pytz and google-api-python-client with pip. (sudo pip install requests pytz google-api-python-client)

3. Configure the program. Open intheAMsync.conf with your favorite  text editor. I'll explain the fields:
	* inthe.am API key: Your key obtained from inthe.am settings. Just copy/paste it in.
	* calendar id: You need to make a new calendar to sync events into. In the calendar settings for this new calendar, there should be a field that looks like <random letters/numbers>@group.calendar.google.com. Copy this in.
	* time zone: this should be primary time zone you are in. Match this to the settings for your calendar as well. Example: America/New_York.
	* show due on prior day: if you put in True, you dates will show up on as due on the day before they're due in taskwarrior. This makes sense to some workflows, and no sense whatsoever to others. Set this to False if you're not impressed.

4. Lastly, before you can run the program, you need your own Google Calendar API credentials, since you're running this yourself. 
	1. Go to console.developers.google.com. 
	2. Left side, click Credentials.
	3. Click the blue Create Credentials box.
	4. Click OAuth Client ID.
	5. Select type Other and name it InTheAmSync
	6. Exit the screen letting you copy/paste your credentials. You should now be out of the popup wizard.
	7. On the right side, click the download button in the row containing InTheAMSync. It's labeled "Download JSON"
	8. Take this file you downloaded, rename it to "client_id.json" and put it in the same directory as the config file  and sync script.
	

5. Run program with ./intheAMsync.py. It will open your default browser and ask you to log into your google account. Your details will be saved on disk at ~/.credentials, so this process will only need to occur once. If you want to use this program on a headless server, do this step on a non-headless box and and move the .credentials folder to your server, along with the program directory. The google API does not officially support headless operation, but this workaround works fine.

6. Run the program every time you want to sync. You can do this automatically at set intervals with cron, as well. I'm sure the author of inthe.am would prefer you don't set the sync interval too high, however. 

Other info regarding sync frequency: For Google Calendar, there's a maximum of 1 million API calls/day. Each sync uses at least one API call, and an additional one for every event added or deleted. At this point, moves count as two calls. If you have really huge task lists or use one Google API key for lots of people, you may run into the the limit there. 
