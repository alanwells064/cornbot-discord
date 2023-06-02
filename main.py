# discord bot by Alan Wells

import discord, util, json, os, helpstrings, customhelp
from discord.ext import commands, tasks
import datetime as dt
import pandas as pd

DIRECTORY_PATH = os.path.dirname(__file__)
USERS_PATH = os.path.join(DIRECTORY_PATH, "users")
TIMES_PATH = os.path.join(DIRECTORY_PATH, "times")
HOURLY_UPDATE_TIMES = [dt.time(hour=i) for i in range(24)]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='', intents=intents, case_insensitive=True)
client.help_command = customhelp.CustomHelp()

#################### EVENTS ####################

@client.event
async def on_ready():
    """
    Setup function that runs on startup.
    """
    print(f"Local time is {dt.datetime.now()}.")
    print(f"UTC time is {dt.datetime.utcnow()}.")
    # populate util.registered_users list
    for filename in os.listdir(USERS_PATH):
        if filename.endswith(".json"):
            util.registered_users.append(int(filename[:-5]))
    print(f"Found {len(util.registered_users)} registered user files.")
    # populate times for prompt_users
    utcnow_hour = dt.datetime.utcnow().hour
    print(f"Loading prompts and populating times from times/{utcnow_hour}.json...")
    with open(f"times/{utcnow_hour}.json", "r") as file:
        hour_json = json.load(file)
        prompt_users.change_interval(time=util.populate_times(hour_json, utcnow_hour))
        util.current_hour_json = hour_json
    # count how many times were loaded, not counting 0:00:13
    if len(prompt_users.time) == 1 and prompt_users.time[0].second == 13:
        loaded_times = 0
    else:
        loaded_times = len(prompt_users.time)
    print(f"Loaded {loaded_times} times for this hour.")
    print("Starting loops...")
    prompt_users.start()
    hourly_update.start()
    break_check.start()
    # set status
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="DM's"))
    print(f"Successfully logged in as {client.user}.")

@client.event
async def on_member_join(member):
    await member.send(f"Hello! I'm Cornbot by Cornsauce. :)\n"
                      "I send you quick messages throughout the day to help you keep a positive headspace! "
                      "I can also keep an activity log of things you like to do, as well as remind you to "
                      f"take breaks every so often. Right now I'm a DM's-only bot.\n\n"
                      "You can say `about` to learn more about me and my functions"
                      f"\n\nOR\n\n"
                      "We'll just need your timezone to finish setting up. You can say `timezone` to continue.")
    # await member.kick()


#################### COMMANDS ####################

