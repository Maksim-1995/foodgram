# Foodgram — «Фудграм»

Foodgram — это онлайн-платформа для публикации и обмена кулинарными рецептами. Пользователи могут создавать рецепты, добавлять чужие рецепты в избранное, подписываться на авторов, а также формировать и скачивать список покупок для приготовления выбранных блюд.

Проект состоит из **REST API** на Django REST Framework и **SPA-фронтенда** на React.

## Запуск проекта
http://176.12.75.107/

---

## Возможности проекта

- **Публикация рецептов**: создание, редактирование и удаление рецептов с изображениями, тегами и ингредиентами.
- **Избранное**: добавление рецептов в избранное и просмотр своего списка избранного.
- **Подписки**: подписка на авторов и просмотр ленты их рецептов на странице «Мои подписки».
- **Список покупок**: добавление рецептов в список покупок и скачивание сводного списка ингредиентов в формате `.txt` с суммированием количества по каждому ингредиенту.
- **Фильтрация**: фильтрация рецептов по тегам (комбинация «или»), автору, избранному и списку покупок.
- **Поиск ингредиентов**: регистронезависимый поиск по началу названия.
- **Короткие ссылки**: генерация короткой ссылки на рецепт, которая не меняется после редактирования.
- **Аутентификация**: регистрация и вход по email и паролю, токен-авторизация.
- **Управление профилем**: смена пароля, загрузка и удаление аватара.
- **Админ-панель**: управление пользователями, рецептами, тегами, ингредиентами, подписками, избранным и списками покупок.
- **Статические страницы**: «О проекте» и «Технологии».

---

## Технологический стек

| Компонент       | Технология                                      |
|-----------------|-------------------------------------------------|
| **Бэкенд**      | Python 3.12, Django 5.1, Django REST Framework 3.15 |
| **Фронтенд**    | React (SPA), Node.js 20                         |
| **База данных** | PostgreSQL 16 (продакшен), SQLite3 (разработка) |
| **Веб-сервер**  | Nginx 1.25                                      |
| **ASGI/WSGI**   | Gunicorn 23                                     |
| **Контейнеризация** | Docker, Docker Compose                      |
| **CI/CD**       | GitHub Actions                                  |
| **Доп. пакеты** | djoser (аутентификация), django-filter, django-cors-headers, Pillow, psycopg2 |

---

## Структура проекта

```
foodgram/
├── backend/                    # Django-приложение (REST API)
│   ├── api/                    # API: views, serializers, filters, permissions, pagination
│   ├── core/                   # Базовая абстрактная модель (TimeStampedModel), константы
│   ├── foodgram/               # Конфигурация Django-проекта (settings, urls, wsgi)
│   ├── recipes/                # Модели рецептов, тегов, ингредиентов; админка; кастомные команды
│   ├── users/                  # Модель пользователя (AbstractUser), подписки; админка
│   ├── data/                   # CSV/JSON с ингредиентами для загрузки в БД
│   ├── seed_data/              # Тестовые данные: пользователи, рецепты, изображения
│   ├── Dockerfile
│   ├── entrypoint.sh           # Точка входа: миграции, статика, загрузка данных
│   └── requirements.txt
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/         # UI-компоненты
│   │   ├── pages/              # Страницы приложения
│   │   ├── api/                # API-клиент
│   │   └── contexts/           # React-контексты (auth, user)
│   └── Dockerfile
├── nginx/                      # Конфигурация Nginx
│   ├── nginx.conf
│   └── Dockerfile
├── infra/                      # Docker Compose для разработки
│   └── docker-compose.yml
├── docs/                       # Спецификация API (OpenAPI 3.0) и ReDoc
├── data/                       # Ингредиенты (JSON, CSV)
├── postman_collection/         # Postman-коллекция для тестирования API
├── docker-compose.production.yml  # Docker Compose для продакшена
├── .env.production.example     # Пример переменных окружения
└── setup.cfg                   # Настройки flake8 и isort
```

---

## Модели данных

### Пользователь (`users.User`)
- Кастомная модель на основе `AbstractUser`.
- Аутентификация по **email** (поле `USERNAME_FIELD = 'email'`).
- Поля: `email`, `username`, `first_name`, `last_name`, `avatar` (изображение).

