from http import HTTPStatus

import requests
import logging
import time
import os

import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(os.sys.stdout)]
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

LAST = 0


def send_message(bot, message):
    """Send message to telegram account."""
    bot.send_message(CHAT_ID, message)
    logging.info('successful dispatch the message')


def get_api_answer(url, current_timestamp):
    """Request the PRACTICUM API."""
    url = ENDPOINT
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    response = requests.get(url, headers=headers, params=payload)
    if response.status_code != HTTPStatus.OK:
        response.raise_for_status()
    return response.json()


def parse_status(homework):
    """Return the message by homework status."""
    verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    homework_name = homework.get('homework_name')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Return true if changed hamework status."""
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise AttributeError
    if not len(homeworks):
        return False
    if not homeworks[LAST].get('status') in HOMEWORK_STATUSES.keys():
        raise AttributeError
    return True


def check_env():
    """Check definition env."""
    env_vars = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for var in env_vars:
        try:
            os.environ.pop(var)
        except KeyError as error:
            logging.critical(error)


# TODO: exception and logging module
def main():
    """Entry point module."""
    check_env()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            if check_response(response):
                homework = response.get('homeworks')[LAST]
                message = parse_status(homework)
                send_message(bot, message)
                current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(error)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()
