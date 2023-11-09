from multifaker.providers.passport import Provider as BaseProvider
from multifaker.providers.passport import f, N, L, LN, FN, D
import random


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        firstname, midname, lastname = (
            f.first_name().upper(),
            f.last_name().upper(),
            f.last_name().upper(),
        )
        sex = random.choice("WF")
        number = N(7)
        issue = D()
        expiry = issue[:-4] + str(int(issue[-4:]) + 5)
        return {
            "type": "P",
            "code": "IDN",
            "number": f"A {number}",
            "sex": f"{'L/M' if sex == 'M' else 'V/F'}",
            "name": f"{firstname} {midname} {lastname}",
            "nationality": "INDONESIA",
            "birth": f"{D()}",
            "bp": f"{f.country().upper()}",
            "issue": issue,
            "expiry": expiry,
            "number1": f"{N(1)}{L()}{N(2)}{L(2)}{N(4)}-{L(3)}",
            "authority": f"{f.name().upper()}",
            "number2": f"NIKIM {N(12)}",
            "number3": f"P<IDN{lastname}<<{firstname}<{midname}".ljust(44, "<"),
            "number4": f"A{number}<{N(1)}IDN{N(7)}{sex}{N(7)}".ljust(42, "<") + N(2),
        }