@client.command()
async def log(ctx, *, arg=None):
    """
    Command to log time of an activity.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        if not arg:
            await ctx.send("Usage: `log <activity> <time>`")
            return
        # split args into list and make them lowercase
        arg_list = arg.lower().split()
        if len(arg_list) <= 1:
            await ctx.send("Usage: `log <activity> <time>`")
            return
        # pop first arg as activity (must be under 30 chars)
        activity = arg_list.pop(0)
        if len(activity) > 30:
            await ctx.send("Couldn't parse activity; names must be 30 characters or less.")
            return
        # then rejoin all following args into 1 string, no spaces,
        # and resplit it into alphabetical and numeric elements
        try:
            arg_list = util.split_alpha_num("".join(arg_list))
        # if split_alpha_num gives ValueError, arg has non-alphanumeric characters
        except ValueError:
            await ctx.send("Couldn't parse time; accepts `hours`, `minutes`, and `seconds` (can be abbreviated).")
            return
        time = dt.timedelta(seconds=0)
        # temp_number keeps track of value while units are parsed
        temp_number = 0
        # parse numbers and units
        for item in arg_list:
            if item.isnumeric():
                temp_number = int(item)
            elif item.isalpha():
                if "hours ".startswith(item):
                    time += dt.timedelta(hours=temp_number)
                elif "minutes ".startswith(item):
                    time += dt.timedelta(minutes=temp_number)
                elif "seconds ".startswith(item):
                    time += dt.timedelta(seconds=temp_number)
                else:
                    await ctx.send("Couldn't parse time; accepts `hours`, `minutes`, and `seconds` (can be abbreviated).")
                    return
        if time >= dt.timedelta(hours=24):
            await ctx.send("Couldn't log a time >=24 hours.")
            return
        # get local date for user's timezone
        with open(f"users/{ctx.author.id}.json", "r") as file:
            user_json = json.load(file)
        local_now = dt.datetime.utcnow() + dt.timedelta(hours=user_json["tz"])
        local_date = dt.date(year=local_now.year, month=local_now.month, day=local_now.day)
        # opening file
        try:
            with open(f"users/{ctx.author.id}.csv", "r") as file:
                log_data = pd.read_csv(file, index_col=0)
        except FileNotFoundError:
            with open(f"users/{ctx.author.id}.csv", "w") as file:
                print(f"File not found, creating logs for {ctx.author.id}.")
                await ctx.send("First-time setting up logs!")
                # turn time into a string, split it on space, and grab the last element
                # to prevent formatting issues, like "0 days 0:00:00"
                time = str(time).split()[-1]
                # create new csv
                log_data = pd.DataFrame({activity:time}, index=[local_date])
                log_data.to_csv(file)
                await ctx.send(f"Created new activity: `{activity}`. (1/10 slots used)")
                await ctx.send(f"Logged `{activity}` for {time}.")
                return
        if activity not in log_data.iloc[0]:
            if len(log_data.iloc[0]) >= 10:
                await ctx.send(f"Couldn't create new activity for `{activity}`. (10/10 slots used)")
                return
            else:
                await ctx.send(f"Created new activity: `{activity}`. ({len(log_data.iloc[0])+1}/10 slots used)")
        # add time already logged with time user logged just now
        updated_time = time + util.get_timedelta(local_date, activity, log_data)
        if updated_time >= dt.timedelta(hours=24):
            updated_time = dt.timedelta(hours=23, minutes=59, seconds=59)
        # turn updated time into a string, split it on space, and grab the last element
        # to prevent formatting issues, like "0 days 0:00:00"
        updated_time = str(updated_time).split()[-1]
        # if already a row for today, put new time in that row
        if str(local_date) in log_data.index:
            log_data.loc[str(local_date), activity] = updated_time
        # if not yet a row for today, make new row df and concat, so that new row is at top
        else:
            new_row = pd.DataFrame({activity:updated_time}, index=[local_date])
            log_data = pd.concat([new_row, log_data])
        # save/overwrite log csv
        with open(f"users/{ctx.author.id}.csv", "w") as file:
            log_data.to_csv(file)
        await ctx.send(f"Logged `{activity}` for {time}.")

@client.command()
async def delete(ctx, *, arg=None):
    """
    Command to delete logs, prompts, or breaks.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        if not arg:
            await ctx.send("Usage: `delete <break, log, prompt> <arg>`")
            return
        # grab first arg as delete_type
        arg_list = arg.lower().split()
        delete_type = arg_list.pop(0)
        # deleting log
        if "log ".startswith(delete_type):
            if len(arg_list) == 0:
                await ctx.send("Usage: `delete log <activity>`")
                return
            arg = arg_list.pop(0)
            # open user's log file and read data
            try:
                with open(f"users/{ctx.author.id}.csv", "r") as file:
                    log_data = pd.read_csv(file, index_col=0)
            except FileNotFoundError:
                await ctx.send("No logs found.")
                return
            # check if the activity the user is trying to delete exists
            if arg in log_data.iloc[0]:
                # delete the entire column from the csv and save
                log_data = log_data.drop(columns=arg)
                with open(f"users/{ctx.author.id}.csv", "w") as file:
                    log_data.to_csv(file)
                await ctx.send(f"Deleted activity `{arg}`. ({len(log_data.iloc[0])}/10 slots used)")
            else:
                await ctx.send(f"Couldn't find activity `{arg}`.")
        # deleting prompt
        elif "prompt ".startswith(delete_type):
            if len(arg_list) == 0:
                await ctx.send("Usage: `delete prompt <#, time>`")
                return
            arg = arg_list.pop(0)
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # if user gives a valid time
            if util.validate_time(arg):
                # add a 0 to time if need, so format is "HH:MM"
                if len(arg) < 5:
                    arg = "0" + arg
            # if user gives a valid int, try to grab time of that index from json
            elif arg.isnumeric():
                try:
                    arg = list(user_json["prompts"])[int(arg)-1]
                except IndexError:
                    await ctx.send(f"Couldn't find prompt with index {arg}.")
                    return
            # user didn't give a valid time or int
            else:
                await ctx.send("Couldn't parse argument as an index number or time.")
                return
            # try to pop user's given time, return if fail
            try:
                user_json["prompts"].pop(arg)
            except KeyError:
                await ctx.send(f"Couldn't find a prompt scheduled at {arg}.")
                return
            # save/overwrite user json
            with open(f"users/{ctx.author.id}.json", "w") as file:
                json.dump(user_json, file)
            # get the hour of the given time in utc
            utc_hour = (int(arg[:2]) - user_json["tz"]) % 24
            # load hour json
            with open(f"times/{utc_hour}.json", "r") as file:
                hour_json = json.load(file)
            # remove user's id from the minute list, deleting their timeslot
            hour_json[arg[3:]].remove(ctx.author.id)
            # if minute list is now empty, pop it
            if len(hour_json[arg[3:]]) == 0:
                hour_json.pop(arg[3:])
            # if deleted time is in the current hour, update the prompt loop
            if dt.datetime.utcnow().hour == utc_hour:
                prompt_users.change_interval(time=util.populate_times(hour_json, utc_hour))
                prompt_users.restart()
                util.current_hour_json = hour_json
            # save/overwrite hour json
            with open(f"times/{utc_hour}.json", "w") as file:
                json.dump(hour_json, file)
            await ctx.send(f"Deleted your daily {arg} prompt.")
        # deleting break
        elif "break ".startswith(delete_type):\
            # no game name given, return usage
            if len(arg_list) == 0:
                await ctx.send("Usage: `delete break <game>`")
                return
            # rejoin args into a single string
            game_name = " ".join(arg_list)
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # can't delete default setting
            if game_name == "default":
                await ctx.send("Can't delete default break setting. To disable breaks, use `schedule break` and set them to 0:00.")
                return
            # if game preference exists, delete it and save file
            elif game_name in user_json["breaks"]:
                user_json["breaks"].pop(game_name)
                with open(f"users/{ctx.author.id}.json", "w") as file:
                    json.dump(user_json, file)
                await ctx.send(f"Deleted break reminders for `{game_name}`. ({len(user_json['breaks'])-1}/10 slots used)"
                               f"\nIt will now use the default setting.")
            # game not found
            else:
                await ctx.send(f"Couldn't find break reminders for `{game_name}`.")
        # arg is some other word, send usage
        else:
            await ctx.send("Usage: `delete <break, log, prompt> <args>`")

