from app import create_app, db
from models import Board
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Проверка состояния базы данных."""
    try:
        # Проверяем подключение к базе данных
        result = db.session.execute(text('SELECT current_database()')).scalar()
        logger.info(f"Подключено к базе данных: {result}")
        
        # Проверяем существование таблицы boards
        result = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'boards'
            )
        """)).scalar()
        logger.info(f"Таблица boards существует: {result}")
        
        if result:
            # Получаем количество записей в таблице
            count = db.session.execute(text('SELECT COUNT(*) FROM boards')).scalar()
            logger.info(f"Количество записей в таблице boards: {count}")
            
            # Получаем все записи
            boards = db.session.execute(text('SELECT * FROM boards')).fetchall()
            for board in boards:
                logger.info(f"Найдена доска: {board}")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке базы данных: {str(e)}")

def check_board():
    app = create_app()
    with app.app_context():
        try:
            # Проверяем состояние базы данных
            check_database()
            
            # Проверяем все доски через ORM
            all_boards = Board.query.all()
            logger.info(f"Всего досок в базе (через ORM): {len(all_boards)}")
            
            for board in all_boards:
                logger.info(f"Найдена доска через ORM: {board.name} (ID: {board.id})")
            
            # Проверяем конкретную доску
            board = Board.query.filter_by(name='board').first()
            if board:
                logger.info(f"Доска 'board' найдена:")
                logger.info(f"ID: {board.id}")
                logger.info(f"Имя: {board.name}")
                logger.info(f"Заголовок: {board.title}")
                logger.info(f"Описание: {board.description}")
                logger.info(f"Заблокирована: {board.is_locked}")
                logger.info(f"Скрыта: {board.is_hidden}")
            else:
                logger.warning("Доска 'board' не найдена в базе данных")
                
        except Exception as e:
            logger.error(f"Ошибка при проверке доски: {str(e)}")

if __name__ == '__main__':
    check_board() 