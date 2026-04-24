# 🤖 KIRA AI Assistant

Telegram‑бот + лендинг с AI‑консультантом на базе OllamaFreeAPI.
 # AI Team — Фаза 1

 ## Запуск

 1. Скопируйте `.env.example` в `.env` (при необходимости отредактируйте)
 2. Запустите все сервисы:
    ```bash
    make up
    ```
    Дождитесь, пока PostgreSQL, Redis и Ollama поднимутся (около 30 секунд)

 Проверьте, что API работает:

 ```bash
 curl http://localhost:8000/
 ```

 Откройте Flower для просмотра задач Celery: http://localhost:5555

 ### Остановка

 ```bash
 make down
 ```

 ### Логи

 ```bash
 make logs          # все логи
 make api-logs      # только API
 make celery-logs   # только воркер
 ```

 ### Что дальше?
 Добавить модели данных (PostgreSQL)

 Реализовать агентов (Kira, Auditor, etc.)

 Настроить миграции Alembic

 ---

 ## 🚀 Как использовать

 1. **Скопируйте** все приведённые выше файлы в ваш приватный репозиторий (создайте их через интерфейс GitHub или через `git clone` локально, затем `git push`).

 2. **Запустите**:
    ```bash
    docker-compose up -d
    ```
    Проверьте:

 ```bash
 curl http://localhost:8000/
 ```
 Убедитесь, что все контейнеры работают:

 ```bash
 docker-compose ps
 ```
 Что теперь?
 У вас есть работающий фундамент:

 FastAPI оркестратор (порт 8000)

 Celery воркер для фоновых задач

 Redis как брокер

 PostgreSQL пустая, но готова

 Flower для мониторинга задач (http://localhost:5555)