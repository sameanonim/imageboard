import click
from flask.cli import with_appcontext
from utils.archive import archive_old_threads, unarchive_thread
from utils.backup import create_backup, list_backups, restore_backup, delete_backup
from datetime import datetime

@click.command('archive-threads')
@click.option('--board-id', type=int, help='ID доски для архивации')
@click.option('--days', type=int, default=30, help='Возраст треда в днях для архивации')
@click.option('--max-replies', type=int, default=1000, help='Максимальное количество ответов')
@click.option('--reason', help='Причина архивации')
@with_appcontext
def archive_threads_command(board_id, days, max_replies, reason):
    """Архивирует старые треды."""
    archived = archive_old_threads(
        board_id=board_id,
        days=days,
        max_replies=max_replies,
        reason=reason
    )
    click.echo(f'Архивировано тредов: {archived}')

@click.command('unarchive-thread')
@click.argument('thread_id', type=int)
@click.option('--reason', help='Причина разархивации')
@with_appcontext
def unarchive_thread_command(thread_id, reason):
    """Разархивирует тред."""
    if unarchive_thread(thread_id, reason):
        click.echo(f'Тред {thread_id} разархивирован')
    else:
        click.echo(f'Тред {thread_id} не был архивирован')

@click.command('backup-create')
@with_appcontext
def backup_create():
    """Создает резервную копию базы данных и файлов."""
    try:
        backup = create_backup()
        click.echo(f'Резервная копия создана: {backup["timestamp"]}')
    except Exception as e:
        click.echo(f'Ошибка при создании резервной копии: {str(e)}', err=True)

@click.command('backup-list')
@with_appcontext
def backup_list():
    """Показывает список доступных резервных копий."""
    try:
        backups = list_backups()
        if not backups:
            click.echo('Резервные копии не найдены')
            return
            
        click.echo('Доступные резервные копии:')
        for backup in backups:
            timestamp = datetime.strptime(backup['timestamp'], '%Y%m%d_%H%M%S')
            click.echo(f'- {timestamp.strftime("%d.%m.%Y %H:%M:%S")} (версия: {backup["version"]})')
    except Exception as e:
        click.echo(f'Ошибка при получении списка резервных копий: {str(e)}', err=True)

@click.command('backup-restore')
@click.argument('timestamp')
@with_appcontext
def backup_restore(timestamp):
    """Восстанавливает резервную копию по временной метке."""
    try:
        restore_backup(timestamp)
        click.echo('Резервная копия успешно восстановлена')
    except Exception as e:
        click.echo(f'Ошибка при восстановлении резервной копии: {str(e)}', err=True)

@click.command('backup-delete')
@click.argument('timestamp')
@with_appcontext
def backup_delete(timestamp):
    """Удаляет резервную копию по временной метке."""
    try:
        delete_backup(timestamp)
        click.echo('Резервная копия успешно удалена')
    except Exception as e:
        click.echo(f'Ошибка при удалении резервной копии: {str(e)}', err=True)

def init_app(app):
    app.cli.add_command(backup_create)
    app.cli.add_command(backup_list)
    app.cli.add_command(backup_restore)
    app.cli.add_command(backup_delete) 