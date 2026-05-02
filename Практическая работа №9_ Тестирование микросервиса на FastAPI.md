# **Практическая работа №9: Тестирование микросервиса на FastAPI**

## **1\. Цель работы**

Научиться писать unit-тесты и интеграционные тесты для микросервиса на FastAPI.  
В результате вы сможете:

* Проверять Pydantic-модели на корректность валидации.  
* Тестировать эндпоинты с реальной тестовой базой данных.  
* Использовать фикстуры для подготовки окружения (опционально).  
* Мокировать внешние вызовы (опционально).

Почему это важно: Тесты — это автоматическая проверка вашего кода. Они ловят ошибки до того, как их увидят пользователи. Без тестов вы не можете быть уверены, что код работает правильно, особенно после изменений.

---

## **2\. Теоретическая часть (читаем внимательно)**

### **2.1. Что такое тест?**

Тест — это маленькая программа, которая проверяет, что другая программа работает правильно.

Структура любого теста:

python

def test\_что\_проверяем():  
    *\# 1\. Подготовка (arrange) – создаём данные, настраиваем окружение*  
    *\# 2\. Действие (act) – вызываем тестируемую функцию*  
    *\# 3\. Проверка (assert) – сравниваем результат с ожидаемым*

    assert полученный\_результат \== ожидаемый\_результат

Что такое assert?  
assert — это ключевое слово Python, которое означает «утверждаю, что...». Если утверждение истинно — тест продолжается. Если ложно — тест падает с ошибкой.

python

assert 1 \+ 1 \== 2   *\# пройдёт*

assert 1 \+ 1 \== 3   *\# упадёт с AssertionError*

В тестах assert используется для проверки, что код вернул ожидаемый результат.

### **2.2. Виды тестов (напоминание)**

| Вид | Что проверяет | Пример |
| :---- | :---- | :---- |
| Unit-тест | Один маленький компонент (функцию, модель) в изоляции | Проверка, что Pydantic-модель не принимает пустое название |
| Интеграционный тест | Взаимодействие компонентов (эндпоинт \+ база данных) | Создание задачи через API и проверка, что она сохранилась в БД |

### **2.3. Инструменты для тестирования**

| Инструмент | Назначение |
| :---- | :---- |
| pytest | Фреймворк для написания и запуска тестов. Сам находит файлы test\_\*.py |
| TestClient | Эмуляция клиента FastAPI. Позволяет вызывать эндпоинты без запуска реального сервера |
| pytest-cov | Измерение покрытия кода (какой процент строк кода выполняется во время тестов) |
| pytest-asyncio | Для асинхронных тестов (если нужно) |
| unittest.mock | Подмена реальных компонентов на имитацию (мокирование) |

### **2.4. Что такое фикстура?**

Фикстура — это функция, которая подготавливает окружение для теста: создаёт базу данных, клиента, тестовые данные. В pytest фикстуры создаются через декоратор @pytest.fixture.

Пример простой фикстуры:

python

@pytest.fixture  
def sample\_task():  
    """Возвращает словарь с данными для теста."""

    return {"title": "Тестовая задача", "description": "Описание"}

Затем фикстуру можно использовать в тесте, передав как аргумент:

python

def test\_create\_task(sample\_task):

    assert sample\_task\["title"\] \== "Тестовая задача"

Зачем это нужно: Чтобы не повторять одну и ту же подготовку данных в каждом тесте.

### **2.5. Как тестировать эндпоинты без реального сервера**

TestClient создаёт объект, который имитирует HTTP-клиента. Вы просто вызываете client.get("/tasks"), и FastAPI обрабатывает этот запрос напрямую, без сети.

python

from fastapi.testclient import TestClient  
from app.main import app

client \= TestClient(app)

def test\_get\_tasks():  
    response \= client.get("/tasks")

    assert response.status\_code \== 200

### **2.6. Как подменить базу данных на тестовую**

В реальном проекте мы используем PostgreSQL. Для тестов удобнее использовать SQLite in-memory (база данных в оперативной памяти). Она быстрая и не требует установки.

