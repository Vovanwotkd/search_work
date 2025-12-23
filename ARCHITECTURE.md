# Job Search Assistant

AI-powered инструмент для поиска работы через HH.ru

## Концепция

1. **LLM-интервью** — чат-бот собирает информацию о пользователе (опыт, проекты, навыки)
2. **Анализ рынка** — поиск вакансий через HH API с оценкой соответствия профилю
3. **Генерация резюме** — базовое резюме + адаптированные вариации под вакансии
4. **Cover Letters** — сопроводительные письма под каждую вакансию
5. **Публикация** — выгрузка резюме на HH через API

## Tech Stack

| Компонент | Технология |
|-----------|------------|
| Frontend | Vue 3 + Vite + TypeScript |
| Backend | FastAPI + Python 3.11+ |
| Database | SQLite (с возможностью миграции на PostgreSQL) |
| LLM | Claude API / OpenAI API (переключаемый) |
| External API | HH.ru API |
| Infrastructure | Docker + Docker Compose |

## Архитектура

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         Vue 3 Frontend                               │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ │  │
│  │  │  Chat     │  │  Profile  │  │ Vacancies │  │ Resume Generator  │ │  │
│  │  │  View     │  │  View     │  │  View     │  │      View         │ │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │ :5173                                 │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         FastAPI Backend :8000                        │  │
│  │                                                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │ /api/chat   │  │ /api/hh     │  │/api/resumes │  │ /api/auth  │  │  │
│  │  │ Interview   │  │ Vacancies   │  │ Generation  │  │ HH OAuth   │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │  │
│  │         │                │                │               │         │  │
│  │  ┌──────▼──────────────────────────────────────────────────────┐   │  │
│  │  │                    Service Layer                            │   │  │
│  │  │  InterviewService │ HHService │ ResumeService │ LLMService │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  │         │                │                │               │         │  │
│  │         ▼                ▼                ▼               ▼         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────────┐   │  │
│  │  │ LLM Provider│  │  HH API     │  │         SQLite            │   │  │
│  │  │Claude/OpenAI│  │             │  │                           │   │  │
│  │  └─────────────┘  └─────────────┘  └───────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
-- Пользователь (связь с HH)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hh_user_id VARCHAR(50) UNIQUE,
    hh_access_token TEXT,           -- encrypted
    hh_refresh_token TEXT,          -- encrypted
    hh_token_expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Профиль пользователя (результат LLM-интервью)
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    raw_interview_data JSON,        -- сырая история чата
    structured_profile JSON,        -- обработанный профиль
    skills JSON,                    -- ["Python", "FastAPI", ...]
    experience_years INTEGER,
    preferred_position VARCHAR(255),
    preferred_salary_min INTEGER,
    preferred_salary_max INTEGER,
    preferred_locations JSON,       -- ["Москва", "Remote"]
    summary TEXT,                   -- краткое описание от LLM
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- История интервью (для продолжения диалога)
CREATE TABLE interview_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    messages JSON,                  -- [{role, content, timestamp}]
    status VARCHAR(20) DEFAULT 'in_progress', -- in_progress, completed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Базовое резюме