### Подписка (`users.Subscription`)
- Связь «подписчик — автор».
- Запрет самоподписки на уровне БД (CheckConstraint).

### Тег (`recipes.Tag`)
- Поля: `name` (уникальный), `slug` (уникальный).

### Ингредиент (`recipes.Ingredient`)
- Поля: `name`, `measurement_unit`.
- Уникальность по паре `(name, measurement_unit)`.

### Рецепт (`recipes.Recipe`)
- Поля: `author` (ForeignKey → User), `name`, `image`, `text`, `cooking_time`, `short_code`.
- Связи: `tags` (ManyToMany → Tag), `ingredients` (ManyToMany → Ingredient через `RecipeIngredient`).
- Автоматическая генерация `short_code` при сохранении.

### Ингредиент рецепта (`recipes.RecipeIngredient`)
- Поля: `recipe`, `ingredient`, `amount`.
- Уникальность по паре `(recipe, ingredient)`.

### Избранное (`recipes.Favorite`)
- Связь «пользователь — рецепт».
- Уникальность по паре `(user, recipe)`.

### Список покупок (`recipes.ShoppingCart`)
- Связь «пользователь — рецепт».
- Уникальность по паре `(user, recipe)`.

---

## API Endpoints

API реализован в строгом соответствии со спецификацией OpenAPI 3.0 (файл `docs/openapi-schema.yml`).

| Метод  | Endpoint                              | Описание                          | Доступ         |
|--------|---------------------------------------|-----------------------------------|----------------|
| GET    | `/api/users/`                         | Список пользователей              | Все            |
| POST   | `/api/users/`                         | Регистрация                       | Все            |
| GET    | `/api/users/{id}/`                    | Профиль пользователя              | Все            |
| GET    | `/api/users/me/`                      | Текущий пользователь              | Токен          |
| PUT    | `/api/users/me/avatar/`               | Загрузить аватар                  | Токен          |
| DELETE | `/api/users/me/avatar/`               | Удалить аватар                    | Токен          |
| POST   | `/api/users/set_password/`            | Сменить пароль                    | Токен          |
| GET    | `/api/users/subscriptions/`           | Мои подписки                      | Токен          |
| POST   | `/api/users/{id}/subscribe/`          | Подписаться                       | Токен          |
| DELETE | `/api/users/{id}/subscribe/`          | Отписаться                        | Токен          |
| POST   | `/api/auth/token/login/`              | Получить токен                    | Все            |
| POST   | `/api/auth/token/logout/`             | Удалить токен                     | Токен          |
| GET    | `/api/tags/`                          | Список тегов                      | Все            |
| GET    | `/api/tags/{id}/`                     | Получить тег                      | Все            |
| GET    | `/api/ingredients/`                   | Список ингредиентов (с поиском)   | Все            |
| GET    | `/api/ingredients/{id}/`              | Получить ингредиент               | Все            |
| GET    | `/api/recipes/`                       | Список рецептов (с фильтрацией)   | Все            |
| POST   | `/api/recipes/`                       | Создать рецепт                    | Токен          |
| GET    | `/api/recipes/{id}/`                  | Получить рецепт                   | Все            |
| PATCH  | `/api/recipes/{id}/`                  | Обновить рецепт                   | Автор          |
| DELETE | `/api/recipes/{id}/`                  | Удалить рецепт                    | Автор          |
| GET    | `/api/recipes/{id}/get-link/`         | Получить короткую ссылку          | Все            |
| POST   | `/api/recipes/{id}/favorite/`         | Добавить в избранное              | Токен          |
| DELETE | `/api/recipes/{id}/favorite/`         | Удалить из избранного             | Токен          |
| POST   | `/api/recipes/{id}/shopping_cart/`    | Добавить в список покупок         | Токен          |
| DELETE | `/api/recipes/{id}/shopping_cart/`    | Удалить из списка покупок         | Токен          |
| GET    | `/api/recipes/download_shopping_cart/`| Скачать список покупок (.txt)     | Токен          |

### Параметры фильтрации рецептов

- `?tags=breakfast&tags=lunch` — фильтр по тегам (slug, комбинация «или»)
- `?author=1` — фильтр по автору (id)
- `?is_favorited=1` — только избранное (для авторизованных)
- `?is_in_shopping_cart=1` — только в списке покупок (для авторизованных)
- `?page=1&limit=6` — пагинация

