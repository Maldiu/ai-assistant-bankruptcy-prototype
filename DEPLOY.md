# Быстрый старт: развернуть ассистента за ~20 минут

Пошаговая инструкция по восстановлению прототипа в своём workspace Dify.
Все пути — относительно корня репозитория.

## 0. Что нужно заранее

- Аккаунт Dify (cloud.dify.ai или self-hosted).
- Ключ OpenAI-совместимого провайдера (модель `cx/gpt-5.6-sol`).
- Файл `knowledge-base/bazaznanii-bankrotstvo-fizlic.md`.

## 1. Создать приложение

1. Dify → «Создать приложение» → тип **Workflow** (advanced-chat).
2. Название: «Ассистент юриста», иконка по вкусу.
3. `show_workflow_steps`: false (чтобы служебный блок не светился).

## 2. База знаний (датасет 1)

1. «Знания» → создать датасет → загрузить `knowledge-base/bazaznanii-bankrotstvo-fizlic.md`.
2. Настройки чанкинга: разделитель `## `, `max_tokens = 800`, `overlap = 80`.
3. Сохранить. Запомнить `dataset_id` (понадобится для HTTP-ноды).

## 3. Датасет для обращений (датасет 2)

Создать пустой датасет с именем «Обращения клиентов» — сюда будут падать тикеты
через HTTP-ноду. Запомнить его `dataset_id` и API-ключ (формат `dataset-...`).

## 4. Собрать воркфлоу

Узлы в порядке (см. `workflow/dify-workflow-draft.json` для точных параметров):

```
start1 → kb1 → llm1 → code1 → ifelse1 → (case1) http1 → ans1
                                    → (false) ans1
```

- **kb1** (knowledge-retrieval): привязать датасет 1, `top_k = 10`, `retrieval_mode = multiple`.
- **llm1**: модель `cx/gpt-5.6-sol` (через OpenAI-совместимый провайдер),
  системный промпт — полностью скопировать из `prompts/system-prompt.md`.
  Контекст: `{{#context#}}` из `kb1`.
- **code1**: язык Python 3, код из `workflow/code-node.py`.
  Входы: `answer ← llm1.text`, `conv_id ← sys.conversation_id`, `user ← sys.user_id`.
  Выходы: `reply`, `obr`, `has`, `payload`.
- **ifelse1**: условие `code1.has = 1` (логический оператор `and`).
- **http1**: POST `https://api.dify.ai/v1/datasets/<dataset2_id>/document/create-by-text`,
  заголовки:
  ```
  Authorization: Bearer <dataset2_api_key>
  Content-Type: application/json; charset=utf-8
  ```
  тело — JSON из `{{#code1.payload#}}`. Включить retry: 3 попытки, интервал 10 с.
- **ans1**: ответ = `{{#code1.reply#}}`.

## 5. Настройки приложения

- Первое сообщение (opening statement) и подсказки — в `features` драфта
  (см. `dify-workflow-draft.json` → `features.opening_statement`).
- `retriever_resource.enabled = false`, `sensitive_word_avoidance.enabled = false`.

## 6. Опубликовать и протестировать

1. Нажать «Опубликовать».
2. Пройти сценарии из `docs/primery-dialogov.pdf` (раздел 1) и проверить,
   что тикет создаётся и попадает в датасет 2.
3. Проверить инъекции (раздел 3 документа) — агент должен отказываться.

## 7. (Опционально) Отказоустойчивость

Добавить вторую LLM-ноду на `cx/gpt-6-luna` + Fail Branch от `llm1` + retry.
См. `workflow/README.md` → «План по отказоустойчивости».

## Известные ограничения

- Редактор воркфлоу Dify иногда падает с `TypeError: h.replace is not a function` —
  граф при этом валиден через API; конфигурировать через console API или экспорт DSL.
- Сессия Dify протухает; для работы с console API нужен `X-CSRF-Token` из cookie
  `__Host-csrf_token`.
- Защита от инъекций держится на промпте — для продакшена нужен второй слой
  (guardrails + фильтрация входа/выхода).