CREATE TABLE base_resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255),
    content JSON,                   -- структура в формате HH API
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Вариации резюме (адаптированные под вакансии)
CREATE TABLE resume_variations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_resume_id INTEGER REFERENCES base_resumes(id),
    vacancy_id INTEGER REFERENCES vacancies_cache(id),
    hh_resume_id VARCHAR(50),       -- ID резюме на HH после публикации
    title VARCHAR(255),
    content JSON,                   -- адаптированная структура
    adaptations JSON,               -- что изменили и почему
    cover_letter TEXT,              -- сопроводительное письмо
    status VARCHAR(20) DEFAULT 'draft', -- draft, published, archived
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Кэш вакансий
CREATE TABLE vacancies_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hh_vacancy_id VARCHAR(50) UNIQUE,
    title VARCHAR(255),
    company_name VARCHAR(255),
    salary_from INTEGER,
    salary_to INTEGER,
    salary_currency VARCHAR(10),
    location VARCHAR(255),
    experience VARCHAR(50),
    employment_type VARCHAR(50),
    requirements TEXT,
    description TEXT,
    key_skills JSON,
    match_score FLOAT,              -- 0-100, насколько подходит профилю
    match_analysis JSON,            -- детали анализа соответствия
    raw_data JSON,                  -- полный ответ от HH API
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Настройки приложения
CREATE TABLE settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- llm_provider: 'claude' | 'openai'
-- claude_api_key: encrypted
-- openai_api_key: encrypted
```

## API Endpoints

### Auth
```
GET  /api/auth/hh/login          # Редирект на HH OAuth
GET  /api/auth/hh/callback       # OAuth callback
GET  /api/auth/status            # Статус авторизации
POST /api/auth/logout            # Выход
```

### Chat (Interview)
```
GET  /api/chat/session           # Получить текущую сессию или создать новую
POST /api/chat/message           # Отправить сообщение
POST /api/chat/complete          # Завершить интервью, сгенерировать профиль
```

### Profile
```
GET  /api/profile                # Получить профиль
PUT  /api/profile                # Обновить профиль вручную
POST /api/profile/regenerate     # Перегенерировать из интервью
```

### HH Vacancies
```
GET  /api/hh/vacancies           # Поиск вакансий (проксирует HH API + добавляет match_score)
GET  /api/hh/vacancies/:id       # Детали вакансии
POST /api/hh/vacancies/:id/analyze  # Анализ соответствия профилю
```

### Resumes
```
GET  /api/resumes/base           # Получить базовое резюме
POST /api/resumes/base           # Создать базовое резюме
PUT  /api/resumes/base           # Обновить базовое резюме

GET  /api/resumes/variations     # Список вариаций
POST /api/resumes/variations     # Создать вариацию под вакансию
GET  /api/resumes/variations/:id # Получить вариацию
PUT  /api/resumes/variations/:id # Редактировать вариацию
DELETE /api/resumes/variations/:id # Удалить вариацию

POST /api/resumes/variations/:id/publish   # Опубликовать на HH
POST /api/resumes/variations/:id/cover-letter # Сгенерировать cover letter
```

### Settings
```
GET  /api/settings               # Получить настройки
PUT  /api/settings               # Обновить настройки (LLM provider, keys)
```

## Project Structure

```
job-search-assistant/
├── docker-compose.yml
├── .env.example
├── README.md
├── ARCHITECTURE.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Settings from env
│   │   ├── database.py             # SQLite connection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependencies (get_db, get_current_user)
│   │   │   ├── auth.py             # /api/auth/*
│   │   │   ├── chat.py             # /api/chat/*
│   │   │   ├── profile.py          # /api/profile/*
│   │   │   ├── vacancies.py        # /api/hh/*
│   │   │   ├── resumes.py          # /api/resumes/*
│   │   │   └── settings.py         # /api/settings/*
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py         # Abstract LLM provider
│   │   │   │   ├── claude.py       # Claude implementation
│   │   │   │   ├── openai.py       # OpenAI implementation
│   │   │   │   └── prompts.py      # All prompts in one place
│   │   │   ├── hh_client.py        # HH API client
│   │   │   ├── interview.py        # Interview logic
│   │   │   ├── profile_builder.py  # Build profile from interview
│   │   │   ├── vacancy_analyzer.py # Analyze vacancy match
│   │   │   ├── resume_generator.py # Generate/adapt resumes
│   │   │   └── cover_letter.py     # Generate cover letters
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── interview.py
│   │   │   ├── resume.py
│   │   │   ├── vacancy.py
│   │   │   └── settings.py
│   │   │
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── profile.py
│   │       ├── vacancy.py
│   │       └── resume.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_chat.py
│       ├── test_hh_client.py
│       └── test_resume_generator.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   │
│   │   ├── views/
│   │   │   ├── ChatView.vue        # LLM интервью
│   │   │   ├── ProfileView.vue     # Просмотр/редактирование профиля
│   │   │   ├── VacanciesView.vue   # Поиск и список вакансий
│   │   │   ├── ResumeView.vue      # Работа с резюме
│   │   │   └── SettingsView.vue    # Настройки (API keys, LLM provider)
│   │   │
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatContainer.vue
│   │   │   │   ├── ChatMessage.vue
│   │   │   │   └── ChatInput.vue
│   │   │   ├── vacancy/
│   │   │   │   ├── VacancyCard.vue
│   │   │   │   ├── VacancyDetails.vue
│   │   │   │   └── MatchScore.vue
│   │   │   ├── resume/
│   │   │   │   ├── ResumeEditor.vue
│   │   │   │   ├── ResumePreview.vue
│   │   │   │   └── AdaptationsList.vue
│   │   │   └── common/
│   │   │       ├── AppHeader.vue
│   │   │       ├── AppSidebar.vue
│   │   │       └── LoadingSpinner.vue
│   │   │
│   │   ├── composables/
│   │   │   ├── useChat.ts
│   │   │   ├── useAuth.ts
│   │   │   ├── useVacancies.ts
│   │   │   └── useResumes.ts
│   │   │
│   │   ├── stores/
│   │   │   ├── auth.ts             # Pinia store
│   │   │   ├── profile.ts
│   │   │   ├── chat.ts
│   │   │   └── vacancies.ts
│   │   │
│   │   ├── api/
│   │   │   ├── client.ts           # Axios instance
│   │   │   ├── auth.ts
│   │   │   ├── chat.ts
│   │   │   ├── vacancies.ts
│   │   │   └── resumes.ts
│   │   │
│   │   └── types/
│   │       └── index.ts
│   │
│   └── public/
│       └── favicon.ico
│
└── scripts/
    ├── init-db.py                  # Инициализация БД
    └── seed-data.py                # Тестовые данные (опционально)