### Поиск ингредиентов

- `?name=Сах` — регистронезависимый поиск по началу названия

---

## Запуск проекта

### Локальный запуск (Docker Compose)

1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:Maksim-1995/foodgram.git
   cd foodgram
   ```

2. Создайте файл `.env` в корне проекта (или скопируйте из `.env.production.example`):
   ```env
   POSTGRES_USER=django_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=django
   DB_HOST=db
   DB_PORT=5432
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. Запустите контейнеры:
   ```bash
   cd infra
   docker compose up --build
   ```

4. Проект будет доступен:
   - **Фронтенд**: http://localhost
   - **Спецификация API (ReDoc)**: http://localhost/api/docs/
   - **Админ-панель**: http://localhost/admin/

### Запуск для разработки (без Docker)

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Установите зависимости:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Выполните миграции:
   ```bash
   python manage.py migrate
   ```

4. Загрузите теги, ингредиенты и тестовые данные:
   ```bash
   python manage.py load_tags
   python manage.py load_ingredients
   python manage.py load_test_data
   ```

5. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```

6. Для фронтенда (в отдельном терминале):
   ```bash
   cd frontend
   npm ci
   npm start
   ```

---

## Тестовые пользователи

После загрузки тестовых данных (`python manage.py load_test_data`) будут доступны следующие пользователи:

| Логин (email)          | Пароль        | Имя пользователя | Роль         |
|------------------------|---------------|------------------|--------------|
| user1@example.com      | user12345     | user1            | Обычный пользователь |
| user2@example.com      | user12345     | user2            | Обычный пользователь |
| user3@example.com      | user12345     | user3            | Обычный пользователь |
| chef_olga@example.com  | OlgaPass123   | chef_olga        | Обычный пользователь |
| chef_dmitry@example.com| DimaPass123   | chef_dmitry      | Обычный пользователь |
| elena_cook@example.com | ElenaPass456  | elena_cook       | Обычный пользователь |

Каждый пользователь имеет по одному рецепту с изображением.

---

## Загрузка данных

### Ингредиенты
```bash
python manage.py load_ingredients
```
Загружает ~2200 ингредиентов из файла `backend/data/ingredients.json`.

### Теги
```bash
python manage.py load_tags
```
Создаёт теги: «Завтрак», «Обед», «Ужин».

### Тестовые данные
```bash
python manage.py load_test_data
```
Создаёт 7 пользователей с рецептами и изображениями.

---

## Деплой (продакшен)

### Переменные окружения

Создайте файл `.env` на сервере:

```env
POSTGRES_USER=django_user
POSTGRES_PASSWORD=strong_password
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-random-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DOCKER_USERNAME=your-dockerhub-username
```

### Сборка и публикация образов

```bash
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml push
```

### Запуск на сервере

```bash
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d
```

### CI/CD (GitHub Actions)

При пуше в ветку `main` автоматически:
1. Собираются и пушатся Docker-образы на Docker Hub.
2. На сервере выполняется деплой через SSH.

---

## Админ-панель

Доступна по адресу `/admin/` для суперпользователя.

**Возможности:**
- **Пользователи**: поиск по email и username.
- **Рецепты**: поиск по названию и автору, фильтрация по тегам, отображение количества добавлений в избранное.
- **Ингредиенты**: поиск по названию.
- **Теги**: управление тегами.
- **Подписки, Избранное, Список покупок**: просмотр и управление.

---

## Тестирование

```bash
cd backend
python -m pytest
```

Запускаются тесты моделей и API (1134+ тестовых сценариев), включая:
- Регистрация и аутентификация
- CRUD рецептов
- Избранное и список покупок
- Подписки
- Фильтрация и поиск
- Права доступа

---

## Спецификация API

Полная спецификация API в формате OpenAPI 3.0 доступна в файле:
- `docs/openapi-schema.yml`

Для визуального просмотра используйте ReDoc:
- http://localhost/api/docs/ (локально)
- http://ваш-домен/api/docs/ (на сервере)

Также в директории `postman_collection/` находится коллекция запросов для Postman.

---

## Автор

https://github.com/Maksim-1995