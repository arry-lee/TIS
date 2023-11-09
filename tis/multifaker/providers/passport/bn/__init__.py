import random

from multifaker.providers.passport import D, FN, L, LN, N, f
from multifaker.providers.passport import Provider as BaseProvider


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        sn = FN()
        gn1 = LN()
        gn2 = LN()
        issue = D()
        expiry = issue[:-4] + str(int(issue[-4:]) + 5)
        bp = f.country().upper()
        sex = self.sex()
        number = f"{L(2)}{N(7)}"
        return {
            "type": "P",
            "code": "BGD",
            "number": number,
            "surname": sn,
            "given_names": f"{gn1} {gn2}",
            "number1": N(17),
            "nationality": "BANGLADESHI",
            "birth": D(),
            "sex": sex,
            "bp": bp,
            "authirity": f"DIP/{bp}",
            "issue": issue,
            "expiry": expiry,
            "number2": f"P<BGD{sn}<<{gn1}<{gn2}".ljust(44, "<"),
            "number3": f"{number}{N(1)}BGD{N(7)}{sex}{N(7)}".ljust(42, "<") + N(2),
        }
