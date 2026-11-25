# Код-нода Dify (Python): разделение ответа агента и блока ОБРАЩЕНИЕ.
# Извлечено из workflow draft. Входы: answer (ответ LLM), conv_id, user.
# Выходы: reply (текст клиенту), obr (блок обращения), has (0/1), payload (для HTTP-ноды).

import json


def main(answer: str, conv_id: str, user: str) -> dict:
    marker = "=== ОБРАЩЕНИЕ ==="
    idx = answer.find(marker)
    if idx >= 0:
        reply = answer[:idx].strip()
        obr = answer[idx:].strip()
        has = 1
    else:
        reply = answer.strip()
        obr = ""
        has = 0

    fallback = "Способ связи: не выбран (диалог не завершён); Телефон: не указан"
    doc_name = ((conv_id or "no-conv") + "_" + (user or "unknown")).replace(" ", "_")
    payload = json.dumps(
        {
            "name": doc_name,
            "text": obr if obr else fallback,
            "indexing_technique": "economy",
            "process_rule": {
                "mode": "automatic",
                "rules": {
                    "pre_processing_rules": [
                        {"id": "remove_extra_spaces", "enabled": True},
                        {"id": "remove_urls_emails", "enabled": False},
                    ]
                },
            },
        },
        ensure_ascii=False,
    )
    return {"reply": reply, "obr": obr, "has": has, "payload": payload}
