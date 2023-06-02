import datetime as dt
import pandas as pd
import json

CLIENT_LOCAL_OFFSET = -7
CLIENT_LOCAL_TZ = dt.timezone(dt.timedelta(hours=CLIENT_LOCAL_OFFSET))
current_hour_json = {}
registered_users = []

def split_alpha_num(str: str):
    """
    Takes a string and splits it into its alphabetical elements and numeric elements.
    Input must be only letters, numbers, and spaces (no punctuation).
    Returns a list.

    EXAMPLE: "2numbers2words" -> ["2", "numbers", "2", "words"]
    """
    # check that input is alphanumeric
    if not "".join(str.split(" ")).isalnum():
        raise ValueError("String contains non-alphanumeric characters")
    list_to_return = []
    # loop until string is empty
    while str != "":
        # strip numbers off the right side of the string and insert them at list head
        temp_str = str.rstrip("0123456789")
        list_to_return.insert(0, str[len(temp_str):])
        str = temp_str
        # strip letters off the right side of the string and insert them at list head
        temp_str = str.rstrip("qwertyuiopasdfghjklzxcvbnm")
        list_to_return.insert(0, str[len(temp_str):])
        str = temp_str
        # strip spaces off the right side of the string
        str = str.rstrip(" ")
    # remove empty string elements from list and return
    list_to_return = list(filter(None, list_to_return))
    return list_to_return

def get_timedelta(row: str or dt.datetime, column: str, dataframe: pd.DataFrame):
    """
    Returns a timedelta object out of a dataframe at a given location.

    ROW: can be a str or a datetime object
    COLUMN: str, such as name of activity
    DATAFRAME: pandas.dataframe object, with dates as the indexes
    """
    # split time on colon (0:00:00 -> ["0", "00", "00"])
    try:
        split_list = dataframe.loc[str(row), column].split(":")
    # KeyError means that today's date index doesn't exist yet
    # so nothing has been logged yet today, return 0 time
    except KeyError:
        return dt.timedelta(seconds=0)
    # AttributeError happens when it tries to .split() a float
    # which means it found no value there in the csv, return 0 time
    except AttributeError:
        return dt.timedelta(seconds=0)
    # if list is empty, indicating an empty string, assume 0 time
    if len(split_list) == 0:
        return dt.timedelta(seconds=0)
    else:
        # int cast each list element from strings
        split_list = [int(i) for i in split_list]
        return dt.timedelta(hours=split_list[0], minutes=split_list[1], seconds=split_list[2])
    
def display_log(dataframe: pd.DataFrame, activity: str=None):
    """
    Returns a string, formatted to be sent in Discord, from a given dataframe.

    DATAFRAME: pandas.dataframe object, with dates as the indexes
    ACTIVITY: optional, str name of a column in the dataframe
    """
    # if no activity was specified
    if activity is None:
        str_to_return = f"ACTIVITY [TOTAL TIME]\n"
        # find total time logged for each column/activity in the log
        for column in dataframe.columns:
            total_time = dt.timedelta(seconds=0)
            for date in dataframe.index:
                total_time += get_timedelta(date, column, dataframe)
            # add the column/activity name & total to the string
            str_to_return += f"\n`{column}` [{total_time}]"
    # if an activity was specified
    else:
        str_to_return = f"`{activity}`\n\nLast 7 days:"
        # counts the last 7 days
        counter = 0
        total_time = dt.timedelta(seconds=0)
        # get the time logged for every date under this activity
        for date in dataframe.index:
            time = get_timedelta(date, activity, dataframe)
            # if it's in last 7 days, add it to string
            if counter < 7:
                str_to_return += f"\n{date} [{time}]"
            # total up all times
            total_time += time
            counter += 1
        # add total to string
        str_to_return += f"\n\nTotal: [{total_time}]"
    return str_to_return

def display_prompt(json: dict):
    """
    Returns a string, formatted to be sent in Discord, of a user's prompts.

    JSON: user json object containing prompts
    """
    if len(json["prompts"]) == 0:
        return "No prompts found."
    else:
        str_list = []
        times = list(json["prompts"].keys())
        contents = list(json["prompts"].values())
        for i in range(len(times)):
            str_list.append(f"{i+1}) {times[i]} - {contents[i]}")
        return f"\n".join(str_list)

def now():
    """
    Returns a datetime.time object with the current local time.
    """
    n = dt.datetime.now()
    return dt.time(hour=n.hour, minute=n.minute, second=n.second, tzinfo=n.tzinfo)

