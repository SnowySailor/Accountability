import datetime
import pytz

def get_current_time_for_user(user_id):
    return datetime.datetime.now(pytz.timezone('America/New_York'))
