from datetime import datetime, timedelta
import requests
import json
import time
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc
from pprint import pformat
from selenium.webdriver.common.action_chains import ActionChains

import random

class NationalBank():
    """
    Attributes
    ----------
    session: session
        Cloudscraper requests session that holds National Bank Direct Brokerage session cookies and header information
    token: str
        Bearer authorization token used to validate each request
    user: str
        National Bank Direct Brokerage username
    passw: str
        National Bank Direct Brokerage password

    Methods
    -------
    login()
        Logs in to NBDB account
    get_quote(ticker, market)
        Returns bid and ask price of specified ticker
    get_account_id(currency_type, account_type)
        Returns account ID of the specified account
    get_account_balance(account_id):
        Returns the buying power of the specified account
    validate(account_id, side, qty, symbol, currency, phone, limit_price=None, days_till_expiration=0)
        Validates order info for the place_limit_order() and palce_market_order() functions
    place_market_order(symbol, account_id, currency, side, qty, phone)
        Places market order
    place_limit_order(symbol, account_id, currency, side, qty, phone, limit_price, days_till_expiration=0)
        Places limit order
    cancel_order(order_id)
        Cancels order with the specified order_id
    get_latest_order(account_id)
        Returns info regarding the latest order in the specified account
    get_order(account_id, order_id)
        Returns info regarding the specified order in the specified account
    get_order_status(account_id, order_id)
        Returns the order status of the specified order
    update_session()
        Logs back into NBDB account after being auto logged out
    get_positions(account_id)
        Returns info regarding the positions held in the specified account
    """

    def __init__(self, user, passw):
        """
        Parameters
        ----------
        user: str
            National Bank Direct Brokerage username
        passw: str
            National Bank Direct Brokerage password

        Returns
        -------
        None
        """
        self.user = user
        self.passw = passw
        # 5 min expiry, 300 seconds
        self.NBDB_AUTH_TOKEN = None
        # 6000 second expiry
        self.AKAMAI_COOKIE_TOKEN = None
        self.session = self.login()

    def findTokenCallback(self, eventdata):
        if 'params' in eventdata and 'request' in eventdata['params'] and 'headers' in eventdata['params']['request']:
            headers = eventdata['params']['request']['headers']
            token = headers.get('Authorization')
            if (token):
                self.NBDB_AUTH_TOKEN = token

    def get_tokens_selenium(self, loginPageURL, username, password):
        driver = uc.Chrome(headless=False, enable_cdp_events=True)
        driver.set_window_size(1600, 900)
        # Listen to the HTTP requests for the bearer token
        driver.add_cdp_listener(
            'Network.requestWillBeSent', self.findTokenCallback)

        _WAIT_TIMEOUT = WebDriverWait(driver, 30)

        # Navigate to the provided URL
        driver.get(loginPageURL)

        # Wait for username ID element to load
        _WAIT_TIMEOUT.until(
            EC.presence_of_element_located((By.ID, 'username')))

        # Finds the accept cookies popup and accepts it if it exists
        try:
            agree_button = driver.find_element(
                By.ID, 'didomi-notice-agree-button')
            agree_button.click()
        except:
            print("no agree button found")

        # Find login elements
        username_text_box = driver.find_element(By.ID, "username")
        password_text_box = driver.find_element(By.ID, "password-hidden")
        login_button = driver.find_element(
            By.CSS_SELECTOR, 'button[type="submit"]')

        # Login to NBDB
        username_text_box.send_keys(username)
        password_text_box.send_keys(password)
        login_button.click()

        # Handle 2FA
        sms_2fa_a_tag = _WAIT_TIMEOUT.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a[data-test="choose-factor-type-sms"]')))
        sms_2fa_a_tag.click()

        user_sms_code = input(
            "Enter the 6 digit code sent to your phone:")

        # Enter SMS code
        boxcode = _WAIT_TIMEOUT.until(EC.presence_of_element_located(
            (By.ID, 'validation-code')))
        boxcode.send_keys(user_sms_code)

        # Submit SMS code
        submit_2fa_code_button = _WAIT_TIMEOUT.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'button[data-test="validation-code-submit-button"]'))
        )
        submit_2fa_code_button.click()

        # Wait until the refresh button appears, then we know we are logged in
        _WAIT_TIMEOUT.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[aria-label="Refresh"]'))
        )

        # Load the history page
        driver.get("https://client.bnc.ca/nbdb/history")

        # Wait for the refresh button to appear
        refresh_button = _WAIT_TIMEOUT.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a[aria-label="Refresh"]')))
        refresh_element_overlay_bypass = ActionChains(driver)
        refresh_element_overlay_bypass.move_to_element(refresh_button)

        while True:
            # Click the refresh button
            refresh_element_overlay_bypass.click().perform()

            # Capture all the new request cookies
            cookies = driver.execute_cdp_cmd("Network.getAllCookies", {})
            for cookie in cookies['cookies']:
                if (cookie['name'] == "X-External-User-Context-Token"):
                    self.AKAMAI_COOKIE_TOKEN = cookie['value']

            print(self.AKAMAI_COOKIE_TOKEN)
            print(self.NBDB_AUTH_TOKEN)
            print("--------------")
            # write code to sleep for a random amount of seconds between 2 and 30 seconds
            time.sleep(random.randint(2, 30))

        # Consuming the tokens
        cookies_object = {
            "X-External-User-Context-Token": self.AKAMAI_COOKIE_TOKEN
        }

        headers = {
            "Authorization": self.NBDB_AUTH_TOKEN,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        loginPageURL = "https://orion-api.bnc.ca/orion-api/v1/1/accounts/history?acctNo=669RH9S&acctNo=669RH97&acctNo=669RH9W&period=TWO_YEARS"
        response = requests.get(
            loginPageURL, headers=headers, cookies=cookies_object)

    def consumer_function():
        while True:
            # Get data from the queue and process it
            title = data_queue.get()  # This will block until there's data in the queue
            print(f"Processing title: {title}")

    def login(self):
        URL = "https://client.bnc.ca/nbdb/login"

        captured_requests = self.get_tokens_selenium(
            URL, self.user, self.passw)

        for request in captured_requests:
            print(request)

        exit(1)
        return ""

    def get_quote(self, ticker, market):
        """
        Parameters
        ----------
        ticker: str
            Ticker of stock.
        market: str
            Either 'USA' or 'CAN'

        Returns
        ------------
        dict
            Dictionary containing the current bid and ask price of the ticker.
        """
        quote_url = 'https://orion-api.bnc.ca/orion-api/v1/1/quotes/realtime/?ids='
        to_add = f'AC;{ticker};{market};'

        quote_url += to_add

        response = self.session.get(quote_url).json()[
            'data'][to_add]['finInstrumentPrice']

        return_value = {
            'bid': response['bidPrice'],
            'ask': response['askPrice']
        }

        return return_value

    def get_account_id(self, currency_type, account_type):
        """
        Parameters
        ----------
        currency_type: str
            Either 'USD' or 'CAD'
        account_type: str
            Account type: cash, tfsa, etc.
        Returns
        -------
        str
            Account ID
        """
        currency_type = currency_type.upper()
        account_type = account_type.title()

        account_url = 'https://orion-api.bnc.ca/orion-api/v1/1/portfolios'
        response = self.session.get(account_url).json()[
            'data'][0]['accountList']

        for item in response:
            if currency_type in item['acctTypeDesc'] and account_type in item['acctTypeDesc']:
                return item['acctNo']

        raise Exception('Error! Unabel to find account')

    def get_account_balance(self, account_id):
        """
        Parameters
        ----------
        account_id: str
            Account ID from get_account_id()

        Returns
        -------
        float
            Buying Power
        """
        account_url = f'https://orion-api.bnc.ca/orion-api/v1/1/accounts/assetsDetail?acctNo={account_id}'

        response = self.session.get(account_url).json()[
            'data']['accountAssetDetailList'][0]

        currency = response['account']['acctCurrCd']
        balance = response['assetsDetailByCurrencyList'][currency]['cashAmt']

        return balance

    def validate(self, account_id, side, qty, symbol, currency, phone, limit_price=None, days_till_expiration=0):
        """
        Parameters
        ----------
        account_id: str
            Account ID obtained from get_account_id()
        side: str
            Either 'BUY' or 'SELL'
        qty: int
            Amount of shares to buy
        symbol: str
            Symbol of ticker to buy
        currency: str
            Currency of stock('USD' or 'CAD)
        phone: str
            Phone number associated with account (000-000-0000)
        limit_price: float
            Limit price if applicable
        days_till_expiration: int
            Amount of days until the order expires.

        Returns
        -------
        dict
            Order data used by the place_market_order() and place_limit_order() functions
        """
        symbol = symbol.upper()
        currency = currency.upper()
        side = side.upper()
        qty = str(qty)

        if currency == 'USD':
            country = 'USA'
        elif currency == 'CAD':
            country = 'CAN'

        if limit_price is not None:
            type = 'SPECIFIC'
        else:
            type = 'MARKET'

        if days_till_expiration == 0:
            expiry = 'DAY'
            expiry_date = None
        else:
            expiry = 'DATE'
            expiry_date = datetime.today() + timedelta(days=days_till_expiration)
            day = expiry_date.weekday()

            if day == 5:
                expiry_date += timedelta(days=2)
            elif day == 6:
                expiry_date += timedelta(days=1)

            expiry_date = expiry_date.strftime('%Y-%m-%d')

        validation_url = 'https://orion-api.bnc.ca/orion-api/v1/1/stock-orders/validation'

        validation_data = {
            "stockOrder": {
                "ordId": None,
                "acctNo": account_id,
                "operation": side,
                "ordQty": qty,
                "expiry": expiry,
                "expiryDt": expiry_date,
                "restriction": "NONE",
                "phone": "000-000-0000",
                "finInstrument": {
                    "marketSymbol": {
                        "symbolCd": symbol,
                        "symbolCurrCd": currency,
                        "symbolCntryCd": country
                    },
                    "finInstrumentTypeCd": "STOCK"
                },
                "limitPrice": limit_price,
                "priceType": type,
                "stopLimitPrice": None
            },
            "mode": "INSERT"
        }

        response = self.session.post(
            url=validation_url, json=validation_data).json()

        order_data = {'stockOrder': response['data']['stockOrder']}

        if 'messageList' in response:

            warning_list = []

            for item in response['messageList']:
                if 'your order will be processed by one of our representatives' in item['message']:
                    raise Exception(
                        'An Error Has Occured When Attempting to process your order.')
                else:
                    warning_list.append(item['msgId'])

            order_data['warnsNoList'] = warning_list

        order_data['stockOrder']['phone'] = phone

        return order_data

    def place_market_order(self, symbol, account_id, currency, side, qty, phone):
        """
        Parameters
        ----------
        symbol: str
            Symbol of ticker to buy
        account_id: str
            Account ID obtained from get_account_id()
        currency: str
            Currency of stock('USD' or 'CAD)
        side: str
            Either 'BUY' or 'SELL'
        qty: int
            Amount of shares to buy
        phone: str
            Phone number associated with account (000-000-0000)

        Returns
        -------
        dict
            Containing order ID
        """
        order_data = self.validate(
            account_id, side, qty, symbol, currency, phone)

        order_url = 'https://orion-api.bnc.ca/orion-api/v1/1/stock-orders'

        response = self.session.post(
            url=order_url, json=order_data).json()['data']

        return {'order_id': response['stockOrder']['ordId']}

    def place_limit_order(self, symbol, account_id, currency, side, qty, phone, limit_price, days_till_expiration=0):
        """
        Parameters
        ----------
        symbol: str
            Symbol of ticker to buy
        account_id: str
            Account ID obtained from get_account_id()
        currency: str
            Currency of stock('USD' or 'CAD)
        side: str
            Either 'BUY' or 'SELL'
        qty: int
            Amount of shares to buy
        phone: str
            Phone number associated with account (000-000-0000)
        limit_price: float
            Limit price
        days_till_expiration: int
            Amount of days until the order expires.

        Returns
        -------
        dict
            Containing order ID
        """
        order_data = self.validate(
            account_id, side, qty, symbol, currency, phone, limit_price, days_till_expiration)

        order_url = 'https://orion-api.bnc.ca/orion-api/v1/1/stock-orders'

        response = self.session.post(
            url=order_url, json=order_data).json()['data']

        return {'order_id': response['stockOrder']['ordId']}

    def cancel_order(self, order_id):
        """
        Parameters
        ----------
        order_id: str
            ID of order that is to be cancelled.

        Returns
        -------
        None
        """
        cancel_url = f'https://orion-api.bnc.ca/orion-api/v1/1/stock-orders/{order_id}'

        self.session.delete(cancel_url)

    def get_latest_order(self, account_id):
        """
        Parameters
        ----------
        account_id: str
            Account ID of account containing orders

        Returns
        -------
        dict
            Dictionary containing order information
        """
        order_url = f'https://orion-api.bnc.ca/orion-api/v1/1/orders?acctNo={account_id}'

        order_info = self.session.get(order_url).json()['data']['orderList']

        if len(order_info) == 0:
            raise Exception('Order not Found.')
        else:
            order_info = order_info[0]

        return_dict = {
            'order_id': order_info['ordId'],
            'operation': order_info['operation'],
            'order_quantity': order_info['ordQty'],
            'filled_quantity': order_info['execQty'],
            'fill_price': order_info['avgExecPrice'],
            'order_open': order_info['orderOpen']
        }

        return return_dict

    def get_order(self, account_id, order_id):
        """
        Parameters
        ----------
        account_id: str
            Account ID of account containing orders
        order_id: str
            Order ID

        Returns
        -------
        dict
            Dictionary containing order information
        """
        order_url = f'https://orion-api.bnc.ca/orion-api/v1/1/orders?acctNo={account_id}'

        response = self.session.get(order_url).json()['data']['orderList']

        order_info = []

        for item in response:
            if item['ordId'] == order_id:
                order_info = item
                break

        if len(order_info) == 0:
            raise Exception('Order not Found.')

        return_dict = {
            'order_id': order_info['ordId'],
            'operation': order_info['operation'],
            'order_quantity': order_info['ordQty'],
            'filled_quantity': order_info['execQty'],
            'fill_price': order_info['avgExecPrice'],
            'order_open': order_info['orderOpen']
        }

        return return_dict

    def get_order_status(self, account_id, order_id):
        """
        Parameters
        ----------
        account_id: str
            Account ID of account containing orders
        order_id: str
            Order ID

        Returns
        -------
        bool
            True if order has not filled, False if order has filled
        """
        order_url = f'https://orion-api.bnc.ca/orion-api/v1/1/orders?acctNo={account_id}'

        response = self.session.get(order_url).json()['data']['orderList']

        for item in response:
            if item['ordId'] == order_id:
                return item['orderOpen']

        raise Exception('Order not Found.')

    def update_session(self):
        """
        Returns
        -------
        None
        """
        self.session = self.login()

    def get_positions(self, account_id):
        """
        Parameters
        ----------
        account_id: str
            Account ID of account where positions are held

        Returns
        -------
        dict
            Dictionary containing data pertaining to held positions
        """
        return_dict = {}

        pos_url = f'https://orion-api.bnc.ca/orion-api/v1/1/accounts/assetsDetail?acctNo={account_id}'

        response = self.session.get(pos_url).json()[
            'data']['accountAssetDetailList'][0]
        currency = response['account']['acctCurrCd']
        pos_list = response['assetsDetailByCurrencyList'][currency]['positionList']

        if len(pos_list) == 0:
            raise Exception('Error! No Positions Found.')

        for item in pos_list:
            symbol = item['finInstrument']['quoteIdKey'].split(';')[1]
            eval = item['positionEval']
            return_dict[symbol] = {
                'quantity': item['quantity'],
                'cost': eval['avgCostPrice'],
                'change': eval['pnlAmt'],
                'change_per': eval['pnlPerc'],
                'market_val': eval['marketValueAmt']
            }

        return return_dict
