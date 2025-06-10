from app import create_app, db
from models import Board, User
from werkzeug.security import generate_password_hash
import logging
import time
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_on_deadlock(func, max_attempts=3, delay=1):
    """Декоратор для повторных попыток при deadlock."""
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if "deadlock detected" in str(e).lower():
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    logger.warning(f"Обнаружен deadlock, попытка {attempts} из {max_attempts}")
                    time.sleep(delay)
                else:
                    raise
    return wrapper

@retry_on_deadlock
def create_board(app):
    """Создание доски с обработкой транзакций."""
    with app.app_context():
        existing_board = Board.query.filter_by(name='board').first()
        if existing_board:
            logger.info(f"Доска /board/ уже существует (ID: {existing_board.id})")
            return existing_board
            
        board = Board(
            name='board',
            title='Random',
            description='Случайные темы и обсуждения',
            is_locked=False,
            is_hidden=False
        )
        
        try:
            db.session.add(board)
            db.session.commit()
            logger.info(f"Доска /board/ успешно создана (ID: {board.id})")
            
            # Проверяем создание
            created_board = Board.query.filter_by(name='board').first()
            if created_board:
                logger.info(f"Подтверждение: доска создана (ID: {created_board.id})")
                return created_board
            else:
                raise Exception("Доска не найдена после создания")
                
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании доски: {str(e)}")
            raise

@retry_on_deadlock
def create_admin(app):
    """Создание администратора с обработкой транзакций."""
    with app.app_context():
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            logger.info(f"Пользователь admin уже существует (ID: {existing_user.id})")
            return existing_user
            
        admin = User(
            username='admin',
            email='admin@example.com',
            password='Admin123!'
        )
        admin.is_superadmin = True
        
        try:
            db.session.add(admin)
            db.session.commit()
            logger.info(f"Администратор успешно создан (ID: {admin.id})")
            
            # Проверяем создание
            created_admin = User.query.filter_by(username='admin').first()
            if created_admin:
                logger.info(f"Подтверждение: администратор создан (ID: {created_admin.id})")
                return created_admin
            else:
                raise Exception("Администратор не найден после создания")
                
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании администратора: {str(e)}")
            raise

def init_system():
    app = create_app()
    try:
        # Создаем доску
        board = create_board(app)
        if board:
            logger.info("Доска успешно инициализирована")
        
        # Создаем администратора
        admin = create_admin(app)
        if admin:
            logger.info("Администратор успешно инициализирован")
            logger.info("Логин: admin")
            logger.info("Пароль: Admin123!")
            
    except Exception as e:
        logger.error(f"Критическая ошибка при инициализации системы: {str(e)}")
        raise

if __name__ == '__main__':
    init_system() 
