# nbdb-python-api [post Akamai - VERY WIP]
> This is currently broken since NBDB upgraded to CIAM and everything is now behind Akamai Bot Defender. This fork aims to get it working with the new setup.

nbdb-python-api is an open source python library that acts as a API wrapper for National Bank Direct Brokerage.

## Installation
TBD

## Features
TBD

## Example Usage
```python
from nbdapi import NationalBank

ticker = 'SU'
market = 'USA'
account_currency = 'USD'
account_type = 'cash'
phone = '000-000-0000'

nb = NationalBank('username', 'password')

account_id = nb.get_account_id(account_currency, account_type)

buying_power = nb.get_account_balance(account_id)

ask_price = nb.get_quote(ticker, market)['ask']

if ask_price < 30:
    shares = buying_power // ask_price
    nb.place_market_order(ticker, account_id, account_currency, 'BUY', shares, phone)

    print(nb.get_positions(account_id)
else:
    print('Price too high')
```
