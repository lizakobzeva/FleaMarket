## Чек-лист выполнения практической работы

**Студент:** ____________________
**Микросервис:** ____________________

### PostgreSQL
- [x] Контейнер с PostgreSQL запущен (`docker ps`)
- [x] Подключение к БД работает (`docker exec -it myapp_db psql -U postgres -d mydb`)

### Зависимости
- [x] В requirements.txt есть sqlalchemy, psycopg2-binary, alembic, python-dotenv
- [x] Все зависимости установлены (`pip install -r requirements.txt`)

### Модели
- [x] Созданы Pydantic модели (Create, Update, Response)
- [x] Созданы SQLAlchemy модели (наследуются от Base)
- [x] Модели отражают предметную область

### Миграции
- [x] Alembic инициализирован (`alembic init alembic`)
- [x] Настроен alembic.ini (указан URL БД)
- [x] Настроен env.py (импортированы модели, указан target_metadata)
- [x] Создана первая миграция (`alembic revision --autogenerate -m "init"`)
- [x] Миграция применена (`alembic upgrade head`)
- [x] Таблица появилась в БД (`\dt` в psql)

### Эндпоинты
- [x] GET / - возвращает статус
- [x] GET /tasks - список (пустой или с данными)
- [x] GET /tasks/{id} - одна запись (404 для несуществующей)
- [x] POST /tasks - создание (возвращает id)
- [x] PUT /tasks/{id} - обновление
- [x] DELETE /tasks/{id} - удаление

### Проверка
- [x] Swagger UI открывается (/docs)
- [x] Все операции работают через Swagger
- [x] Данные сохраняются после перезапуска сервера
