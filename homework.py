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
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def send_message(bot, message):
    """Send message to telegram account."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('successful dispatch the telegram message')
    except telegram.TelegramError as error:
        message = f'telegram message dispatch error: {error}'
        logging.error(message)
        raise telegram.error.TelegramError(message)


def get_api_answer(url, current_timestamp):
    """Request the PRACTICUM API."""
    current_timestamp = current_timestamp or int(time.time())
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(url, headers=headers, params=payload)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
        logging.info('successful request API')
        return response.json()
    except requests.exceptions.RequestException:
        message = f'API request error, statuts_code: {response.status_code}'
        logging.error(message)
        raise requests.exceptions.RequestException(message)


def parse_status(homework):
    """Return the message by homework status."""
    status = homework.get('status')
    if not isinstance(status, str):
        message = f'not correct status: {status}'
        logging.error(message)
        return message
    verdict = HOMEWORK_STATUSES.get(status)
    homework_name = homework.get('homework_name')
    if not isinstance(homework_name, str):
        message = f'not correct homework_name: {homework_name}'
        logging.error(message)
        return message
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Return true if changed hamework status."""
    homeworks = response.get('homeworks')
    if homeworks is None or not isinstance(homeworks, list):
        message = f'not correct homeworks: {homeworks}'
        logging.error(message)
        raise ValueError(message)
    if not homeworks:
        return False
    status = homeworks[0].get('status')
    if status in HOMEWORK_STATUSES:
        return homeworks[0]
    message = f'not correct status: {status}'
    logging.error(message)
    raise ValueError(message)


def check_env():
    """Check definition env."""
    env_vars = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for var in env_vars:
        if var is None:
            logging.critical('not found environment var')
            return False
    logging.info('successful found all tokens')
    return True


def main():
    """Entry point module."""
    if not check_env():
        return
    error_buf = None
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if error_buf != message:
                error_buf = message
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
