# Чек-лист: MCP сервер для анализа SDD

##PASS Criteria
- [ ] MCP сервер запуска без ошиб
- [ ] Tool analyze_specification возвращает структурированный JSON
- [ ] JSON содержит weak_points, recommendations, unclear_sections
- [ ] Статус success для partial случаев

## Error handling
- [ ] Пустой spec_path возвращает ValidationError
- [ ] Несуществующий файл возвращает FileNotFoundError
- [ ] Неподдерживаемый формат возвращает UnsupportedFormatError
- [ ] Timeout > 120 сек возвращает partial result с warnings

## SDD Analysis specific
- [ ] config/sdd_config.yaml созд
- [ ] src/prompts/sdd/ созд
- [ ] SDD-specific agents configured
- [ ] Фокус на архитектура, данные, API, безопасность

## Integration
- [ ] MCP сервер добавлен в Claude Code
- [ ] Вызов analyze_specification из Claude Code
- [ ] Получение структурированного отчёта

## NOT INCLUDED
- Аутентификация
- Кэширование
- Batch processing
- WebSocket/SSE
- Web UI
