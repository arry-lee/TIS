import random

from multifaker.providers.passport import D, FN, L, LN, N, f
from multifaker.providers.passport import Provider as BaseProvider


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        number = f"N{N(7)}"
        sex = self.sex()
        birth = f.date_of_birth().strftime("%d/%m/%Y")
        issue = f.date_this_decade().strftime("%d/%m/%Y")
        expiry = issue[:-4] + str(int(issue[-4:]) + 10)
        sn = FN()
        gn = LN()
        number1 = f"{N(9)}{L(1)}"
        return {
            "type": "PA",
            "code": "LKA",
            "number": number,
            "surname": sn,
            "given_names": gn,
            "job": "HOUSE MAID",
            "nation": "SRI LANKAN",
            "birth": birth,
            "number1": number1,
            "sex": sex,
            "bp": f.country().upper(),
            "authority": "කෝලෝම්බෝ",
            "issue": issue,
            "expiry": expiry,
            "number2": f"PALKA{sn}<<{gn}".ljust(44, "<"),
            "number3": f"{number}<{N(1)}LKA{N(7)}{sex}{N(7)}{number1}".ljust(42, "<")
            + N(2),
        }
