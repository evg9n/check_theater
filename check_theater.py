from time import sleep
from datetime import time, datetime
from smtplib import SMTP
from typing import List, Union
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from requests import get
from logging import getLogger, basicConfig, INFO

from config import PASS, RECIPIENT, HOST, PORT, LOGIN

logger = getLogger()
format_log = '%(levelname)s [%(asctime)s] %(message)s'
datefmt = '%d-%m-%Y %H:%M:%S'
basicConfig(level=INFO, filename='logging.log', format=format_log, datefmt=datefmt)


def send_mail(sender: str, password: str, recipient: Union[str, List[str]],
              subject: str, message: str, host: str, port: int) -> bool:
    """
    Отправка сообщения по электронной почте

    :param sender: str Отправитель адрес электронной почты
    :param password: str Пароль от электронной почты отправителя
    :param recipient: str Получатель, если несколько получателей то List[str]
    :param subject: str Тема
    :param message: str Сообщение
    :param host: str Хост
    :param port: str Порт
    :return: Возвращает bool
    """
    server = SMTP(host, port)
    server.starttls()

    try:
        server.login(sender, password)
        msg = MIMEText(message)
        msg['Subject'] = subject
        server.sendmail(sender, recipient, msg.as_string())
        logger.info('Message send')
        return True

    except Exception as error:
        logger.error(f"{error}")
        return False


def check(find_month: str, find_play: List[str]) -> List:
    """
    Проверяет есть спектакли из списка find_play на месяц month

    :param find_month: str поиск по месяцу, все символы в нижнем регистре,
    :param find_play: List[str] с названиями спектаклей,
        названия аналогичны как на сайте https://russdramteatr.ru/index.php/ru/afisha
    :return: Возвращает List с найденными спектаклями
    """
    result = list()
    headers = {
        'Accept-Language': 'en-US,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/109.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://russdramteatr.ru/',
        'Connection': 'keep-alive',
    }
    url = 'https://russdramteatr.ru/index.php/ru/afisha'
    html = get(url, headers)
    logger.info(f'status_code: {html.status_code}')
    html = BeautifulSoup(html.text, 'lxml')
    number = 0
    afisha = html.find(name='section', class_='blog afisha')

    while True:

        play = afisha.find(name='div', class_=f'items-row cols-1 row-{number}')
        if play is None:
            logger.info(f'End find')
            return result
        if not find_play:
            logger.info(f'Stop find')
            return result

        for name_play in find_play:
            if name_play.lower() in str(play.contents).lower():
                month = str(play.find(name='span', class_='date_mod').text).strip()
                if month.lower()[:-1] == find_month.lower()[:-1]:
                    result.append(name_play)
                    logger.info(f"add {name_play}")
                    find_play.remove(name_play)

        number += 1


def i_am_sleep(stand_up_hour: int = 0, stand_up_minute: int = 0) -> None:
    """
    Пауза до stand_up_hour:stand_up_minute
    :param stand_up_hour: Час
    :param stand_up_minute: Минуты
    :return: None
    """
    try:
        time(hour=stand_up_hour, minute=stand_up_minute)
    except ValueError:
        logger.error('hour or minute must be in 0..23')
        stand_up_hour = stand_up_minute = 0
        logger.info('Reset time 00:00')
    now = datetime.now().now()
    now_hour = now.hour
    now_minute = now.minute

    second_sleep = ((stand_up_hour - now_hour) * 60 + (stand_up_minute - now_minute)) * 60
    second_sleep = second_sleep if second_sleep >= 0 else second_sleep + 86400
    logger.info(f'Sleep {second_sleep} second')
    sleep(second_sleep if second_sleep >= 0 else second_sleep + 86400)
    logger.info('Stand up')


def main() -> bool:
    list_play = ['Собачье сердце']
    month = "апреля"
    playes = check(find_month=month, find_play=list_play)
    if playes:
        logger.info("Found OK")
        text = f'В {month[:-1]}е есть желаемые спектакли:\n'
        for play in playes:
            text += play + '\n'

        text += f'\n\n\n\nКупить можно здесь: https://russdramteatr.ru/index.php/ru/afisha'
        subject = 'ПОЯВИЛИИИСЬ СПЕКТАЛИИИ'

        result_send = send_mail(sender=LOGIN, recipient=RECIPIENT, password=PASS,
                                subject=subject, message=text, host=HOST, port=PORT)
        if result_send:
            logger.info('OK Send')
            return True
        else:
            logger.error('BAD Send')
            return False
    else:
        logger.info('Not found')
        return False


if __name__ == "__main__":
    main()