def utcnow():
    """
    Returns a datetime.time object with the current UTC time.
    """
    n = dt.datetime.utcnow()
    return dt.time(hour=n.hour, minute=n.minute, second=n.second)

def get_tz(json):
    """
    Returns a datetime.timezone object from a user json object.
    """
    return dt.timezone(dt.timedelta(hours=json["tz"]))

def populate_times(json: dict, hr: int):
    """
    Returns a list populated with datetime.time objects from an hour json object.
    OR
    Returns a single datetime.time object with time 0:00:13 if json is empty.

    JSON: json object containing times
    HR: which hour of the day in UTC the json corresponds to
    """
    # grab keys from json, which are minutes as strings "MM"
    list_to_return = list(json.keys())
    if len(list_to_return) > 0:
        # update hr to local time
        hr = (hr + CLIENT_LOCAL_OFFSET) % 24
        # turn each minute value into its corresponding dt.time using local tz
        for i in range(len(list_to_return)):
            # if time is exactly on the hour, add 15 seconds to time
            # this is to give time for hourly_update() to run before prompt_users()
            if int(list_to_return[i]) == 0:
                list_to_return[i] = dt.time(hour=hr, minute=int(list_to_return[i]), second=15, tzinfo=CLIENT_LOCAL_TZ)
            else:
                list_to_return[i] = dt.time(hour=hr, minute=int(list_to_return[i]), tzinfo=CLIENT_LOCAL_TZ)
        return list_to_return
    else:
        return dt.time(hour=0, second=13, tzinfo=CLIENT_LOCAL_TZ)
    
def validate_time(str: str):
    """
    Returns True if a string is in the format "H:MM" or "HH:MM".
    """
    list = str.split(":")
    if len(list) == 2 and list[0].isnumeric() and list[1].isnumeric():
        if int(list[0]) in range(24) and int(list[1]) in range(60) and len(list[1]) > 1:
            return True
        else:
            return False
    else:
        return False
    
def validate_signed_num(str: str):
    """
    Returns True if a string is numeric with a "+" or "-" sign.
    """
    str = str.lstrip("+-")
    return str.isnumeric()
    
def display_timezones():
    """
    Returns a string, formatted to be sent in Discord, of all supported timezones.
    """
    now = dt.datetime.utcnow()
    str_to_return = ""
    for i in range (-11, 15):
        # format offset string
        if i >= 0:
            offset = "+" + str(i)
        else:
            offset = str(i)
        # format localized time string
        local_time = str(now + dt.timedelta(hours=i))[:16]
        # append to string
        str_to_return += f"\n**{offset}** = {local_time}"
    str_to_return += f"\n\nCheck https://timeanddate.com/time/map/ for more info."
    return str_to_return

def display_breaks(json: dict):
    """
    Returns a string, formatted to be sent in Discord, of a user's break preferences.
    Takes a registered user json.
    """
    str_list = []
    games = list(json["breaks"].keys())
    times = [dt.timedelta(minutes=n) for n in list(json["breaks"].values())]
    for i in range(len(games)):
        if i == 0:
            str_list.append(f"default - {times[i]}")
        else:
            str_list.append(f"`{games[i]}` - {times[i]}")
    return "\n".join(str_list)

def parse_time_from_args(list: list):
    """
    Takes a list of args split using split_alpha_num() and parses a time from it.
    Returns a list of the remaining args that were not part of the time,
    and a datetime.timedelta object of the amount of time parsed.

    If no valid time gets parsed, False will be returned instead of a timedelta.
    """
    time = dt.timedelta(seconds=0)
    # create items_parsed list that basically marks items for deletion from the main list
    items_parsed_as_time = []
    for item in list:
        if item.isnumeric():
            temp_number = int(item)
        elif item.isalpha():
            if "hours ".startswith(item):
                time += dt.timedelta(hours=temp_number)
                items_parsed_as_time.append(str(temp_number))
                items_parsed_as_time.append(item)
            elif "minutes ".startswith(item):
                time += dt.timedelta(minutes=temp_number)
                items_parsed_as_time.append(str(temp_number))
                items_parsed_as_time.append(item)
            else:
                pass
    if len(items_parsed_as_time) == 0:
        return list, False
    else:
        # move through list backwards and remove matches
        list.reverse()
        for item in items_parsed_as_time:
            list.remove(item)
        list.reverse()
        return list, time