@client.command()
async def merge(ctx, *, arg):
    """
    Command to merge 2 activity categories into 1.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        # split args into list and make them lowercase
        arg_list = arg.lower().split()
        # open user's log file and read data
        try:
            with open(f"users/{ctx.author.id}.csv", "r") as file:
                log_data = pd.read_csv(file, index_col=0)
        except FileNotFoundError:
            await ctx.send("No logs found.")
            return
        # if not enough args, send usage
        if len(arg_list) < 3:
            await ctx.send("Usage: `merge <activity1> <activity2> <new-activity>`")
            return
        # check if the given activities exist in the user's logs
        if arg_list[0] not in log_data.iloc[0]:
            await ctx.send(f"Couldn't find activity `{arg_list[0]}`.")
            return
        if arg_list[1] not in log_data.iloc[0]:
            await ctx.send(f"Couldn't find activity `{arg_list[1]}`.")
            return
        # check if the given activites are the same
        if arg_list[0] == arg_list[1]:
            await ctx.send(f"Can't merge an activity `{arg_list[0]}` with itself.")
            return
        # check if the new activity already exists, and doesn't match the first 2
        if arg_list[2] in log_data.iloc[0] and arg_list[2] != arg_list[0] and arg_list[2] != arg_list[1]:
            await ctx.send(f"Can't create new activity `{arg_list[3]}`; it already exists")
        # list comprehension. i felt like a GOD after writing this.
        # a filthy, pythonic god, but still.
        # make a list of all timedeltas from the first activity arg
        list_base = [util.get_timedelta(date, arg_list[0], log_data) for date in log_data.index]
        # make a list of all timedeltas from the second activity arg
        list_to_add = [util.get_timedelta(date, arg_list[1], log_data) for date in log_data.index]
        # add the values of the second list into the first. should be impossible to have diff list lengths.
        list_base = [list_base[i] + list_to_add[i] for i in range(len(list_base))]
        # turn each time into a string, split it on space, and grab the last element
        # to prevent formatting issues, like "0 days 0:00:00"
        list_base = [str(time).split()[-1] for time in list_base]
        # remove the old/just-got-merged columns from the log
        log_data = log_data.drop(columns=[arg_list[0], arg_list[1]])
        # slot the list values into a new column in the log, column title = third arg
        # old columns are deleted first to allow columns to be merged into themselves (x + y -> x)
        log_data[arg_list[2]] = list_base
        with open(f"users/{ctx.author.id}.csv", "w") as file:
            log_data.to_csv(file)
        await ctx.send(f"Successfully merged activity categories `{arg_list[0]}` and `{arg_list[1]}` into `{arg_list[2]}`. ({len(log_data.iloc[0])}/10 slots used)")

@client.command(name="list")
async def list_display(ctx, list_type=None, arg1=None):
    """
    Command for listing/displaying user's logs, prompts, and breaks settings/data.
    Also displays timezones and their current times.
    Usable by unregistered users only for timezones.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        # if no args, send usage
        if list_type is None:
            await ctx.send("Usage: `list <breaks, logs, prompts, timezones>`")
            return
        # listing logs
        elif "logs ".startswith(list_type):
            # opening file
            try:
                with open(f"users/{ctx.author.id}.csv", "r") as file:
                    log_data = pd.read_csv(file, index_col=0)
            except FileNotFoundError:
                await ctx.send("No logs found.")
                return
            # no arg1 = send all logs; arg1 if found = send specific log
            if arg1 is None or arg1 in log_data.columns:
                await ctx.send(util.display_log(log_data, arg1))
            else:
                await ctx.send(f"Couldn't find activity `{arg1}`.")
        # listing prompts
        elif "prompts ".startswith(list_type):
            # opening file
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # send prompts
            await ctx.send(util.display_prompt(user_json))
        # listing timezones
        elif "timezones ".startswith(list_type):
            await ctx.send(util.display_timezones())
        # listing breaks
        elif "breaks ".startswith(list_type):
            # opening file
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # send breaks
            await ctx.send(util.display_breaks(user_json))
        # list_type is some other word, send usage
        else:
            await ctx.send("Usage: `list <breaks, logs, prompts>`")
    # if user is not registered yet, only allow "list timezones"
    elif isinstance(ctx.channel, discord.channel.DMChannel):
        if not list_type:
            await ctx.send("Try `list timezones`.")
        elif "timezones ".startswith(list_type):
            await ctx.send(util.display_timezones())
        else:
            await ctx.send("Try `list timezones`.")