```

## UI/UX Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MAIN LAYOUT                                    │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                             │
│  SIDEBAR   │                      CONTENT AREA                          │
│            │                                                             │
│  ┌──────┐  │  ┌─────────────────────────────────────────────────────┐  │
│  │ 💬   │  │  │                                                     │  │
│  │ Chat │  │  │   Зависит от выбранного раздела                     │  │
│  └──────┘  │  │                                                     │  │
│  ┌──────┐  │  │                                                     │  │
│  │ 👤   │  │  │                                                     │  │
│  │Profile│  │  │                                                     │  │
│  └──────┘  │  │                                                     │  │
│  ┌──────┐  │  │                                                     │  │
│  │ 🔍   │  │  │                                                     │  │
│  │ Jobs │  │  │                                                     │  │
│  └──────┘  │  │                                                     │  │
│  ┌──────┐  │  │                                                     │  │
│  │ 📄   │  │  │                                                     │  │
│  │Resume│  │  │                                                     │  │
│  └──────┘  │  │                                                     │  │
│  ┌──────┐  │  │                                                     │  │
│  │ ⚙️   │  │  │                                                     │  │
│  │Settngs│  │  │                                                     │  │
│  └──────┘  │  └─────────────────────────────────────────────────────┘  │
│            │                                                             │
└────────────┴────────────────────────────────────────────────────────────┘
```

