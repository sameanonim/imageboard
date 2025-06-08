from datetime import datetime
import json

ACHIEVEMENTS = {
    'first_post': {
        'id': 'first_post',
        'title': 'Первый пост!',
        'description': 'Создал свой первый пост',
        'icon': '📝'
    },
    'thread_master': {
        'id': 'thread_master',
        'title': 'Мастер тредов',
        'description': 'Создал 5 тредов',
        'icon': '🧵',
        'required_count': 5
    },
    'night_owl': {
        'id': 'night_owl',
        'title': 'Ночная сова',
        'description': 'Написал пост в 3 часа ночи',
        'icon': '🦉'
    },
    'early_bird': {
        'id': 'early_bird',
        'title': 'Ранняя пташка',
        'description': 'Написал пост в 6 утра',
        'icon': '🐦'
    },
    'weekend_warrior': {
        'id': 'weekend_warrior',
        'title': 'Воин выходного дня',
        'description': 'Написал пост в субботу или воскресенье',
        'icon': '⚔️'
    },
    'file_hoarder': {
        'id': 'file_hoarder',
        'title': 'Собиратель файлов',
        'description': 'Загрузил 10 файлов',
        'icon': '📁',
        'required_count': 10
    },
    'gif_master': {
        'id': 'gif_master',
        'title': 'Мастер GIF',
        'description': 'Загрузил 5 GIF-анимаций',
        'icon': '🎬',
        'required_count': 5
    },
    'quick_replier': {
        'id': 'quick_replier',
        'title': 'Быстрый ответчик',
        'description': 'Ответил на пост в течение минуты',
        'icon': '⚡'
    },
    'thread_reviver': {
        'id': 'thread_reviver',
        'title': 'Оживитель тредов',
        'description': 'Ответил в треде старше недели',
        'icon': '💉'
    },
    'lurker': {
        'id': 'lurker',
        'title': 'Луркер',
        'description': 'Просмотрел 100 тредов',
        'icon': '👀',
        'required_count': 100
    }
}

def check_achievements(request, post_data=None):
    """
    Проверяет и обновляет достижения пользователя.
    
    Args:
        request: Объект запроса Flask
        post_data: Данные о посте (опционально)
    
    Returns:
        list: Список новых достижений
    """
    # Получаем текущие достижения из куки
    current_achievements = json.loads(
        request.cookies.get('achievements', '[]')
    )
    
    # Получаем статистику из куки
    stats = json.loads(
        request.cookies.get('user_stats', '{}')
    )
    
    new_achievements = []
    
    # Проверяем достижения, связанные с постами
    if post_data:
        # Первый пост
        if 'first_post' not in current_achievements:
            new_achievements.append(ACHIEVEMENTS['first_post'])
        
        # Ночная сова
        if datetime.now().hour == 3 and 'night_owl' not in current_achievements:
            new_achievements.append(ACHIEVEMENTS['night_owl'])
        
        # Ранняя пташка
        if datetime.now().hour == 6 and 'early_bird' not in current_achievements:
            new_achievements.append(ACHIEVEMENTS['early_bird'])
        
        # Воин выходного дня
        if datetime.now().weekday() >= 5 and 'weekend_warrior' not in current_achievements:
            new_achievements.append(ACHIEVEMENTS['weekend_warrior'])
        
        # Быстрый ответчик
        if post_data.get('is_reply') and post_data.get('reply_time', 0) < 60:
            if 'quick_replier' not in current_achievements:
                new_achievements.append(ACHIEVEMENTS['quick_replier'])
        
        # Оживитель тредов
        if post_data.get('thread_age', 0) > 7 and 'thread_reviver' not in current_achievements:
            new_achievements.append(ACHIEVEMENTS['thread_reviver'])
    
    # Обновляем статистику
    stats['posts'] = stats.get('posts', 0) + 1
    stats['threads'] = stats.get('threads', 0) + (1 if post_data and post_data.get('is_op') else 0)
    stats['files'] = stats.get('files', 0) + post_data.get('file_count', 0) if post_data else 0
    stats['gifs'] = stats.get('gifs', 0) + post_data.get('gif_count', 0) if post_data else 0
    stats['views'] = stats.get('views', 0) + 1
    
    # Проверяем достижения, основанные на статистике
    if stats['threads'] >= 5 and 'thread_master' not in current_achievements:
        new_achievements.append(ACHIEVEMENTS['thread_master'])
    
    if stats['files'] >= 10 and 'file_hoarder' not in current_achievements:
        new_achievements.append(ACHIEVEMENTS['file_hoarder'])
    
    if stats['gifs'] >= 5 and 'gif_master' not in current_achievements:
        new_achievements.append(ACHIEVEMENTS['gif_master'])
    
    if stats['views'] >= 100 and 'lurker' not in current_achievements:
        new_achievements.append(ACHIEVEMENTS['lurker'])
    
    # Обновляем список достижений
    current_achievements.extend([a['id'] for a in new_achievements])
    
    return {
        'new_achievements': new_achievements,
        'current_achievements': current_achievements,
        'stats': stats
    } 