@client.command()
async def schedule(ctx, *, arg=None):
    """
    Command to schedule a prompts and breaks.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        # if no args given, send usage
        if not arg:
            await ctx.send("Usage: `schedule <break, prompt> <args>`")
            return
        # split args and grab first as sch_type, either "prompt" or "break"
        arg_list = arg.split()
        sch_type = arg_list.pop(0).lower()
        # scheduling a prompt
        if "prompt ".startswith(sch_type):
            # if not enough args given, send usage
            if len(arg_list) < 2:
                await ctx.send("Usage: `schedule prompt <24-hr-time> <message>`")
                return
            # grab new first arg, should be time
            time_arg = arg_list.pop(0)
            # validate time_arg to continue parsing
            if not util.validate_time(time_arg):
                await ctx.send("Couldn't parse time; accepts `HH:MM` in 24-hour time.")
                return
            # add a zero to the hour if need (8:45 -> 08:45) so all times are len(5)
            if len(time_arg) < 5:
                time_arg = "0" + time_arg
            # grab ints out of time_arg
            user_hour = int(time_arg[:2])
            user_minute = int(time_arg[3:])
            # rejoin remaining args into a string, they are the prompt message content
            content = " ".join(arg_list)
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # notify user if a prompt was already scheduled at this time
            if time_arg in list(user_json["prompts"].keys()):
                await ctx.send(f"Overwriting {time_arg} prompt.")
                # set prompt time:content
                user_json["prompts"][time_arg] = content
                # save/overwrite user json
                with open(f"users/{ctx.author.id}.json", "w") as file:
                    json.dump(user_json, file)
            else:
                # set prompt time:content
                user_json["prompts"][time_arg] = content
                # save/overwrite user json
                with open(f"users/{ctx.author.id}.json", "w") as file:
                    json.dump(user_json, file)
                # use user's timezone to determine which utc hour json to edit
                utc_hour = (user_hour - user_json["tz"]) % 24
                # load hour json
                with open(f"times/{utc_hour}.json", "r") as file:
                    hour_json = json.load(file)
                # if there are no prompts scheduled at this minute, make empty list
                if time_arg[3:] not in hour_json.keys():
                    hour_json[time_arg[3:]] = []
                # append the user's id to the scheduled minute list
                hour_json[time_arg[3:]].append(ctx.author.id)
                # save/overwrite hour json
                with open(f"times/{utc_hour}.json", "w") as file:
                    json.dump(hour_json, file)
                # if user just scheduled a time in the current hour, update the prompt loop with new times
                if dt.datetime.utcnow().hour == utc_hour:
                    prompt_users.change_interval(time=util.populate_times(hour_json, utc_hour))
                    prompt_users.restart()
                    util.current_hour_json = hour_json
            await ctx.send(f"Scheduled prompt at {time_arg} daily.")
        # scheduling a break
        if "break ".startswith(sch_type):
            # if not enough args given, send usage
            if len(arg_list) < 2:
                await ctx.send("Usage: `schedule break <game> <time>`")
                return
            # turn arg_list lowercase
            arg_list = [x.lower() for x in arg_list]
            # split alphabetical and numerical terms
            try:
                alnum_arg_list = util.split_alpha_num(" ".join(arg_list))
            except ValueError:
                await ctx.send("Couldn't parse game name or time; can't accept special characters.")
                return
            # parse time, remaining_args are terms that were not parsed as time
            remaining_args, time = util.parse_time_from_args(alnum_arg_list)
            # if time returns as false, there was no parsable time in the arguments list
            if time == False:
                await ctx.send("Couldn't parse time; accepts `hours` and `minutes` (can be abbreviated).")
                return
            # check HOW MANY of the remaining args match the full arg_list
            # we do this because spaces could have been added by split_alpha_num
            # ensures "game2" does not become "game 2"
            for i in range(len(arg_list)):
                if "".join(arg_list[:i]) in "".join(remaining_args):
                    arg_counter = i
            # finally, get the game name using the number we just calculated ^
            game_name = " ".join(arg_list[:arg_counter])
            # if no game name parsed, send usage
            if game_name == "":
                await ctx.send("Usage: `schedule break <game> <time>`")
                return
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # check slots used for breaks already, max 10 allowed not including default
            if len(user_json["breaks"]) >= 11 and game_name not in user_json["breaks"]:
                await ctx.send(f"Couldn't schedule a new break time for `{game_name}`. (10/10 slots used)")
                return
            # update user json, value is just stored as an int of minutes
            user_json["breaks"][game_name] = int(time.seconds / 60)
            # save/overwrite user json
            with open(f"users/{ctx.author.id}.json", "w") as file:
                json.dump(user_json, file)
            if game_name == "default":
                await ctx.send(f"Updated default break reminders to every {time}.")
            else:
                await ctx.send(f"Scheduled break reminders for `{game_name}` every {time}. ({len(user_json['breaks'])-1}/10 slots used)")

@client.command()
async def timezone(ctx, arg=None):
    """
    Command to set user's timezone.
    Also usable by unregistered users, and completes their registration.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        # open user json
        with open(f"users/{ctx.author.id}.json", "r") as file:
            user_json = json.load(file)
        if not arg:
            # localize current time to user
            local_hour = (dt.datetime.utcnow().hour + user_json["tz"]) % 24
            local_minute = dt.datetime.utcnow().minute
            # format tz string
            if user_json["tz"] >= 0:
                tz_str = "+" + str(user_json["tz"])
            else:
                tz_str = str(user_json["tz"])
            await ctx.send(f"Your current timezone is UTC**{tz_str}**. (now {local_hour}:{local_minute})")
            await ctx.send("Use `timezone <offset>` to change it.")
            return
        # check if arg is valid
        elif util.validate_signed_num(arg) and int(arg) in range(-11, 15):
            # delete prompts from hour jsons before tz gets updated
            for time in list(user_json["prompts"].keys()):
                delete_prompt_from_hr(ctx.author.id, user_json, time)
            # update tz
            user_json["tz"] = int(arg)
            # save/overwrite user json
            with open(f"users/{ctx.author.id}.json", "w") as file:
                json.dump(user_json, file)
            # reschedule prompts in correct hour jsons after tz gets updated
            for time in list(user_json["prompts"].keys()):
                schedule_prompt_to_hr(ctx.author.id, user_json, time)
            # localize current time to user
            local_hour = (dt.datetime.utcnow().hour + user_json["tz"]) % 24
            local_minute = str(dt.datetime.utcnow().minute)
            if len(local_minute) < 2:
                local_minute = "0" + local_minute
            # format tz string
            if user_json["tz"] >= 0:
                tz_str = "+" + str(user_json["tz"])
            else:
                tz_str = str(user_json["tz"])
            await ctx.send(f"Updated your timezone to UTC**{tz_str}**. (now {local_hour}:{local_minute})")
            return
        # arg was not a valid number
        else:
            await ctx.send("Couldn't parse number; accepts values from -11 to 14.")
            await ctx.send("Use `list timezone` to see current times.")
            return
    # if user is not registered yet
    elif isinstance(ctx.channel, discord.channel.DMChannel):
        if not arg:
            utc_minute = dt.datetime.utcnow().minute
            eastern_hour = (dt.datetime.utcnow().hour - 4) % 24
            pacific_hour = (eastern_hour - 3) % 24
            await ctx.send("Your timezone is the number of hours **offset** you are from UTC time. For example:"
                           f"\nEastern time is **-4** hours (currently {eastern_hour}:{utc_minute})."
                           f"\nPacific time is **-7** hours (currently {pacific_hour}:{utc_minute})."
                           f"\n\n"
                           "Use `list timezone` to see all timezones, or"
                           f"\nUse `timezone #` with your # of hours to set your timezone.")
        # check if arg is valid
        elif util.validate_signed_num(arg) and int(arg) in range(-11, 15):
            # set tz and create default values
            user_json = {
                "tz":int(arg),
                "prompts":{
                    "20:00":"What's something you did today that you're proud of?"
                },
                "breaks":{
                    "default":70
                }
            }
            # create user file
            with open(f"users/{ctx.author.id}.json", "w") as file:
                json.dump(user_json, file)
            # put the default prompt into its hour json
            schedule_prompt_to_hr(ctx.author.id, user_json, "20:00")
            # add user to registry
            util.registered_users.append(ctx.author.id)
            # get local time
            user_hour = (dt.datetime.utcnow().hour + user_json["tz"]) % 24
            utc_minute = dt.datetime.utcnow().minute
            # format tz string
            if user_json["tz"] >= 0:
                tz_str = "+" + str(user_json["tz"])
            else:
                tz_str = str(user_json["tz"])
            await ctx.send(f"Set your timezone to UTC**{tz_str}**. (now {user_hour}:{utc_minute})")
            await ctx.send("Setup complete! Don't forget `help` and `about` if you need info or get stuck. Enjoy using Cornbot!"
                           f"\n\n"
                           "*Not sure where to start? Try* `list prompts`*.*")
        # arg was not a valid number
        else:
            await ctx.send("Couldn't parse number; accepts values from -11 to 14.")
            await ctx.send("Use `list timezone` to see current times.")