### 1. Chat View (LLM Interview)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  💬 Интервью                                           [Начать заново]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🤖 Привет! Я помогу составить твой профессиональный профиль.  │   │
│  │     Расскажи, кем ты сейчас работаешь и чем занимаешься?       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  👤 Я senior backend разработчик в финтех компании. Пишу       │   │
│  │     микросервисы на Python, работаю с PostgreSQL и Redis.      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🤖 Отлично! Расскажи подробнее о самом интересном проекте,   │   │
│  │     над которым работал. Какая была задача и что сделал?       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ...                                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  ┌─────┐  │
│  │ Введите сообщение...                                    │  │  ➤  │  │
│  └─────────────────────────────────────────────────────────┘  └─────┘  │
│                                                                         │
│  Прогресс: ████████░░░░░░░░ 50% (5/10 вопросов)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Profile View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  👤 Профиль                              [Редактировать] [Обновить]     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ПОЗИЦИЯ                                                         │  │
│  │  Senior Backend Developer                                         │  │
│  │                                                                   │  │
│  │  ОПЫТ: 5 лет                                                     │  │
│  │  ЛОКАЦИЯ: Москва, готов к удалёнке                               │  │
│  │  ЗАРПЛАТА: 300 000 - 400 000 ₽                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  НАВЫКИ                                                          │  │
│  │  ┌────────┐ ┌─────────┐ ┌────────────┐ ┌───────┐ ┌─────┐       │  │
│  │  │ Python │ │ FastAPI │ │ PostgreSQL │ │ Redis │ │ K8s │       │  │
│  │  └────────┘ └─────────┘ └────────────┘ └───────┘ └─────┘       │  │
│  │  ┌──────┐ ┌────────┐ ┌──────────┐                               │  │
│  │  │ Docker │ │ CI/CD │ │ Microservices │                          │  │
│  │  └──────┘ └────────┘ └──────────┘                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  О СЕБЕ                                                          │  │
│  │  Backend-разработчик с 5-летним опытом в финтех. Специализируюсь │  │
│  │  на высоконагруженных системах и микросервисной архитектуре.     │  │
│  │  Последние 2 года — в роли техлида команды из 4 человек.         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  КЛЮЧЕВЫЕ ПРОЕКТЫ                                                │  │
│  │                                                                   │  │
│  │  📁 Платёжный шлюз (2023)                                        │  │
│  │     Разработал систему обработки 10k транзакций/сек              │  │
│  │     Python, FastAPI, PostgreSQL, Kafka                           │  │
│  │                                                                   │  │
│  │  📁 Антифрод система (2022)                                      │  │
│  │     ML-пайплайн для выявления мошенничества в реальном времени   │  │
│  │     Python, scikit-learn, Redis, ClickHouse                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Vacancies View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔍 Вакансии                                                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────┐  ┌───────┐ │
│  │ Python Backend Москва Remote                           │  │Искать │ │
│  └────────────────────────────────────────────────────────┘  └───────┘ │
│                                                                         │
│  Фильтры: [Зарплата ▼] [Опыт ▼] [Тип занятости ▼] [Только подходящие] │
│                                                                         │
│  Найдено: 247 вакансий                          Сортировка: [По match ▼]│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ★ 94%   Senior Python Developer                                 │  │
│  │          Яндекс • Москва / Remote                                │  │
│  │          250 000 - 350 000 ₽                                     │  │
│  │                                                                   │  │
│  │          Совпадения: FastAPI, PostgreSQL, K8s, микросервисы      │  │
│  │                                                                   │  │
│  │          [Подробнее]  [Создать резюме]  [Cover Letter]           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ★ 87%   Backend Team Lead                                       │  │
│  │          Тинькофф • Москва                                       │  │
│  │          350 000 - 450 000 ₽                                     │  │
│  │                                                                   │  │
│  │          Совпадения: Python, управление командой, финтех         │  │
│  │          Не хватает: Go (можно изучить)                          │  │
│  │                                                                   │  │
│  │          [Подробнее]  [Создать резюме]  [Cover Letter]           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ★ 72%   Python Developer                                        │  │
│  │          СберТех • Москва                                        │  │
│  │          200 000 - 280 000 ₽                                     │  │
│  │          ...                                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [← Prev]  Страница 1 из 25  [Next →]                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. Resume View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📄 Резюме                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Tabs: [Базовое резюме] [Вариации (5)]                                 │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════   │
│                                                                         │
│  ┌────────────────────────────────┬─────────────────────────────────┐  │
│  │  РЕДАКТОР                      │  ПРЕДПРОСМОТР                   │  │
│  │                                │                                  │  │
│  │  Заголовок:                    │  ┌─────────────────────────┐    │  │
│  │  ┌──────────────────────────┐  │  │  ИВАН ИВАНОВ            │    │  │
│  │  │ Senior Backend Developer │  │  │  Senior Backend Developer│    │  │
│  │  └──────────────────────────┘  │  │                         │    │  │
│  │                                │  │  📍 Москва              │    │  │
│  │  О себе:                       │  │  💰 300-400k            │    │  │
│  │  ┌──────────────────────────┐  │  │  📧 email@example.com   │    │  │
│  │  │ Backend-разработчик с    │  │  │                         │    │  │
│  │  │ 5-летним опытом...       │  │  │  ─────────────────────  │    │  │
│  │  │                          │  │  │                         │    │  │
│  │  └──────────────────────────┘  │  │  ОПЫТ РАБОТЫ            │    │  │
│  │                                │  │                         │    │  │
│  │  Навыки:                       │  │  FinTech Corp           │    │  │
│  │  [Python] [FastAPI] [+]        │  │  Senior Developer       │    │  │
│  │                                │  │  2021 - настоящее время │    │  │
│  │  [Сохранить]                   │  │  • Разработал...        │    │  │
│  │                                │  │  • Оптимизировал...     │    │  │
│  │                                │  │                         │    │  │
│  │                                │  └─────────────────────────┘    │  │
│  └────────────────────────────────┴─────────────────────────────────┘  │
│                                                                         │
│  [Опубликовать на HH]                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Фазы разработки

### Phase 1: Foundation (MVP Core)

**Цель:** Базовая инфраструктура и LLM-интервью