В тестах мы подменяем функцию get\_db() так, чтобы она возвращала соединение с тестовой БД, а не с реальной. Это называется dependency override (подмена зависимости).

---

## **3\. Подготовка к работе**

### **3.1. Установка зависимостей**

Добавьте в requirements-dev.txt:

text

pytest  
pytest-cov

httpx

Установка:

bash

pip install pytest pytest-cov httpx

### **3.2. Структура проекта**

text

task\_manager/  
├── app/  
│   ├── \_\_init\_\_.py  
│   ├── main.py  
│   ├── models.py  
│   ├── schemas.py  
│   ├── database.py  
│   └── crud.py (если есть)  
├── tests/  
│   ├── \_\_init\_\_.py  
│   ├── test\_schemas.py      \# unit-тесты для Pydantic  
│   ├── test\_integration.py  \# интеграционные тесты  
│   └── conftest.py          \# общие фикстуры для всех тестов

└── requirements.txt

Папку tests нужно создать. В ней будут лежать все тесты.

---

## **4\. Пример кода микросервиса (Task Manager)**

Для работы с тестами нужно понимать, что мы тестируем. Вот упрощённый код микросервиса.

### **4.1. app/schemas.py – Pydantic-модели**

python

from pydantic import BaseModel  
from typing import Optional

*\# Модель для создания задачи (получаем от клиента)*  
class TaskCreate(BaseModel):  
    title: str  
    description: Optional\[str\] \= None  
    completed: bool \= False

*\# Модель для обновления задачи (все поля необязательны)*  
class TaskUpdate(BaseModel):  
    title: Optional\[str\] \= None  
    description: Optional\[str\] \= None  
    completed: Optional\[bool\] \= None

*\# Модель для ответа (отдаём клиенту, включая id)*  
class TaskResponse(BaseModel):  
    id: int  
    title: str  
    description: Optional\[str\]

    completed: bool

### **4.2. app/models.py – SQLAlchemy модель**

python

from sqlalchemy import Column, Integer, String, Boolean  
from app.database import Base

class Task(Base):  
    \_\_tablename\_\_ \= "tasks"  
    id \= Column(Integer, primary\_key\=True, index\=True)  
    title \= Column(String, nullable\=False)  
    description \= Column(String, nullable\=True)

    completed \= Column(Boolean, default\=False)

### **4.3. app/database.py – настройка БД**

python

from sqlalchemy import create\_engine  
from sqlalchemy.ext.declarative import declarative\_base  
from sqlalchemy.orm import sessionmaker

*\# В реальном проекте DATABASE\_URL берётся из .env*  
DATABASE\_URL \= "postgresql://user:pass@localhost/db"

engine \= create\_engine(DATABASE\_URL)  
SessionLocal \= sessionmaker(autocommit\=False, autoflush\=False, bind\=engine)  
Base \= declarative\_base()

def get\_db():  
    """Зависимость FastAPI. Возвращает сессию базы данных."""  
    db \= SessionLocal()  
    try:  
        yield db  
    finally:

        db.close()

### **4.4. app/main.py – эндпоинты**

python

from fastapi import FastAPI, Depends, HTTPException  
from sqlalchemy.orm import Session  
from typing import List  
from app import schemas, models  
from app.database import get\_db

app \= FastAPI()

*\# Создать задачу*  
@app.post("/tasks", response\_model\=schemas.TaskResponse, status\_code\=201)  
def create\_task(task: schemas.TaskCreate, db: Session \= Depends(get\_db)):  
    db\_task \= models.Task(\*\*task.dict())  *\# преобразуем Pydantic в SQLAlchemy*  
    db.add(db\_task)  
    db.commit()  
    db.refresh(db\_task)  *\# получаем сгенерированный id*  
    return db\_task

*\# Получить все задачи*  
@app.get("/tasks", response\_model\=List\[schemas.TaskResponse\])  
def get\_tasks(db: Session \= Depends(get\_db)):  
    return db.query(models.Task).all()

*\# Получить одну задачу по id*  
@app.get("/tasks/{task\_id}", response\_model\=schemas.TaskResponse)  
def get\_task(task\_id: int, db: Session \= Depends(get\_db)):  
    task \= db.get(models.Task, task\_id)  
    if not task:  
        raise HTTPException(status\_code\=404, detail\="Task not found")  
    return task