@client.command()
async def reset(ctx, arg=None):
    """
    Command to reset logs, breaks, prompts, or all data.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author.id in util.registered_users:
        if not arg:
            await ctx.send("Usage: `reset <all, breaks, logs, prompts>`"
                           "\n**WARNING:** any reset data will be permanently erased!")
        elif arg == "all":
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # delete user's scheduled prompts from hour jsons
            for time in user_json["prompts"]:
                delete_prompt_from_hr(ctx.author.id, user_json, time)
            # delete user json
            os.remove(f"users/{ctx.author.id}.json")
            # delete user logs, if they exist
            if os.path.exists(f"users/{ctx.author.id}.csv"):
                os.remove(f"users/{ctx.author.id}.csv")
            # remove user from registered_users
            util.registered_users.remove(ctx.author.id)
            await ctx.send("All data deleted.\n\nIf you want to re-setup, say `timezone`.")
        elif arg =="breaks":
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # reset breaks to default
            user_json["breaks"] = {"default":70}
            # save/overwrite user json
            with open(f"users/{ctx.author.id}.json", "w") as file:
                json.dump(user_json, file)
            await ctx.send("All break reminder settings have been deleted/reset to default.")
        elif arg == "logs":
            # delete user logs, if they exist
            if os.path.exists(f"users/{ctx.author.id}.csv"):
                os.remove(f"users/{ctx.author.id}.csv")
                await ctx.send("All logs have been deleted.")
            else:
                await ctx.send("No logs found.")
        elif arg == "prompts":
            # load user json
            with open(f"users/{ctx.author.id}.json", "r") as file:
                user_json = json.load(file)
            # delete user's schedule prompts from hour jsons
            for time in user_json["prompts"]:
                delete_prompt_from_hr(ctx.author.id, user_json, time)
            # reset prompts to default
            user_json["prompts"] = {"20:00":"What's something you did today that you're proud of?"}
            # schedule newly reset prompt to hour json
            schedule_prompt_to_hr(ctx.author.id, user_json, "20:00")
            # save/overwrite user json
            with open(f"users/{ctx.author.id}.json", "w") as file:
                json.dump(user_json, file)
            await ctx.send("All prompt data has reset to default.")
        # arg was something else, send usage
        else:
            await ctx.send("Usage: `reset <all, breaks, logs, prompts>`"
                           "\n**WARNING:** any reset data will be permanently erased!")
            
@client.command()
async def about(ctx):
    """
    Command to display the about blurb.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send(helpstrings.ABOUT)

