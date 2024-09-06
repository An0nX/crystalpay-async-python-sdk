import httpx
import json
import hashlib


class InvoiceType:
    topup = "topup"
    purchase = "purchase"


class PayoffSubtractFrom:
    balance = "balance"
    amount = "amount"


class crystal_utils:
    """Дополнительный класс, содержащий в себе дополнительные функции для работы SDK"""

    async def concatParams(self, concatList, kwargs):
        temp = concatList
        for key, param in kwargs:
            temp[key] = param
        return temp

    """ Асинхронная отправка запроса на API """

    async def requestsApi(self, method, function, params):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.crystalpay.io/v2/{method}/{function}/",
                data=params,
                headers={"Content-Type": "application/json"},
            )
            response_data = response.json()

        if response_data["error"]:
            raise Exception(response_data["errors"])

        del response_data["error"]
        del response_data["errors"]

        return response_data


class CrystalPAY:

    def __init__(self, auth_login, auth_secret, salt):
        self.Me = self.Me(auth_login, auth_secret, crystal_utils())
        self.Method = self.Method(auth_login, auth_secret, crystal_utils())
        self.Balance = self.Balance(auth_login, auth_secret, crystal_utils())
        self.Invoice = self.Invoice(auth_login, auth_secret, crystal_utils())
        self.Payoff = self.Payoff(auth_login, auth_secret, salt, crystal_utils())
        self.Ticker = self.Ticker(auth_login, auth_secret, crystal_utils())

    class Me:

        def __init__(self, auth_login, auth_secret, crystal_utils):
            self.__auth_login = auth_login
            self.__auth_secret = auth_secret
            self.__crystal_utils = crystal_utils

        """ Асинхронное получение информации о кассе """

        async def getinfo(self):
            response = await self.__crystal_utils.requestsApi(
                "me",
                "info",
                json.dumps(
                    {"auth_login": self.__auth_login, "auth_secret": self.__auth_secret}
                ),
            )
            return response

    class Method:

        def __init__(self, auth_login, auth_secret, crystal_utils):
            self.__auth_login = auth_login
            self.__auth_secret = auth_secret
            self.__crystal_utils = crystal_utils

        """ Асинхронное получение информации о методах оплаты """

        async def getlist(self):
            response = await self.__crystal_utils.requestsApi(
                "method",
                "list",
                json.dumps(
                    {"auth_login": self.__auth_login, "auth_secret": self.__auth_secret}
                ),
            )
            return response

        """ Асинхронное изменение настроек метода оплаты """

        async def edit(self, method, extra_commission_percent, enabled):
            response = await self.__crystal_utils.requestsApi(
                "method",
                "edit",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "method": method,
                        "extra_commission_percent": extra_commission_percent,
                        "enabled": enabled,
                    }
                ),
            )
            return response

    class Balance:

        def __init__(self, auth_login, auth_secret, crystal_utils):
            self.__auth_login = auth_login
            self.__auth_secret = auth_secret
            self.__crystal_utils = crystal_utils

        """ Асинхронное получение баланса кассы """

        async def getinfo(self, hide_empty=False):
            response = await self.__crystal_utils.requestsApi(
                "balance",
                "info",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "hide_empty": hide_empty,
                    }
                ),
            )
            return response["balances"]

    class Invoice:

        def __init__(self, auth_login, auth_secret, crystal_utils):
            self.__auth_login = auth_login
            self.__auth_secret = auth_secret
            self.__crystal_utils = crystal_utils

        """ Асинхронное получение информации о счёте """

        async def getinfo(self, id):
            response = await self.__crystal_utils.requestsApi(
                "invoice",
                "info",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "id": id,
                    }
                ),
            )
            return response

        """ Асинхронное выставление счёта на оплату """

        async def create(self, amount, type_, lifetime, **kwargs):
            response = await self.__crystal_utils.requestsApi(
                "invoice",
                "create",
                json.dumps(
                    await self.__crystal_utils.concatParams(
                        {
                            "auth_login": self.__auth_login,
                            "auth_secret": self.__auth_secret,
                            "amount": amount,
                            "type": type_,
                            "lifetime": lifetime,
                        },
                        kwargs.items(),
                    )
                ),
            )
            return response

    class Payoff:

        def __init__(self, auth_login, auth_secret, salt, crystal_utils):
            self.__auth_login = auth_login
            self.__auth_secret = auth_secret
            self.__salt = salt
            self.__crystal_utils = crystal_utils

        """ Асинхронное создание заявки на вывод средств """

        async def create(self, amount, method, wallet, subtract_from, **kwargs):
            signature_string = f"{amount}:{method}:{wallet}:{self.__salt}"
            signature = hashlib.sha1(str.encode(signature_string)).hexdigest()

            response = await self.__crystal_utils.requestsApi(
                "payoff",
                "create",
                json.dumps(
                    await self.__crystal_utils.concatParams(
                        {
                            "auth_login": self.__auth_login,
                            "auth_secret": self.__auth_secret,
                            "signature": signature,
                            "amount": amount,
                            "method": method,
                            "wallet": wallet,
                            "subtract_from": subtract_from,
                        },
                        kwargs.items(),
                    )
                ),
            )
            return response

        """ Асинхронное подтверждение заявки на вывод средств """

        async def submit(self, id):
            signature_string = f"{id}:{self.__salt}"
            signature = hashlib.sha1(str.encode(signature_string)).hexdigest()

            response = await self.__crystal_utils.requestsApi(
                "payoff",
                "submit",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "signature": signature,
                        "id": id,
                    }
                ),
            )
            return response

        """ Асинхронная отмена заявки на вывод средств """

        async def cancel(self, id):
            signature_string = f"{id}:{self.__salt}"
            signature = hashlib.sha1(str.encode(signature_string)).hexdigest()

            response = await self.__crystal_utils.requestsApi(
                "payoff",
                "cancel",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "signature": signature,
                        "id": id,
                    }
                ),
            )
            return response

        """ Асинхронное получение информации о заявке на вывод средств """

        async def getinfo(self, id):
            response = await self.__crystal_utils.requestsApi(
                "payoff",
                "info",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "id": id,
                    }
                ),
            )
            return response

    class Ticker:

        def __init__(self, auth_login, auth_secret, crystal_utils):
            self.__auth_login = auth_login
            self.__auth_secret = auth_secret
            self.__crystal_utils = crystal_utils

        """ Асинхронное получение информации о тикерах """

        async def getlist(self):
            response = await self.__crystal_utils.requestsApi(
                "ticker",
                "list",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                    }
                ),
            )
            return response["tickers"]

        """ Асинхронное получение курса валют по отношению к рублю """

        async def get(self, tickers):
            response = await self.__crystal_utils.requestsApi(
                "ticker",
                "get",
                json.dumps(
                    {
                        "auth_login": self.__auth_login,
                        "auth_secret": self.__auth_secret,
                        "tickers": tickers,
                    }
                ),
            )
            return response
