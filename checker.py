# checker.py
import logging
import requests
from datetime import datetime, timedelta
from telegram import Bot

# ----- РЕДАКТИРУЙ ТУТ СПИСОК ВРАЧЕЙ -----
DOCTORS = [
     {"surname": "Прохореня", "usluga": 2},
    # {"surname": "Дегтярёв", "usluga": 22},
    # {"surname": "Сидоров", "usluga": 44},
]

BASE_URL = "https://z-api-lode.vot.by/getAllData"

def _iso_range_utc_60d():
    now = datetime.utcnow()
    start = now.isoformat(timespec="milliseconds") + "Z"
    end = (now + timedelta(days=60)).replace(
        hour=23, minute=59, second=59, microsecond=999000
    ).isoformat(timespec="milliseconds") + "Z"
    return start, end

async def check_and_notify(bot: Bot, chat_id: str):
    start, end = _iso_range_utc_60d()

    for doc in DOCTORS:
        surname = doc["surname"].strip()
        usluga = doc["usluga"]

        params = {"start": start, "end": end, "usluga": usluga}
        try:
            r = requests.get(BASE_URL, params=params, timeout=20)
            logging.info(f"[{surname}] GET {r.url} -> {r.status_code}")
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logging.warning(f"[{surname}] Ошибка запроса/JSON: {e}")
            continue

        workers = data.get("workers", [])
        tickets = data.get("tickets", [])
        logging.info(f"[{surname}] workers={len(workers)} tickets={len(tickets)}")

        # ищем врача по фамилии
        target = next(
            (w for w in workers
             if w.get("surname", "").strip().lower() == surname.lower()),
            None
        )
        if not target:
            logging.info(f"[{surname}] врач НЕ найден в workers для usluga={usluga}")
            continue

        worker_id = target["id"]
        full_name = " ".join([
            target.get("surname", ""), target.get("name", ""), target.get("father", "")
        ]).strip()

        matched = [t for t in tickets if t.get("worker_id") == worker_id]
        logging.info(f"[{surname}] найдено талонов для worker_id={worker_id}: {len(matched)}")

        # ✅ ДОБАВЬ ЭТУ ПРОВЕРКУ
        # (например, уведомлять только о записях в ближайшие 14 дней)
        limit_date = datetime.utcnow() + timedelta(days=90)
        filtered = []
        for t in matched:
            try:
                t_date = datetime.strptime(t["date"], "%Y-%m-%d")
                if t_date <= limit_date:
                    filtered.append(t)
            except Exception as e:
                logging.warning(f"[{surname}] ошибка парсинга даты {t['date']}: {e}")

        matched = filtered
        # 🔚 конец добавки

        if not matched:
            logging.info(f"[{surname}] свободных записей нет")
            continue

        for t in matched:
            msg = f"⚡️ Свободная запись к {full_name}\n📅 {t['date']} ⏰ {t['time']}"
            logging.info(f"[{surname}] ОТПРАВКА: {msg}")
            try:
                await bot.send_message(chat_id=chat_id, text=msg)
            except Exception as e:
                logging.warning(f"[{surname}] Не удалось отправить сообщение: {e}")