@client.command()
async def respond(ctx):
    """
    Adds a check mark reaction to the given response.
    """
    if isinstance(ctx.channel, discord.channel.DMChannel):
        msg = None
        messages = [m async for m in ctx.channel.history(limit=2)]
        msg = await ctx.channel.fetch_message(messages[0].id)
        await msg.add_reaction("\U00002705")


#################### FUNCTIONS ####################

def schedule_prompt_to_hr(user_id: int, user_json: dict, arg: str):
    """
    Schedules a prompt to its correct hour json. Not a command, just for internal use.
    Basically a stripped down version of schedule() that doesn't send messages.
    """
    # use user's timezone to determine which utc hour json to edit
    utc_hour = (int(arg[:2]) - user_json["tz"]) % 24
    # load hour json
    with open(f"times/{utc_hour}.json", "r") as file:
        hour_json = json.load(file)
    # if there are no prompts scheduled at this minute, make empty list
    if arg[3:] not in hour_json.keys():
        hour_json[arg[3:]] = []
    # append the user's id to the scheduled minute list
    hour_json[arg[3:]].append(user_id)
    # save/overwrite hour json
    with open(f"times/{utc_hour}.json", "w") as file:
        json.dump(hour_json, file)
    # if user just scheduled a time in the current hour, update the prompt loop with new times
    if dt.datetime.utcnow().hour == utc_hour:
        prompt_users.change_interval(time=util.populate_times(hour_json, utc_hour))
        prompt_users.restart()
        util.current_hour_json = hour_json