*\# Обновить задачу*  
@app.put("/tasks/{task\_id}", response\_model\=schemas.TaskResponse)  
def update\_task(task\_id: int, task\_update: schemas.TaskUpdate, db: Session \= Depends(get\_db)):  
    task \= db.get(models.Task, task\_id)  
    if not task:  
        raise HTTPException(status\_code\=404, detail\="Task not found")  
    *\# Обновляем только те поля, которые были переданы*  
    for field, value in task\_update.dict(exclude\_unset\=True).items():  
        setattr(task, field, value)  
    db.commit()  
    db.refresh(task)  
    return task

*\# Удалить задачу*  
@app.delete("/tasks/{task\_id}")  
def delete\_task(task\_id: int, db: Session \= Depends(get\_db)):  
    task \= db.get(models.Task, task\_id)  
    if not task:  
        raise HTTPException(status\_code\=404, detail\="Task not found")  
    db.delete(task)  
    db.commit()

    return {"detail": "Task deleted"}

---

## **5\. Настройка тестов (файл tests/conftest.py)**

Этот файл содержит общие настройки для всех тестов. Здесь мы создаём фикстуры.

python

"""  
conftest.py – общие фикстуры для всех тестов.  
Фикстуры – это функции, которые подготавливают окружение перед тестом.  
"""

import pytest  
from fastapi.testclient import TestClient  
from sqlalchemy import create\_engine  
from sqlalchemy.orm import sessionmaker  
from sqlalchemy.pool import StaticPool

from app.main import app  
from app.database import Base, get\_db  
from app import models  *\# импортируем модели, чтобы они зарегистрировались в Base*

*\# \============================================================*  
*\# 1\. Тестовая база данных (SQLite in-memory)*  
*\# \============================================================*  
*\# SQLite in-memory – база данных, которая живёт в оперативной памяти.*  
*\# Она очень быстрая и не требует установки.*  
*\# StaticPool нужен, чтобы соединение не закрывалось между вызовами.*  
SQLALCHEMY\_DATABASE\_URL \= "sqlite:///:memory:"  
engine \= create\_engine(  
    SQLALCHEMY\_DATABASE\_URL,  
    connect\_args\={"check\_same\_thread": False},  *\# необходимо для SQLite*  
    poolclass\=StaticPool,  
)

*\# Создаём все таблицы в тестовой БД (один раз перед запуском тестов)*  
Base.metadata.create\_all(bind\=engine)

*\# Фабрика сессий для тестовой БД*  
TestingSessionLocal \= sessionmaker(autocommit\=False, autoflush\=False, bind\=engine)

*\# \============================================================*  
*\# 2\. Фикстура: сессия базы данных для каждого теста*  
*\# \============================================================*  
@pytest.fixture  
def db\_session():  
    """  
    Фикстура, которая создаёт новую сессию БД для каждого теста.  
    После теста данные откатываются (rollback), чтобы следующий тест  
    начинался с чистой базы.  
    """  
    *\# Открываем соединение и начинаем транзакцию*  
    connection \= engine.connect()  
    transaction \= connection.begin()  
    session \= TestingSessionLocal(bind\=connection)  
      
    yield session  *\# передаём сессию в тест*  
      
    *\# После завершения теста откатываем транзакцию и закрываем соединение*  
    session.close()  
    transaction.rollback()  
    connection.close()

*\# \============================================================*  
*\# 3\. Фикстура: клиент FastAPI (TestClient)*  
*\# \============================================================*  
@pytest.fixture  
def client(db\_session):  
    """  
    Фикстура создаёт тестовый клиент FastAPI.  
    Важно: мы подменяем оригинальную зависимость get\_db() на нашу,  
    которая возвращает тестовую сессию. Благодаря этому все эндпоинты  
    будут работать с тестовой БД, а не с реальной.  
    """  
    *\# Функция, которая будет использоваться вместо оригинальной get\_db*  
    def override\_get\_db():  
        try:  
            yield db\_session  
        finally:  
            pass  
      
    *\# Подменяем зависимость в приложении FastAPI*  
    app.dependency\_overrides\[get\_db\] \= override\_get\_db  
      
    *\# Создаём тестовый клиент*  
    with TestClient(app) as test\_client:  
        yield test\_client  
      
    *\# После теста восстанавливаем оригинальную зависимость*

    app.dependency\_overrides.clear()

