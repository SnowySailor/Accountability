from datetime import datetime, timezone, timedelta
import requests

def get_new_assignments_this_hour(token: str) -> list:
    (start, end) = get_current_and_next_hour_formatted()
    params = {
        'available_after': start,
        'available_before': end
    }
    assignments = do_wk_get('https://api.wanikani.com/v2/assignments', token, params=params)
    if assignments is None:
        return []
    return assignments

def do_wk_get(url: str, token: str, params = {}, headers = {}):
    headers['Authorization'] = f'Bearer {token}'
    headers['Wanikani-Revision'] = '20170710'

    try:
        result = requests.get(url, headers=headers, params=params)
        return result.json()['data']
    except:
        return None

def get_current_and_next_hour_formatted() -> str:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    next_hour = now + timedelta(hours=1, minutes=-1)
    return (now.strftime('%Y-%m-%dT%H:%M:%S.000000Z'), next_hour.strftime('%Y-%m-%dT%H:%M:%S.000000Z'))