def delete_prompt_from_hr(user_id: int, user_json: dict, arg: str):
    """
    Deletes a prompt from its hour json. Not a command, just for internal use.
    Basically a stripped down version of delete() that doesn't send messages.
    """
    # get the hour of the given time in utc
    utc_hour = (int(arg[:2]) - user_json["tz"]) % 24
    # load hour json
    with open(f"times/{utc_hour}.json", "r") as file:
        hour_json = json.load(file)
    # remove user's id from the minute list, deleting their timeslot
    hour_json[arg[3:]].remove(user_id)
    # if minute list is now empty, pop it
    if len(hour_json[arg[3:]]) == 0:
        hour_json.pop(arg[3:])
    # if deleted time is in the current hour, update the prompt loop
    if dt.datetime.utcnow().hour == utc_hour:
        prompt_users.change_interval(time=util.populate_times(hour_json, utc_hour))
        prompt_users.restart()
        util.current_hour_json = hour_json
    # save/overwrite hour json
    with open(f"times/{utc_hour}.json", "w") as file:
        json.dump(hour_json, file)


#################### LOOPS ####################

@tasks.loop()
async def prompt_users():
    """
    Sends users their prompts when they are scheduled.
    Uses a list of times to determine when to run.
    Uses util.current_hour_json to fetch user id's.
    """
    # do not run at 0:00:13, which indicates no times this hour
    if prompt_users.time[0].second == 13:
        return
    # grab the minute int for the current time and make it a string format "MM"
    utcnow_mins = str(dt.datetime.utcnow().minute)
    if len(utcnow_mins) < 2:
        utcnow_mins = "0" + utcnow_mins
    # look in current_hour_json for list of users who have a prompt at this minute
    for user_id_ in util.current_hour_json[utcnow_mins]:
        # load user json
        with open(f"users/{user_id_}.json", "r") as file:
            user_json = json.load(file)
            # adjust current hour to user's timezone
            user_tz = user_json["tz"]
            hour_to_user = str((dt.datetime.utcnow().hour + user_tz) % 24)
            # add a 0 to hour if need, so format is "HH"
            if len(hour_to_user) < 2:
                hour_to_user = "0" + hour_to_user
            time_to_user = f"{hour_to_user}:{utcnow_mins}"
        # fetch user id and send them prompt contents from their json
        user = await client.fetch_user(user_id_)
        await user.send(user_json["prompts"][time_to_user])