Объяснение для студентов:

* Мы создаём тестовую базу данных в памяти (:memory:).  
* Фикстура db\_session даёт каждому тесту свою чистую БД.  
* Фикстура client создаёт клиент, который вызывает эндпоинты.  
* Подмена app.dependency\_overrides заставляет FastAPI использовать тестовую БД вместо реальной.

---

## **6\. Unit-тесты (файл tests/test\_schemas.py)**

Unit-тесты проверяют Pydantic-модели в изоляции.

python

"""  
Unit-тесты для Pydantic-моделей.  
Проверяем, что модели правильно валидируют данные.  
"""

import pytest  
from app.schemas import TaskCreate, TaskUpdate, TaskResponse

*\# \============================================================*  
*\# Тесты для TaskCreate (создание задачи)*  
*\# \============================================================*

def test\_task\_create\_valid():  
    """  
    Проверяем, что корректные данные проходят валидацию.  
    Тест состоит из трёх частей:  
    1\. Подготовка: создаём словарь с данными  
    2\. Действие: создаём модель TaskCreate  
    3\. Проверка (assert): сравниваем поля с ожидаемыми  
    """  
    *\# Подготовка (arrange)*  
    data \= {"title": "Купить молоко", "description": "Вечером"}  
      
    *\# Действие (act)*  
    task \= TaskCreate(\*\*data)  
      
    *\# Проверка (assert)*  
    assert task.title \== "Купить молоко"  
    assert task.description \== "Вечером"  
    assert task.completed \== False  *\# значение по умолчанию*

def test\_task\_create\_missing\_title():  
    """  
    Проверяем, что отсутствие обязательного поля title вызывает ошибку.  
    pytest.raises(ValueError) – проверяет, что внутри блока возникает ошибка.  
    """  
    with pytest.raises(ValueError):  
        TaskCreate()  *\# нет title – должно упасть*

def test\_task\_create\_extra\_field():  
    """  
    Проверяем, что лишние поля игнорируются (в Pydantic v2 по умолчанию).  
    Создаём модель с лишним полем 'extra'.  
    """  
    task \= TaskCreate(title\="Тест", extra\="ignore")  
    *\# Убеждаемся, что лишнего поля нет*  
    assert not hasattr(task, "extra")

*\# \============================================================*  
*\# Тесты для TaskUpdate (обновление задачи)*  
*\# \============================================================*

def test\_task\_update\_all\_fields\_optional():  
    """  
    В TaskUpdate все поля опциональны – можно создать пустой объект.  
    """  
    update \= TaskUpdate()  
    assert update.title is None  
    assert update.description is None  
    assert update.completed is None

def test\_task\_update\_partial():  
    """  
    Можно передать только одно поле, остальные остаются None.  
    """  
    update \= TaskUpdate(completed\=True)  
    assert update.completed \== True  
    assert update.title is None

    assert update.description is None

---

## **7\. Интеграционные тесты (файл tests/test\_integration.py)**

Интеграционные тесты проверяют эндпоинты с реальной тестовой БД.

python

"""  
Интеграционные тесты – проверяем эндпоинты с тестовой базой данных.  
Используем фикстуры client и db\_session из conftest.py.  
"""

*\# \============================================================*  
*\# Тесты для POST /tasks (создание)*  
*\# \============================================================*

def test\_create\_task(client):  
    """  
    Создаём задачу через API и проверяем ответ.  
    """  
    *\# Подготовка: JSON для отправки*  
    payload \= {"title": "Изучить pytest", "description": "Написать тесты"}  
      
    *\# Действие: отправляем POST-запрос*  
    response \= client.post("/tasks", json\=payload)  
      
    *\# Проверки*  
    assert response.status\_code \== 201  *\# статус "Created"*  
    data \= response.json()  
    assert data\["title"\] \== "Изучить pytest"  
    assert data\["description"\] \== "Написать тесты"  
    assert data\["completed"\] \== False  
    assert "id" in data

