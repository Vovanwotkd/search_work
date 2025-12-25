# Job Search Assistant

AI-powered инструмент для автоматизации поиска работы через HH.ru

## Возможности

- **LLM-интервью** - чат-бот собирает информацию о вашем опыте, навыках и проектах
- **Поиск вакансий** - расширенный поиск по HH.ru с фильтрами (регион, специализация, зарплата, опыт и т.д.)
- **Анализ соответствия** - LLM оценивает насколько вакансия подходит под ваш профиль
- **Генерация резюме** - создание базового резюме и адаптированных вариаций под конкретные вакансии
- **Сопроводительные письма** - автоматическая генерация cover letter
- **Экспорт вакансий** - выгрузка в JSON/CSV до 2000 вакансий
- **Автоматизация** - пакетный анализ вакансий и автоматическое создание резюме
- **Интеграция с GitHub** - анализ ваших репозиториев для обогащения профиля

## Tech Stack

| Компонент | Технология |
|-----------|------------|
| Frontend | Vue 3 + Vite + TypeScript + Pinia |
| Backend | FastAPI + Python 3.11+ |
| Database | SQLite |
| LLM | Claude API / OpenAI API (переключаемый) |
| External API | HH.ru API, GitHub API |
| Infrastructure | Docker + Docker Compose + nginx |

## Требования

- Docker и Docker Compose
- API ключ Claude (Anthropic) или OpenAI
- (Опционально) Приложение HH.ru для OAuth

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Vovanwotkd/search_work.git
cd search_work
```

### 2. Создать файл .env

```bash
cp .env.example .env
```

Отредактируйте `.env` и заполните необходимые переменные:

```env
# Обязательные
SECRET_KEY=your-secret-key-here
CLAUDE_API_KEY=your-claude-api-key

# Или если используете OpenAI
# OPENAI_API_KEY=your-openai-api-key

# HH.ru OAuth (опционально, для авторизации)
HH_CLIENT_ID=your-hh-client-id
HH_CLIENT_SECRET=your-hh-client-secret
HH_REDIRECT_URI=http://localhost:8000/api/auth/hh/callback
```

### 3. Запустить через Docker Compose

```bash
docker-compose up -d
```

### 4. Открыть приложение

- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Настройка

### Получение API ключей

#### Claude (Anthropic)

1. Зарегистрируйтесь на https://console.anthropic.com
2. Создайте API ключ в разделе "API Keys"
3. Добавьте ключ в `.env` как `CLAUDE_API_KEY`

#### OpenAI

1. Зарегистрируйтесь на https://platform.openai.com
2. Создайте API ключ в разделе "API Keys"
3. Добавьте ключ в `.env` как `OPENAI_API_KEY`

#### HH.ru OAuth (опционально)

Для полной интеграции с HH.ru (публикация резюме, отклик на вакансии):

1. Зарегистрируйте приложение на https://dev.hh.ru
2. Получите `Client ID` и `Client Secret`
3. Укажите Redirect URI: `http://localhost:8000/api/auth/hh/callback`
4. Добавьте данные в `.env`

#### GitHub Token (опционально)

Для анализа приватных репозиториев:

1. Создайте Personal Access Token на https://github.com/settings/tokens
2. Выберите scopes: `repo` (для приватных репозиториев)
3. Добавьте токен в настройках приложения

## Использование

### 1. Интервью (Chat)

Начните с раздела **Интервью** - чат-бот задаст вопросы о вашем опыте, навыках и проектах. На основе ответов будет сформирован профиль.

Также можно загрузить существующее резюме текстом в разделе **Настройки**.

### 2. Профиль

В разделе **Профиль** отображается собранная информация:
- Желаемая позиция
- Опыт работы
- Навыки
- Ожидаемая зарплата
- Локация

### 3. Поиск и экспорт

Раздел **Поиск и экспорт** позволяет:
- Искать вакансии с фильтрами (регион, специализация, зарплата, опыт и т.д.)
- Просматривать детали вакансии (навыки, описание)
- Экспортировать до 2000 вакансий в JSON или CSV

### 4. Вакансии

Раздел **Вакансии** показывает:
- Результаты поиска с оценкой соответствия профилю
- Совпадающие и недостающие навыки
- Кнопки для анализа и создания резюме

