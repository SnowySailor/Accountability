import api

def get_subject(subject_id: int, token: str, reload: bool = False) -> Union[dict, None]:
    key = f'subject:v2:{subject_id}'
    def callback():
        return api.get_subject(subject_id, token)
    return remember(key, callback, 60*60*24*14)

def get_user(token: str) -> Union[dict, None]:
    key = f'user:v1:{sha256(token.encode("utf-8")).hexdigest()}'
    def callback():
        return api.get_user(token)
    return remember(key, callback, 60*5)

def get_user_stats(token: str) -> dict:
    user_stats = {}
    response = api.get_user_level_progression_info(token)
    if len(response) == 0:
        user_stats['Level'] = 0
    else:
        user_stats['Level'] = response[-1]['data']['level']

    user_stats['Available reviews'] = api.get_number_of_reviews_available_now(token)

    response = api.get_number_of_lessons_available_now(token)
    user_stats['Available lessons'] = response['total_count']

    return user_stats
