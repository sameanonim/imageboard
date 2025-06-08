def format_file_size(size_in_bytes):
    """
    Форматирует размер файла в человекочитаемый формат
    """
    if not size_in_bytes:
        return '0 B'
        
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB" 