*\# \============================================================*  
*\# Тесты для GET /tasks (список)*  
*\# \============================================================*

def test\_get\_empty\_tasks(client):  
    """  
    В начале список задач пуст.  
    """  
    response \= client.get("/tasks")  
    assert response.status\_code \== 200  
    assert response.json() \== \[\]  *\# пустой список*

def test\_get\_tasks\_after\_create(client):  
    """  
    Создаём задачу, затем проверяем, что она появилась в списке.  
    """  
    *\# Сначала создаём*  
    create\_response \= client.post("/tasks", json\={"title": "Тестовая задача"})  
    task\_id \= create\_response.json()\["id"\]  
      
    *\# Затем получаем список*  
    response \= client.get("/tasks")  
    tasks \= response.json()  
      
    assert len(tasks) \== 1  
    assert tasks\[0\]\["id"\] \== task\_id  
    assert tasks\[0\]\["title"\] \== "Тестовая задача"

*\# \============================================================*  
*\# Тесты для GET /tasks/{id} (получение одной задачи)*  
*\# \============================================================*

def test\_get\_task\_by\_id(client):  
    """  
    Создаём задачу, затем получаем её по id.  
    """  
    *\# Создаём*  
    create\_resp \= client.post("/tasks", json\={"title": "Уникальная задача"})  
    task\_id \= create\_resp.json()\["id"\]  
      
    *\# Получаем*  
    get\_resp \= client.get(f"/tasks/{task\_id}")  
      
    assert get\_resp.status\_code \== 200  
    assert get\_resp.json()\["title"\] \== "Уникальная задача"

def test\_get\_nonexistent\_task(client):  
    """  
    Запрос несуществующей задачи должен вернуть 404\.  
    """  
    response \= client.get("/tasks/99999")  
    assert response.status\_code \== 404  
    assert response.json()\["detail"\] \== "Task not found"

*\# \============================================================*  
*\# Тесты для PUT /tasks/{id} (обновление)*  
*\# \============================================================*

def test\_update\_task(client):  
    """  
    Создаём задачу, затем обновляем её название.  
    """  
    *\# Создаём*  
    create\_resp \= client.post("/tasks", json\={"title": "Старое название"})  
    task\_id \= create\_resp.json()\["id"\]  
      
    *\# Обновляем*  
    update\_resp \= client.put(f"/tasks/{task\_id}", json\={"title": "Новое название"})  
    assert update\_resp.status\_code \== 200  
    assert update\_resp.json()\["title"\] \== "Новое название"  
      
    *\# Проверяем через GET*  
    get\_resp \= client.get(f"/tasks/{task\_id}")  
    assert get\_resp.json()\["title"\] \== "Новое название"

*\# \============================================================*  
*\# Тесты для DELETE /tasks/{id} (удаление)*  
*\# \============================================================*

def test\_delete\_task(client):  
    """  
    Создаём задачу, удаляем её, затем убеждаемся, что она исчезла.  
    """  
    *\# Создаём*  
    create\_resp \= client.post("/tasks", json\={"title": "Удаляемая задача"})  
    task\_id \= create\_resp.json()\["id"\]  
      
    *\# Удаляем*  
    delete\_resp \= client.delete(f"/tasks/{task\_id}")  
    assert delete\_resp.status\_code \== 200  
      
    *\# Проверяем, что задача исчезла*  
    get\_resp \= client.get(f"/tasks/{task\_id}")  
    assert get\_resp.status\_code \== 404

*\# \============================================================*  
*\# Тесты на ошибки валидации*  
*\# \============================================================*

def test\_create\_task\_invalid\_data(client):  
    """  
    Отправляем пустой JSON – поле title обязательное.  
    Ожидаем ошибку 422 (Unprocessable Entity).  
    """  
    response \= client.post("/tasks", json\={})

    assert response.status\_code \== 422

---

## **8\. Запуск тестов и измерение покрытия**

bash

*\# Запустить все тесты*  
pytest tests/

