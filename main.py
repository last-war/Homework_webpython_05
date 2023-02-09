import argparse
import platform

import aiohttp
import asyncio
from datetime import date
import const

"""
py main.py --days -d how many days
py main.py --curr -c list of currency names
'AUD', 'AZN', 'BYN', 'CAD', 'CHF', 'CNY', 'CZK', 'DKK', 'EUR', 'GBP', 'GEL', 'HUF', 'ILS', 'JPY',
               'KZT', 'MDL', 'NOK', 'PLN', 'SEK', 'SGD', 'TMT', 'TRY', 'UAH', 'USD', 'UZS', 'XAU'
"""

parser = argparse.ArgumentParser(description='exchange currency')

parser.add_argument('-d', '--days', required=True)
parser.add_argument('-c', '--curr', default='EUR,USD')


def check_args(need_days: int, currency: list) -> list:
    if need_days > const.MAX_DAYS:
        need_days = const.MAX_DAYS
    for cur_currency in currency:
        if not cur_currency in const.PB_CURRENCY:
            currency.remove(cur_currency)
    if not len(currency):
        currency.append('USD')
    return [need_days, currency]


def parse_args(args) -> list:
    """check for valid params"""
    return check_args(int(args.get('days')), args.get('curr').split(','))


def prepare_urls(days: int) -> list:
    """"""
    rez = []
    base = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='
    for itr in range(date.toordinal(date.today()), date.toordinal(date.today())-days, -1):
        rez.append(base+date.fromordinal(itr-1).strftime('%d.%m.%Y'))
    return rez


def format_result(cur_list: list, raw: dict) -> dict:
    """format and clean result"""
    rez = dict()
    rez[raw.get('date')] = dict()
    f_date = rez[raw.get('date')]
    for c_cur in cur_list:
        list_rate = raw.get('exchangeRate')
        for itr in list_rate:
            if c_cur == itr.get('currency'):
                f_sale = itr.get('saleRate')
                f_purchase = itr.get('purchaseRate')
                f_date[c_cur] = {'sale': f_sale, 'purchase': f_purchase}
                break
    return rez


async def as_get_curr_ratelist(agrs: list) -> list:
    rez = []
    async with aiohttp.ClientSession() as session:
        for url in prepare_urls(agrs[0]):
            #print(f'Starting {url}')
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        rez.append(format_result(agrs[1], result))
                    else:
                        print(f"Error status: {response.status} for {url}")
            except aiohttp.ClientConnectorError as err:
                print(f'Connection error: {url}', str(err))
    print(rez)
    return rez


def get_curr_ratelist(params):
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(as_get_curr_ratelist(params))


if __name__ == '__main__':
    params = parse_args(vars(parser.parse_args()))
    rez = get_curr_ratelist(params)
    print(rez)
