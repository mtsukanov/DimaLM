# JSON Schema для LM Studio

Чтобы LM Studio принудительно возвращал ответ в JSON-формате, который наше приложение распарсит и подхватит правильный аватар/эмоцию, добавьте в инференс модели следующую schema.

## Где это вставить

В LM Studio v0.3+:

**Способ 1 — через UI**: Server settings → Structured Output → JSON Schema → вставить блок ниже.

**Способ 2 — через API-запрос**: добавить поле `response_format` в JSON тела запроса (наше приложение уже шлёт остальное).

## Schema

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "dima_response",
    "strict": true,
    "schema": {
      "type": "object",
      "properties": {
        "line_id": {
          "type": "integer",
          "minimum": 1,
          "maximum": 42,
          "description": "Номер выбранной строки из таблицы фирменных фраз"
        },
        "text": {
          "type": "string",
          "description": "Точный текст ответа из колонки Text таблицы"
        },
        "avatar": {
          "type": "string",
          "enum": [
            "avatar_1.jpeg", "avatar_2.jpeg", "avatar_3.jpeg",
            "avatar_4.jpeg", "avatar_5.jpeg", "avatar_6.jpeg",
            "avatar_7.jpeg", "avatar_8.jpeg", "avatar_9.jpeg"
          ],
          "description": "Файл аватара из колонки Avatar"
        },
        "emotion": {
          "type": "string",
          "description": "Название эмоции из колонки Emotion (Задумчивый, Растерянный, Внимательный, Скучающий, Сосредоточенный, Игривый, Гневный)"
        }
      },
      "required": ["line_id", "text", "avatar", "emotion"],
      "additionalProperties": false
    }
  }
}
```

## Пример валидного ответа

```json
{
  "line_id": 4,
  "text": "ага, не успеваю",
  "avatar": "avatar_4.jpeg",
  "emotion": "Скучающий"
}
```

## Что делает наше приложение с таким ответом

1. Парсит JSON, извлекает `text` → выводит typewriter'ом.
2. По `line_id` (или, если нет — по `avatar`) находит запись в `DI_REPLIES` и выставляет именно этот аватар. Если по какой-то причине JSON не пришёл — fallback на текстовый ответ + поиск фирменной фразы в нём.
3. В консоли DevTools видно `[LLM] JSON parsed: {...}` для отладки.

## Если JSON-схема не настроена

Приложение всё равно работает — просто берёт текст ответа модели и пытается найти фирменную фразу в нём, чтобы определить аватар. Но JSON-режим даёт **гарантированный** правильный аватар + точное соответствие таблице.
