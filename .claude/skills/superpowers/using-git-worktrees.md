# Using Git Worktrees Skill

Навык для работы с git worktrees — параллельная разработка без переключения веток.

## Основные команды:

```bash
# Создать новый worktree с новой веткой
git worktree add ../feature-branch -b feature/name

# Создать worktree для существующей ветки
git worktree add ../existing-branch feature/name

# Список всех worktrees
git worktree list

# Удалить worktree
git worktree remove ../feature-branch

# Очистить удаленные worktrees
git worktree prune
```

## Workflow для PM:

1. **Создание изолированной среды**
   - Каждый worktree — отдельный контекст
   - Нет конфликтов между задачами
   - Можно работать параллельно

2. **Типичная структура:**
   ```
   project/
   ├── main/           # основная ветка
   ├── feature/auth/   # работа над авторизацией
   ├── bugfix/api/     # исправление багов API
   └── docs/           # документация
   ```

3. **Лучшие практики:**
   - Именуй worktrees осмысленно
   - Удаляй завершенные worktrees
   - Используй для долгоживущих задач

## Преимущества:

- Нет необходимости в `git stash`
- Можно запускать тесты параллельно
- Изоляция изменений
- Быстрое переключение контекста
