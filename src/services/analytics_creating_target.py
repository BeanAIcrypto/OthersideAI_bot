import json
import os
import logging
import requests
from datetime import datetime
import tzlocal


logger = logging.getLogger(__name__)

GRASPIL_API_KEY = os.getenv("GRASPIL_API_KEY")
url = "https://api.graspil.com/v1/send-target"
async def analytics_creating_target(user_id, user_name, target_start_id, value=None, unit=None):

    local_timezone = tzlocal.get_localzone()
    current_time = datetime.now(local_timezone)

    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S%z')
    formatted_time = formatted_time[:-2] + ':' + formatted_time[-2:]

    event_data = {
        "target_id": target_start_id,
        "user_id": user_id,
        "date": formatted_time,
        "value": value,
        "unit": unit
    }
    headers = {
        "Api-Key": GRASPIL_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(event_data))

    if response.status_code == 200 and response.json().get("ok"):
        logger.info(f"Целевое событие для пользователя {user_name} (ID: {user_id}) успешно отправлено.")
    else:
        logger.error(f"Ошибка при отправке целевого события: {response.text}")
