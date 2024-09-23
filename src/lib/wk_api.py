import pytz
import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta
from dateutil import parser
from hashlib import sha256
from typing import Union
from urllib.error import HTTPError

from ..internals.redis import remember_async
from src.utils.utils import parse_timestamp
from src.utils.logger import logtofile

async def get_new_assignments_this_hour(token: str) -> list:
    (start, end) = get_current_and_next_hour_formatted()
    params = {
        'available_after': start,
        'available_before': end
    }
    assignments = (await get_assignments(token, params))['data']
    if assignments is None:
        return []
    return assignments

async def get_subject(subject_id: int, token: str, reload: bool = False) -> Union[dict, None]:
    key = f'subject:v2:{subject_id}'
    async def callback():
        return (await do_wk_get(f'https://api.wanikani.com/v2/subjects/{subject_id}', token))['data']
    return await remember_async(key, callback, 60*60*24*14)

async def get_user(token: str) -> Union[dict, None]:
    key = f'user:v1:{sha256(token.encode("utf-8")).hexdigest()}'
    async def callback():
        return (await do_wk_get(f'https://api.wanikani.com/v2/user', token))['data']
    return await remember_async(key, callback, 60*1)

async def get_assignments(token: str, params: dict = {}, first_page_only=False) -> dict:
    assignments = await do_wk_get('https://api.wanikani.com/v2/assignments', token, params)
    response = assignments
    if not first_page_only:
        while response['pages']['next_url'] is not None:
            response = await do_wk_get(response['pages']['next_url'], token)
            assignments['data'] += response['data']
    del assignments['pages']
    return assignments

async def get_count_of_assignments_updated_yesterday(token: str, timezone: str) -> int:
    (start, _) = get_previous_day_for_timezone_start_and_end_formatted(timezone)
    params = {
        'updated_after': start,
        'started': 'true',
        'srs_stages': ','.join(['2','3','4','5','6','7','8','9'])
    }

    return (await get_assignments(token, params, first_page_only=True))['total_count']

async def get_lessons_completed_yesterday(token: str, timezone: str) -> list:
    (start, _) = get_previous_day_for_timezone_start_and_end_formatted(timezone)
    params = {
        'updated_after': start,
        'started': 'true'
    }

    updated_assignments = (await get_assignments(token, params))['data']

    today_start = datetime.now(pytz.timezone(timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
    previous_day_start = today_start - timedelta(days=1)

    started_yesterday = []
    for assignment in updated_assignments:
        started_date = parse_timestamp(assignment['data']['started_at'])
        if started_date > previous_day_start:
            started_yesterday.append(assignment)
    return started_yesterday

async def get_count_of_reviews_available_before_end_of_yesterday(token: str, timezone: str) -> int:
    (start, end) = get_previous_day_for_timezone_start_and_end_formatted(timezone)
    end = parse_timestamp(end)
    # available_before is inclusive, so it will return reviews available at the specified time too
    # need to subtract 1 minute so it doesn't include reviews that just now became available
    end = (end - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    params = {
        'immediately_available_for_review': 1,
        'available_before': end
    }
    return (await get_assignments(token, params, first_page_only=True))['total_count']

async def get_user_stats(token: str) -> dict:
    user_stats = {}
    response = (await get_user_level_progressions(token))['data']
    if len(response) == 0:
        user_stats['Level'] = 0
    else:
        user_stats['Level'] = response[-1]['data']['level']

    user_stats['Available reviews'] = await get_number_of_reviews_available_now(token)

    response = await get_assignments(token, {'immediately_available_for_lessons': 1}, first_page_only=True)
    user_stats['Available lessons'] = response['total_count']

    return user_stats

async def get_user_level_progressions(token: str) -> dict:
    return await do_wk_get('https://api.wanikani.com/v2/level_progressions', token)

async def get_number_of_reviews_available_now(token: str) -> int:
    return (await get_assignments(token, {'immediately_available_for_review': 1}, first_page_only=True))['total_count']

async def is_user_on_vacation_mode(token: str) -> bool:
    user = await get_user(token)
    if user['current_vacation_started_at'] is None:
        return False
    return True

async def do_wk_get(url: str, token: str, params = {}, headers = {}, retries = 2):
    headers['Authorization'] = f'Bearer {token}'
    headers['Wanikani-Revision'] = '20170710'

    status_code = None
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params, raise_for_status=True) as response:
                return await response.json()
    except aiohttp.ClientResponseError as e:
        status_code = e.code
    except Exception as e:
        pass

    if retries < 1:
        raise Exception(f'Failed to get {url} after 3 attempts. Last status code was {status_code}.') from None
    await asyncio.sleep(30) # Wait 30s before trying again
    return await do_wk_get(url, token, params, headers, retries - 1)

def get_previous_day_for_timezone_start_and_end_formatted(timezone: str) -> tuple:
    today_start = datetime.now(pytz.timezone(timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = today_start.astimezone(pytz.utc)
    previous_day_start = today_start - timedelta(days=1)
    return (previous_day_start.strftime('%Y-%m-%dT%H:%M:%S.000000Z'), today_start.strftime('%Y-%m-%dT%H:%M:%S.000000Z'))

def get_current_and_next_hour_formatted() -> tuple:
    hour_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    next_hour = hour_start + timedelta(hours=1, minutes=-1)
    return (hour_start.strftime('%Y-%m-%dT%H:%M:%S.000000Z'), next_hour.strftime('%Y-%m-%dT%H:%M:%S.000000Z'))
