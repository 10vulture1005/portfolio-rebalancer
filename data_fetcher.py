# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    data_fetcher.py                                    :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: Time Money Code <->                        +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2025/06/05 18:42:32 by Time Money        #+#    #+#              #
#    Updated: 2025/06/05 18:42:32 by Time Money       ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


import yfinance as yf
import requests

# Example: {'USD': 1.0, 'EUR': 0.92, ...}
CURRENCY_CACHE = {}


def fetch_current_prices(assets):
    """Fetch current prices for a list of assets using Yahoo Finance."""
    prices = {}
    for asset in assets:
        try:
            ticker = yf.Ticker(asset.ticker)
            price = ticker.history(period="1d").iloc[-1]["Close"]
            prices[asset.ticker] = price
        except Exception as e:
            print(f"Error fetching price for {asset.ticker}: {e}")
            prices[asset.ticker] = None
    return prices


def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another using exchangerate.host API."""
    if from_currency == to_currency:
        return amount
    pair = f"{from_currency}_{to_currency}"
    if pair in CURRENCY_CACHE:
        rate = CURRENCY_CACHE[pair]
    else:
        try:
            url = f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}"
            response = requests.get(url)
            data = response.json()
            rate = data["result"]
            CURRENCY_CACHE[pair] = rate
        except Exception as e:
            print(f"Error converting currency {from_currency} to {to_currency}: {e}")
            return None
    return amount * rate
