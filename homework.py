import requests
import logging
import time
import os

import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}

#TODO: send notification to telegram account
def send_message(bot, message):
    """ """
    pass


def get_api_answer(url, current_timestamp):
    """Request the PRACTICUM API and get response 
    between current_timestamp and current time"""

    url = ENDPOINT
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    return requests.get(url, headers=headers, params=payload).json()


def parse_status(homework):
    """Return the message by homework status"""

    verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    homework_name = homework.get('homework_name')
    return f'Изменился статус проверки работы {homework_name}. {verdict}'


def check_response(response):
    """Return true if changed hamework status"""

    homeworks = response.get('homeworks')
    return len(homeworks) > 0


#TODO: exception and logging module
def main():
    """ """
    
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    pass
    while True:
        try:
            pass
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            pass
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()
