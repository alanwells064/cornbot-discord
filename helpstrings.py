HELP = {
    "help": "`about` - Displays info about Cornbot."
    "\n`delete` - Deletes a prompt, log activity, or break reminder setting."
    "\n`help` - Displays this message, a list of commands."
    "\n`list` - Displays a list of your prompts, logs, or breaks, or displays all timezones."
    "\n`log` - Makes an entry in your personal activity log."
    "\n`merge` - Allows the time from two log activities to be merged into one."
    "\n`reset` - Reset some or all of your Cornbot data."
    "\n`respond` - Mark a message as a response to a prompt."
    "\n`schedule` - Set a prompt or break reminder for a certain time."
    "\n`timezone` - Set or check your timezone setting."
    "\nYou can say `help <command>` for info about a specific command."
    ,
    "about": "`about` (no arguments)"
    "\nDisplays info about Cornbot."
    ,
    "delete": "`delete <break, log, prompt> <arg>"
    "\nDeletes a prompt, log activity, or break reminder setting."
    "\n`delete break <game>` - Deleting a game's setting makes it use the default setting."
    "\n`delete log <activity>`"
    "\n`delete prompt <#, time>` - The #)'s given by `list prompt` can be used instead of a time."
    ,
    "list": "`list <breaks, logs, prompts, timezones>`"
    "\nDisplays a list of your prompts, logs, or breaks, or displays all timezones."
    "\n`list log <activity>` - Optional, shows more details about a specific activity."
    ,
    "log": "`log <activity> <time>`"
    "\nMakes an entry in your personal activity log. You have 10 activity slots."
    "\n`<time>` - Examples: '1 hour 30 min', '75minutes', '1h 10m30s', etc."
    ,
    "merge": "`merge <activity1> <activity2> <new-activity>`"
    "\nAllows the time from two log activities to be merged into one."
    "\nExample: `merge running swimming excercise` - Merges the 'running' and 'swimming' activites into a new 'excecise' activity."
    "\n`<new-activity>` can be the same as `<activity1>` or `<activity2>`, but can't be the same as another already existing activity."
    ,
    "reset": "`reset <all, breaks, logs, prompts>`"
    "\nReset some or all of your Cornbot data. **WARNING:** any reset data will be permanently erased! "
    "There is currently no confirmation after sending the command; deletion will happen right away."
    "\n`reset all` deletes your user data entirely from the bot's system."
    ,
    "respond": "`respond <message>`"
    "\nMarks a message as a response to a prompt. Note: response message are not recorded, "
    "but they allow you to easily search through your responses using Discord's search bar."
    ,
    "schedule": "`schedule <break, prompt> <args>`"
    "\nSet a prompt or break reminder for a certain time."
    "\n`schedule break <game> <time>` - `<time>` Examples: '1h30m', '40 minutes', etc."
    "\n`schedule prompt <24-hr-time> <message>` - Must be a 24 hour time (no AM or PM)."
    ,
    "timezone": "`timezone <offset>`"
    "\nSet or check your timezone setting."
    "\nTo see your current timezone, don't give an `<offset>`. To see all timezones, use `list timezones`."
}

NOOB_HELP = ("`about` - Displays info about Cornbot."
"\n`help` - Displays this message, a list of commands."
"\n`list timezones` - Displays a list all timezones."
"\n`timezone` - Set or check your timezone setting.")

ABOUT = ("> I created Cornbot for as a final project for my college Python course. "
"My professor saw a great opportunity for a tool I could use in my mental health journey, and his ideas became what is now the prompt system. "
"Wanting to make something functional and easy to use for myself and others, I set my goal to develop a small but fully hostable bot. "
"While I initially started this project for me, my hope is that Cornbot can add a little mental tool to the belt of anyone in need."
"\n> \n"
"> You can reach me at Cornsauce#6228 if you have questions, feedback, or outages to report. Thanks and enjoy!"
"\n> \n"
"> *- Alan, aka Cornsauce, author*"
"\n\n"
"Cornbot does not store or track any personal information or data related to your Discord profile. "
"Your preferences, prompts, and log data are stored anonymously under your 18-digit Discord ID. "
"Using `reset all` deletes all your data, effectively removing you from the bot's system."
"\n\n"
"Last updated 5-30-23.")