### 5. Резюме

В разделе **Резюме**:
- Базовое резюме - основа, сгенерированная из профиля
- Вариации - адаптированные версии под конкретные вакансии
- Сопроводительные письма

### 6. Автоматизация

Раздел **Автоматизация** для пакетной обработки:
1. Импорт резюме с HH.ru или анализ GitHub
2. Выбор городов и специализаций
3. Загрузка вакансий
4. Автоматический анализ и рекомендации
5. Генерация резюме под подходящие вакансии

### 7. Настройки

В разделе **Настройки**:
- Выбор LLM провайдера (Claude/OpenAI) и модели
- API ключи
- GitHub токен
- Загрузка резюме текстом
- Настройка промптов

## Разработка

### Локальный запуск без Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Структура проекта

```
search_work/
├── docker-compose.yml
├── .env.example
├── README.md
├── ARCHITECTURE.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI приложение
│       ├── config.py            # Конфигурация
│       ├── database.py          # SQLite подключение
│       ├── api/                  # API endpoints
│       │   ├── auth.py          # HH OAuth
│       │   ├── chat.py          # LLM интервью
│       │   ├── profile.py       # Профиль пользователя
│       │   ├── vacancies.py     # HH вакансии
│       │   ├── resumes.py       # Резюме
│       │   ├── search.py        # Поиск и экспорт
│       │   ├── automation.py    # Автоматизация
│       │   └── settings.py      # Настройки
│       ├── services/            # Бизнес-логика
│       │   ├── llm/             # LLM провайдеры
│       │   ├── hh_client.py     # HH API клиент
│       │   ├── interview.py     # Интервью
│       │   ├── vacancy_analyzer.py
│       │   ├── resume_generator.py
│       │   └── github_analyzer.py
│       ├── models/              # SQLAlchemy модели
│       └── schemas/             # Pydantic схемы
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/
        ├── main.ts
        ├── App.vue
        ├── router/              # Vue Router
        ├── views/               # Страницы
        │   ├── ChatView.vue
        │   ├── ProfileView.vue
        │   ├── VacanciesView.vue
        │   ├── ResumeView.vue
        │   ├── SearchView.vue
        │   ├── AutomationView.vue
        │   └── SettingsView.vue
        ├── stores/              # Pinia stores
        ├── api/                 # API клиенты
        └── components/          # Vue компоненты
```

## API Endpoints

### Auth
- `GET /api/auth/hh/login` - Редирект на HH OAuth
- `GET /api/auth/hh/callback` - OAuth callback
- `GET /api/auth/status` - Статус авторизации

### Chat
- `GET /api/chat/session` - Получить/создать сессию
- `POST /api/chat/message` - Отправить сообщение

### Profile
- `GET /api/profile` - Получить профиль
- `POST /api/profile/parse-resume` - Загрузить резюме текстом

### Search
- `GET /api/search/vacancies` - Поиск вакансий
- `GET /api/search/vacancies/{id}` - Детали вакансии
- `POST /api/search/vacancies/export` - Экспорт в JSON/CSV
- `GET /api/search/areas/russia` - Регионы России
- `GET /api/search/professional-roles` - Специализации
- `GET /api/search/dictionaries` - Справочники HH

### Resumes
- `GET /api/resumes/base` - Базовое резюме
- `POST /api/resumes/variations` - Создать вариацию
- `POST /api/resumes/variations/{id}/cover-letter` - Сгенерировать cover letter

## Troubleshooting

### Ошибка подключения к API

Убедитесь что:
1. API ключи указаны корректно в `.env`
2. Контейнеры запущены: `docker-compose ps`
3. Логи backend: `docker-compose logs backend`

### HH API возвращает 403

HH.ru требует корректный User-Agent. Если ошибка повторяется:
1. Проверьте что `HH_CLIENT_ID` и `HH_CLIENT_SECRET` указаны
2. Попробуйте переавторизоваться через OAuth

### Вакансии не загружаются

1. Проверьте логи: `docker-compose logs backend`
2. Убедитесь что HH API доступен
3. Попробуйте поиск без фильтров

## Лицензия

MIT

## Контакты

- GitHub: https://github.com/Vovanwotkd/search_work
- Issues: https://github.com/Vovanwotkd/search_work/issues
