# Test-Driven Development Skill

Навык для разработки через тестирование (TDD).

## Цикл TDD:

```
RED → GREEN → REFACTOR → (повтор)
```

### 1. RED — Напиши падающий тест
```python
def test_feature():
    result = new_feature()
    assert result == expected_value
```

### 2. GREEN — Реализуй минимальный код
```python
def new_feature():
    return expected_value
```

### 3. REFACTOR — Улучши код
- Удали дубликацию
- Улучши читаемость
- Оптимизируй

## Типы тестов:

### Unit Tests
- Изолированные
- Быстрые
- Один компонент

### Integration Tests
- Между компонентами
- С внешними сервисами
- База данных

### E2E Tests
- Полный сценарий
- Пользовательский путь
- Критические функции

## Лучшие практики:

1. **AAA Pattern**
   ```python
   def test_example():
       # Arrange
       input_data = prepare_data()

       # Act
       result = process(input_data)

       # Assert
       assert result == expected
   ```

2. **Один assert на тест** (по возможности)

3. **Описательные имена**
   ```python
   def test_should_return_error_when_input_is_negative():
       ...
   ```

4. **Независимость тестов**
   - Нет порядка выполнения
   - Очистка состояния
   - Изоляция данных

## Покрытие:

```bash
# Запуск с покрытием
pytest --cov=src tests/

# Минимум 80% покрытия
# Критические пути — 100%
```
