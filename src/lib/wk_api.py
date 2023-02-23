import pytz
from datetime import datetime, timezone, timedelta
from dateutil import parser
import requests
from typing import Union
from ..internals.redis import get_redis, serialize, deserialize

def get_new_assignments_this_hour(token: str) -> list:
    (start, end) = get_current_and_next_hour_formatted()
    params = {
        'available_after': start,
        'available_before': end
    }
    assignments = do_wk_get('https://api.wanikani.com/v2/assignments', token, params=params)['data']
    if assignments is None:
        return []
    return assignments

def get_subject(subject_id: int, token: str, reload: bool = False) -> Union[dict, None]:
    redis = get_redis()
    key = f'subject:{subject_id}'
    subject = redis.get(key)
    if subject is None or reload:
        subject = do_wk_get(f'https://api.wanikani.com/v2/subjects/{subject_id}', token)['data']
        redis.set(key, serialize(subject))
    else:
        subject = deserialize(subject)
    return subject

def get_user(token: str) -> Union[dict, None]:
    return do_wk_get(f'https://api.wanikani.com/v2/user', token)['data']

def get_count_of_reviews_completed_yesterday(token: str, timezone: str) -> list:
    (start, end) = get_previous_day_for_timezone_start_and_end_formatted(timezone)
    return do_wk_get('https://api.wanikani.com/v2/reviews', token, params={'updated_after': start})['total_count']

def get_lessons_completed_yesterday(token: str, timezone: str) -> list:
    (start, end) = get_previous_day_for_timezone_start_and_end_formatted(timezone)
    params = {
        'updated_after': start,
        'started': 'true'
    }

    response = do_wk_get('https://api.wanikani.com/v2/assignments', token, params=params)
    updated_assignments = response['data']
    while response['pages']['next_url'] is not None:
        response = do_wk_get(response['pages']['next_url'], token)
        updated_assignments += response['data']

    today_start = datetime.now(pytz.timezone(timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
    previous_day_start = today_start - timedelta(days=1)

    started_yesterday = []
    for assignment in updated_assignments:
        started_date = parser.parse(assignment['data']['started_at'])
        if started_date > previous_day_start:
            started_yesterday.append(assignment)
    return started_yesterday

def get_count_of_reviews_available_before_end_of_yesterday(token: str, timezone: str) -> int:
    (start, end) = get_previous_day_for_timezone_start_and_end_formatted(timezone)
    end = parser.parse(end)
    # available_before is inclusive, so it will return reviews available at the specified time too
    # need to subtract 1 minute so it doesn't include reviews that just now became available
    end = (end - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    params = {
        'immediately_available_for_review': 'true',
        'available_before': end
    }
    return do_wk_get('https://api.wanikani.com/v2/assignments', token, params=params)['total_count']

def get_user_stats(token: str) -> dict:
    user_stats = {}
    response = do_wk_get('https://api.wanikani.com/v2/level_progressions', token)['data']
    if len(response) == 0:
        user_stats['Level'] = 0
    else:
        user_stats['Level'] = response[-1]['data']['level']

    user_stats['Available reviews'] = get_number_of_lessons_available_now(token)

    response = do_wk_get('https://api.wanikani.com/v2/assignments', token, {'immediately_available_for_lessons': True})
    user_stats['Available lessons'] = response['total_count']

    return user_stats

def get_number_of_lessons_available_now(token: str) -> int:
    return do_wk_get('https://api.wanikani.com/v2/assignments', token, {'immediately_available_for_review': True})['total_count']

def do_wk_get(url: str, token: str, params = {}, headers = {}, retries = 2):
    headers['Authorization'] = f'Bearer {token}'
    headers['Wanikani-Revision'] = '20170710'

    try:
        result = requests.get(url, headers=headers, params=params)
        return result.json()
    except:
        if retries < 1:
            return None
        return do_wk_get(url, token, params, headers, retries - 1)

def get_previous_day_for_timezone_start_and_end_formatted(timezone: str) -> tuple:
    today_start = datetime.now(pytz.timezone(timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = today_start.astimezone(pytz.utc)
    previous_day_start = today_start - timedelta(days=1)
    return (previous_day_start.strftime('%Y-%m-%dT%H:%M:%S.000000Z'), today_start.strftime('%Y-%m-%dT%H:%M:%S.000000Z'))

def get_current_and_next_hour_formatted() -> tuple:
    hour_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    next_hour = hour_start + timedelta(hours=1, minutes=-1)
    return (hour_start.strftime('%Y-%m-%dT%H:%M:%S.000000Z'), next_hour.strftime('%Y-%m-%dT%H:%M:%S.000000Z'))
