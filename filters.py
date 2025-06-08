from datetime import datetime
from utils import format_file_size

def format_datetime(value, format='%d.%m.%Y %H:%M'):
    """Форматирует дату и время"""
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

def nl2br(value):
    """Заменяет переносы строк на HTML-теги <br>"""
    if not value:
        return ''
    return value.replace('\n', '<br>')

def format_filesize(value):
    """Форматирует размер файла"""
    if not value:
        return ''
    return format_file_size(value)

def time_ago(value):
    """Возвращает время в формате 'X времени назад'"""
    if not isinstance(value, datetime):
        return value
    
    now = datetime.utcnow()
    diff = now - value
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} {'год' if years == 1 else 'года' if 1 < years < 5 else 'лет'} назад"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} {'месяц' if months == 1 else 'месяца' if 1 < months < 5 else 'месяцев'} назад"
    elif diff.days > 0:
        return f"{diff.days} {'день' if diff.days == 1 else 'дня' if 1 < diff.days < 5 else 'дней'} назад"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} {'час' if hours == 1 else 'часа' if 1 < hours < 5 else 'часов'} назад"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} {'минуту' if minutes == 1 else 'минуты' if 1 < minutes < 5 else 'минут'} назад"
    else:
        return 'только что'

def truncate(value, length=100):
    """Обрезает текст до указанной длины"""
    if not value:
        return ''
    if len(value) <= length:
        return value
    return value[:length] + '...'

def markdown(value):
    """Преобразует Markdown в HTML"""
    if not value:
        return ''
    
    # Простая реализация основных элементов Markdown
    lines = value.split('\n')
    result = []
    in_list = False
    
    for line in lines:
        # Заголовки
        if line.startswith('#'):
            level = len(line.split()[0])
            text = line[level:].strip()
            result.append(f'<h{level}>{text}</h{level}>')
            continue
        
        # Списки
        if line.startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{line[2:]}</li>')
            continue
        elif in_list:
            result.append('</ul>')
            in_list = False
        
        # Жирный текст
        line = line.replace('**', '<strong>', 1)
        line = line.replace('**', '</strong>', 1)
        
        # Курсив
        line = line.replace('*', '<em>', 1)
        line = line.replace('*', '</em>', 1)
        
        # Ссылки
        if '[' in line and '](' in line and ')' in line:
            parts = line.split('](')
            if len(parts) == 2:
                text = parts[0][1:]
                url = parts[1].split(')')[0]
                line = f'<a href="{url}">{text}</a>'
        
        result.append(line)
    
    if in_list:
        result.append('</ul>')
    
    return '\n'.join(result)

def init_app(app):
    """Регистрирует фильтры в приложении"""
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['filesize'] = format_filesize
    app.jinja_env.filters['timeago'] = time_ago
    app.jinja_env.filters['truncate'] = truncate
    app.jinja_env.filters['markdown'] = markdown 