@tasks.loop(time=HOURLY_UPDATE_TIMES)
async def hourly_update():
    """
    Runs every hour using HOURLY_UPDATE_TIMES.
    Updates util.current_hour_json to current time.
    Refreshes prompt_users to the new times.
    """
    utcnow_hour = dt.datetime.utcnow().hour
    with open(f"times/{utcnow_hour}.json", "r") as file:
        hour_json = json.load(file)
        prompt_users.change_interval(time=util.populate_times(hour_json, utcnow_hour))
        prompt_users.restart()
        util.current_hour_json = hour_json

@tasks.loop(minutes=1)
async def break_check():
    """
    Runs every minute. Checks the activity status of every registered member
    and sends them their break reminders when it's time.
    """
    # all members that the bot can see
    for member in client.get_all_members():
        # if user is registered
        if member.id in util.registered_users:
            # grab the current game the user is playing, if it exists
            game = None
            for activity in member.activities:
                # if isinstance(activity, discord.Game):
                game = activity
            if not game:
                pass
            # if game does exist
            else:
                # load user json to find out when next reminder should be
                with open(f"users/{member.id}.json", "r") as file:
                    user_json = json.load(file)
                # if the user has a preference for the current game, use it
                if game.name.lower() in user_json["breaks"]:
                    break_pref = dt.timedelta(minutes=user_json["breaks"][game.name.lower()])
                # if no preference, just use their default value
                else:
                    break_pref = dt.timedelta(minutes=user_json["breaks"]["default"])
                # elapsed_time = how much time has passed since user started playing game (0:02 = 5:32 - 5:30)
                elapsed_time = dt.datetime.utcnow - game.start
                # elapsed % pref = how much time since last reminder should have happened
                # this allows reminders to reoccur at their correct interval (instead of happening once)
                # here we check if the modulus is <1 min, which should catch everything
                # since function runs every 1 min (and negative elapsed shouldn't be possible)
                if elapsed_time % break_pref < dt.timedelta(minutes=1):
                    await member.send("Time for a break? If you need,\n"
                                "- Get some food\n"
                                "- Get some water\n"
                                "- Stretch or move around! :)")
                else:
                    pass



# GOOOOO!
client.run('MTEwNjQxMjU1NzQ1NzE4Mjc1MQ.GhPii7.VzVD9Wn21SH_sD7uep64AepJreWUDz6fL6dj6w')