*\# Запустить с подробным выводом*  
pytest \-v tests/

*\# Измерить покрытие кода (папка app)*  
pytest \--cov=app tests/

*\# Сгенерировать HTML-отчёт о покрытии*  
pytest \--cov=app \--cov-report\=html tests/

*\# Открыть htmlcov/index.html в браузере*

Что означает покрытие: Процент строк кода, которые были выполнены во время тестов. Хороший ориентир — 70–80%.

---

## **9\. Задания для студентов**

### **Базовый уровень (обязательно для всех)**

1. Адаптировать тесты под свой микросервис.  
   * Замените Task на свою сущность.  
   * Напишите unit-тесты для своих Pydantic-моделей (проверьте обязательные поля, значения по умолчанию, валидацию).  
   * Напишите интеграционные тесты для своих CRUD-эндпоинтов (создание, чтение, обновление, удаление).  
2. Добиться покрытия кода не менее 70% (измерить через pytest \--cov).

### **Средний уровень (рекомендуется)**

3. Использовать фикстуры для подготовки тестовых данных (например, создать несколько задач перед тестом).  
   Пример фикстуры для создания двух задач:  
4. python

@pytest.fixture  
def two\_tasks(db\_session):  
    task1 \= Task(title\="Первая")  
    task2 \= Task(title\="Вторая")  
    db\_session.add\_all(\[task1, task2\])  
    db\_session.commit()

5.     return \[task1, task2\]  
6. Добавить тесты на обработку ошибок (например, попытка создать задачу с пустым названием, если это запрещено).

### **Продвинутый уровень (опционально)**

5. Мокирование внешних вызовов.  
   Если ваш микросервис вызывает другой сервис по HTTP, замокайте этот вызов с помощью unittest.mock.  
   Пример мокирования:  
6. python

from unittest.mock import patch

def test\_external\_call(client):  
    with patch("app.services.requests.get") as mock\_get:  
        *\# Настраиваем мок: возвращаем фиктивный ответ*  
        mock\_get.return\_value.status\_code \= 200  
        mock\_get.return\_value.json.return\_value \= {"data": "mocked"}  
          
        response \= client.get("/external-endpoint")

7.         assert response.status\_code \== 200  
8. Настроить автоматический запуск тестов в CI (GitHub Actions) – будет в следующей практической работе.

---

## **10\. Чек-лист для самопроверки**

* Установлены pytest, pytest-cov, httpx.  
* Создана папка tests/ с файлами test\_schemas.py, test\_integration.py, conftest.py.  
* Написаны unit-тесты для всех Pydantic-моделей.  
* Написаны интеграционные тесты для всех CRUD-эндпоинтов.  
* Тесты проходят без ошибок (pytest зелёный).  
* Покрытие кода не менее 70% (pytest \--cov=app).  
* (Опционально) Использованы фикстуры для подготовки данных.  
* (Опционально) Замоканы внешние вызовы.

---

## **11\. Часто задаваемые вопросы**

Вопрос: Как запустить только один тестовый файл?  
Ответ: pytest tests/test\_schemas.py

Вопрос: Как запустить только один конкретный тест?  
Ответ: pytest tests/test\_integration.py::test\_create\_task

Вопрос: Тесты падают, потому что не могут найти модуль app. Что делать?  
Ответ: Добавьте в начало conftest.py или выполните перед запуском export PYTHONPATH=. (или настройте IDE).

Вопрос: Моя база данных в тестах не очищается между тестами.  
Ответ: Убедитесь, что в фикстуре db\_session используется transaction.rollback(). В нашем примере это уже сделано.

Вопрос: Что такое pytest.raises?  
Ответ: Это контекстный менеджер, который проверяет, что внутри блока возникает указанное исключение. Если исключения нет – тест падает.

---

## **12\. Заключение**

Поздравляю\! Вы освоили написание unit- и интеграционных тестов для FastAPI-микросервиса. Эти навыки помогут вам поддерживать код в рабочем состоянии, уверенно рефакторить и добавлять новые фичи без страха что-то сломать.

Следующий шаг: Автоматизация запуска тестов через CI/CD (GitHub Actions). Это будет в следующей практической работе.  
