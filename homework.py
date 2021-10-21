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
        logging.error(error)
        telegram.error.TelegramError(error)


def get_api_answer(url, current_timestamp):
    """Request the PRACTICUM API."""
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    response = requests.get(url, headers=headers, params=payload)
    if response.status_code != requests.codes.ok:
        message = f'API request error, statuts_code: {response.status_code}'
        logging.error(message)
        response.raise_for_status()
    logging.info('successful request API')
    return response.json()


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
    if homeworks is None:
        message = f'not correct homeworks: {homeworks}'
        logging.error(message)
        raise ValueError(message)
    if not homeworks:
        return False
    status = homeworks[0].get('status')
    if status in HOMEWORK_STATUSES:
        return homeworks[0]
    else:
        message = f'not correct status: {status}'
        logging.error(message)
        raise ValueError(message)


def check_env():
    """Check definition env."""
    env_vars = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for var in env_vars:
        if os.environ.get(var, True):
            logging.critical(f'not found environment var: {var}')
            return False
    logging.info('all tokens has')
    return True


def main():
    """Entry point module."""
    ERROR_BUF = None
    if not check_env():
        return
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
            if not current_timestamp:
                message = f'not correct current_timestamp: {current_timestamp}'
                logging.error(message)
                raise ValueError(message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if ERROR_BUF != message:
                ERROR_BUF = message
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
