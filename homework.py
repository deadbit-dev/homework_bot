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

ERROR_BUF = None


def send_message(bot, message):
    """Send message to telegram account."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('successful dispatch the telegram message')
    except Exception as error:
        logging.error(error)


def get_api_answer(url, current_timestamp):
    """Request the PRACTICUM API."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    response = requests.get(url, headers=headers, params=payload)
    if response.status_code != requests.codes.ok:
        response.raise_for_status()
    logging.info('successful request')
    return response.json()
# FIXME: this not pass test (need raise exception)
#    try:
#        response = requests.get(url, headers=headers, params=payload)
#        if response.status_code != requests.codes.ok:
#            response.raise_for_status()
#        logging.info('successful request')
#        return response.json()
#    except Exception as error:
# NOTE: not send message telegram ?
#        logging.error(error)
#        return {}


# FIXME: parse and check or only parse?
def parse_status(homework):
    """Return the message by homework status."""
    status = homework.get('status')
    if str is not type(status):
        raise ValueError
    verdict = HOMEWORK_STATUSES.get(status)
    homework_name = homework.get('homework_name')
    if str is not type(homework_name):
        raise ValueError
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# FIXME: return homework and check all response ?
def check_response(response):
    """Return true if changed hamework status."""
    homeworks = response.get('homeworks')
    if list is not type(homeworks):
        raise ValueError
    if not homeworks:
        return False
    status = homeworks[0].get('status')
    if str is not type(status):
        raise ValueError
    if status in HOMEWORK_STATUSES:
        return homeworks[0]
    else:
        raise ValueError


def check_env():
    """Check definition env."""
    env_vars = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for var in env_vars:
        try:
            os.environ.pop(var)
        except KeyError as error:
            logging.critical(error)
            return False
    logging.info('all tokens has')
    return True


def main():
    """Entry point module."""
    global ERROR_BUF
    if check_env():
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
                # NOTE: check ?
                if not current_timestamp:
                    raise ValueError
                time.sleep(RETRY_TIME)
            except Exception as error:
                logging.error(error)
                if ERROR_BUF != error:
                    ERROR_BUF = error
                    message = f'Сбой в работе программы: {error}'
                    send_message(bot, message)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
