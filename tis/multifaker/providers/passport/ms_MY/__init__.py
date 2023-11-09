import random

from multifaker.providers.passport import D, FN, L, LN, N, f
from multifaker.providers.passport import Provider as BaseProvider


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        number = f"A{N(8)}"
        fn = FN()
        mn = FN()
        ln = LN()
        sex = self.sex()
        issue = D()
        expiry = issue[:-4] + str(int(issue[-4:]) + 5)

        return {
            "type": "P",
            "code": "MYS",
            "number": number,
            "name": f"{fn} {mn} {ln}",
            "nationality": "MALAYSIA",
            "number1": f"{N(12)}",
            "birth": f"{D()}",
            "bp": f.country().upper(),
            "height": f"1{random.randint(50, 90)} CM",
            "sex": f"P-{sex}",
            "issue": issue,
            "expiry": expiry,
            "authority": "UTC SUNGAI PETANI",
            "number2": f"P<MYS{fn}<<{mn}<{ln}".ljust(44, "<"),
            "number3": f"{number}{N(0)}MYS{N(7)}{sex}{N(15)}".ljust(42, "<") + N(2),
        }