#### Backend
- [ ] Инициализация FastAPI проекта
- [ ] Настройка SQLite + Alembic миграции
- [ ] Создание моделей: users, user_profiles, interview_sessions
- [ ] LLM Service с абстракцией провайдера
  - [ ] Базовый класс LLMProvider
  - [ ] Claude implementation
  - [ ] OpenAI implementation
- [ ] Interview Service
  - [ ] Промпты для интервью
  - [ ] Логика ведения диалога
  - [ ] Генерация профиля из интервью
- [ ] API endpoints: /api/chat/*, /api/settings/*

#### Frontend
- [ ] Инициализация Vue 3 + Vite + TypeScript
- [ ] Базовый layout (sidebar + content area)
- [ ] Pinia stores: chat, settings
- [ ] ChatView с компонентами:
  - [ ] ChatContainer
  - [ ] ChatMessage
  - [ ] ChatInput
- [ ] SettingsView (выбор LLM provider, API keys)

#### Infrastructure
- [ ] Docker Compose для dev окружения
- [ ] .env конфигурация

**Результат:** Работающий чат с LLM, который проводит интервью и сохраняет профиль

---

### Phase 2: HH Integration

**Цель:** Подключение к HH.ru API, поиск и анализ вакансий

#### Backend
- [ ] HH OAuth flow (/api/auth/hh/*)
- [ ] HH API Client
  - [ ] Авторизация и refresh токенов
  - [ ] Поиск вакансий
  - [ ] Получение деталей вакансии
- [ ] Vacancy Analyzer Service
  - [ ] Промпты для анализа соответствия
  - [ ] Расчёт match_score
- [ ] Модели: vacancies_cache
- [ ] API endpoints: /api/hh/*

#### Frontend
- [ ] Pinia store: auth, vacancies
- [ ] Интеграция HH OAuth (кнопка логина, callback)
- [ ] VacanciesView:
  - [ ] Поиск с фильтрами
  - [ ] VacancyCard с match score
  - [ ] VacancyDetails modal

**Результат:** Поиск вакансий на HH с оценкой соответствия профилю

---

### Phase 3: Resume Generation

**Цель:** Генерация и адаптация резюме

#### Backend
- [ ] Resume Generator Service
  - [ ] Генерация базового резюме из профиля
  - [ ] Адаптация под конкретную вакансию
  - [ ] Форматирование в структуру HH API
- [ ] Cover Letter Service
- [ ] Модели: base_resumes, resume_variations
- [ ] API endpoints: /api/resumes/*

#### Frontend
- [ ] Pinia store: resumes
- [ ] ProfileView (просмотр/редактирование)
- [ ] ResumeView:
  - [ ] ResumeEditor
  - [ ] ResumePreview
  - [ ] Tabs для вариаций
  - [ ] AdaptationsList

**Результат:** Генерация резюме и сопроводительных писем под вакансии

---

### Phase 4: HH Publishing

**Цель:** Публикация резюме на HH.ru

#### Backend
- [ ] HH Resume API integration
  - [ ] POST /resumes (создание)
  - [ ] PUT /resumes/{id} (обновление)
  - [ ] Получение списка своих резюме
- [ ] Синхронизация статусов

#### Frontend
- [ ] Кнопка "Опубликовать на HH"
- [ ] Статус публикации
- [ ] Список опубликованных резюме

**Результат:** Полный цикл: интервью → резюме → публикация на HH

---

### Phase 5: Polish & Enhancements

**Цель:** Улучшения и полировка

- [ ] Улучшение промптов на основе тестирования
- [ ] Обработка ошибок и edge cases
- [ ] Loading states и skeleton screens
- [ ] Responsive design
- [ ] Экспорт резюме в PDF
- [ ] История изменений резюме
- [ ] Тесты (unit, integration)

---

## Environment Variables

```env
# App
APP_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///./data/app.db

# HH.ru OAuth
HH_CLIENT_ID=your-hh-client-id
HH_CLIENT_SECRET=your-hh-client-secret
HH_REDIRECT_URI=http://localhost:8000/api/auth/hh/callback

# LLM Providers
LLM_PROVIDER=claude  # or openai
CLAUDE_API_KEY=your-claude-api-key
OPENAI_API_KEY=your-openai-api-key

# Frontend
VITE_API_URL=http://localhost:8000
```

## Запуск

```bash
# Development
docker-compose up -d

# Frontend отдельно (для hot reload)
cd frontend && npm run dev

# Backend отдельно
cd backend && uvicorn app.main:app --reload
```
