Практическая работа №9: Настройка CI/CD для
вашего микросервиса
Цель работы
Научиться настраивать автоматическую проверку кода (CI) и сборку
Docker-образа (CD) для своего микросервиса с помощью встроенного
инструмента GitHub Actions.
Теоретическая часть (что мы делаем и зачем)
Что такое CI/CD простыми словами
CI (Continuous Integration — непрерывная интеграция) — это автоматическая
проверка качества вашего кода. При каждом git push робот запускает ваши
тесты (pytest), проверку стиля кода (ruff) и типов (mypy). Если что-то сломано,
вы узнаете об этом сразу.
CD (Continuous Delivery — непрерывная доставка) — это автоматическая
упаковка вашего приложения в Docker-образ и отправка его в специальное
хранилище (реестр). После этого образ можно легко развернуть на любом
сервере командой docker run.
Что такое GitHub Actions: Это встроенный в GitHub исполнитель, который
запускает ваши сценарии при событиях (например, git push). Сценарии
описываются в YAML-файлах и выполняются на виртуальных машинах,
которые GitHub предоставляет бесплатно.
Что такое реестр (Container Registry): Это «склад» для хранения
Docker-образов. В работе мы будем использовать GitHub Container Registry
(GHCR) — он бесплатен и работает прямо с вашим GitHub-аккаунтом.
Подготовка к работе
1. Ваш микросервис должен быть в репозитории на GitHub (даже если он
приватный).
2. В репозитории должны быть:
○ Файл requirements.txt со всеми зависимостями
○ Папка tests/ с тестами (хотя бы один тест, например, проверка
корневого эндпоинта)
○ Файл Dockerfile для сборки образа
○ Код приложения (например, app/ или main.py)
Выполнение работы
Шаг 1. Создание директории для workflow-файлов
Создайте в корне вашего репозитория папку .github/workflows/. Внутри неё
создайте файл с любым именем, например ci-cd.yml.
yaml
# .github/workflows/ci-cd.yml
Шаг 2. Базовый скелет workflow
Напишите в файле следующий код.
yaml
# Имя workflow (будет отображаться в интерфейсе GitHub Actions)
name: CI/CD Pipeline
# События, при которых будет запускаться workflow
on:
push:
branches: [ main, master ] # при пуше в главную ветку
pull_request:
branches: [ main, master ] # при создании pull request'а в главную
ветку
Пояснение: on — триггеры запуска. При каждом git push в ветку main (или
master) и при создании pull request в эти ветки, GitHub автоматически
запустит наш сценарий.
Шаг 3. Добавление первой job: проверка кода (CI)
job — это набор шагов, которые выполняются последовательно. Добавим job с
именем test.
yaml
jobs:
test:
runs-on: ubuntu-latest # виртуальная машина (runner) с Ubuntu
steps:
# 1. Скачиваем код репозитория
- name: Checkout code
uses: actions/checkout@v3
# 2. Устанавливаем нужную версию Python
- name: Set up Python
uses: actions/setup-python@v4
with:
python-version: '3.11'
# 3. Устанавливаем зависимости
- name: Install dependencies
run: |
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install ruff mypy pytest pytest-cov
# 4. Запускаем линтер (проверка стиля кода)
- name: Lint with ruff
run: ruff check .
# 5. Запускаем проверку типов
- name: Type check with mypy
run: mypy app
# 6. Запускаем тесты с проверкой покрытия
- name: Test with pytest
run: pytest --cov=app --cov-fail-under=70 tests/
Пояснения:
● runs-on: ubuntu-latest — GitHub выделит временную виртуальную
машину с Ubuntu.
● actions/checkout@v3 — специальное действие, которое скачивает ваш
код в эту машину.
● actions/setup-python@v4 — устанавливает Python и настраивает
окружение.
● run: — выполняет команды в терминале этой виртуальной машины.
● --cov-fail-under=70 — если покрытие тестами упадёт ниже 70%, тесты
не пройдут.
Шаг 4. Добавление job для сборки и публикации Docker-образа
(CD)
Добавим вторую job с именем build-and-push. Важно: она должна
запускаться только после успешного выполнения job test. Для этого
используем needs: test.
yaml
build-and-push:
needs: test # запускать только после успешного test
runs-on: ubuntu-latest
# Даём права на запись в GitHub Container Registry
permissions:
contents: read
packages: write
steps:
- name: Checkout code
uses: actions/checkout@v3
# 1. Логинимся в GitHub Container Registry
- name: Log in to GitHub Container Registry
uses: docker/login-action@v2
with:
registry: ghcr.io
username: ${{ github.actor }}
password: ${{ secrets.GITHUB_TOKEN }}
# 2. Собираем Docker-образ
- name: Build Docker image
run: |
docker build -t ghcr.io/${{ github.repository }}:latest .
# 3. Публикуем образ в реестр
- name: Push Docker image
run: |
docker push ghcr.io/${{ github.repository }}:latest
Пояснения:
● needs: test — гарантирует, что сборка начнётся только если все тесты
прошли.
● permissions: packages: write — разрешает запись в GitHub Container
Registry.
● docker/login-action@v2 — логинимся в реестр. ${{
secrets.GITHUB_TOKEN }} — это специальный секретный токен, который
GitHub создаёт автоматически; его не нужно настраивать вручную.
● ghcr.io/${{ github.repository }}:latest — имя образа будет,
например, ghcr.io/ваш-логин/название-репозитория:latest.
Шаг 5. Тестирование и проверка
1. Закоммитьте и запушите файл .github/workflows/ci-cd.yml в ваш
репозиторий.
2. Перейдите на страницу репозитория на GitHub.
3. Нажмите на вкладку Actions. Вы увидите запущенный workflow (если нет
— сделайте ещё один git push или вручную запустите из интерфейса).
4. Нажмите на запущенный workflow, чтобы увидеть детали выполнения
каждого шага.
5. Если какой-то шаг упал — исправьте ошибку, закоммитьте и запушите
изменения. Workflow запустится снова.
Что должно получиться
1. Зелёная галочка рядом с последним коммитом в репозитории — значит,
все тесты и проверки прошли.
2. Docker-образ в реестре: Перейдите по адресу
https://github.com/ваш-логин/название-репозитория/pkgs/container/
название-репозитория. Там будет образ с тегом latest.
3. Локальная проверка образа: Вы можете скачать и запустить образ на
любом компьютере:
4. bash
docker pull ghcr.io/ваш-логин/название-репозитория:latest
5. docker run -p 8000:8000 ghcr.io/ваш-логин/название-репозитория:latest
3. Задания для самостоятельной работы
Базовый уровень (обязательно для всех)
1. Создать файл .github/workflows/ci-cd.yml и скопировать в него код из
инструкции.
2. Адаптировать команды под свой проект (пути к файлам, названия
папок).
3. Убедиться, что workflow запускается и проходит без ошибок.
4. Проверить, что Docker-образ появился в реестре (ghcr.io).
Средний уровень (для тех, кто справился с базовым)
1. Добавить в workflow тег с хэшем коммита (например, ${{ github.sha
}}) и тег latest.
2. Изменить имя образа: ghcr.io/ваш-логин/название-репозитория:${{
github.sha }}.
3. Добавить отдельную job для деплоя (пока заглушку, например, echo
"Deploy").
Продвинутый уровень (дополнительно)
1. Настроить отдельный workflow для pull request'ов, который не публикует
образ, а только проверяет код.
2. Добавить в workflow отправку уведомления в Telegram (используйте
appleboy/telegram-action).
3. Настроить свой self-hosted runner (на своей виртуальной машине).
4. Итог
Вы настроили автоматический конвейер, который:
● Проверяет код (стиль, типы, тесты) при каждом git push.
● После успешной проверки собирает Docker-образ.
● Публикует образ в реестр ghcr.io.
Теперь ваш микросервис всегда готов к деплою, и любой разработчик (или
сервер) может скачать свежий образ одной командой docker pull.
Полезные ссылки
● Документация GitHub Actions
● GitHub Container Registry
● Действия (actions) на Marketplace