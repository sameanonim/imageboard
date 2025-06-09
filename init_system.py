from app import create_app, db
from models import Board, User

def init_system():
    app = create_app()
    with app.app_context():
        # Создание доски /b/
        existing_board = Board.query.filter_by(name='b').first()
        if existing_board:
            print("Доска /b/ уже существует")
        else:
            board = Board(
                name='b',
                title='Random',
                description='Случайные темы и обсуждения',
                is_locked=False,
                is_hidden=False
            )
            try:
                db.session.add(board)
                db.session.commit()
                print("Доска /b/ успешно создана")
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при создании доски: {str(e)}")

        # Создание администратора
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            print("Пользователь admin уже существует")
        else:
            admin = User(
                username='admin',
                email='admin@example.com',
                password='admin'
            )
            admin.is_superadmin = True
            
            try:
                db.session.add(admin)
                db.session.commit()
                print("Администратор успешно создан")
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при создании администратора: {str(e)}")

if __name__ == '__main__':
    init_system() 
