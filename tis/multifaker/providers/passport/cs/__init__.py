from multifaker.providers.passport import Provider as BaseProvider
from multifaker.providers.passport import f, N, L, LN, FN, D
import random


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        issue = f.date_this_decade().strftime("%m.%d.%Y")
        expiry = issue[:-4] + str(int(issue[-4:]) + 10)
        sex = self.sex()
        bp = f"{f.country()} {N(1)}"
        sn = FN()
        gn = LN()
        number = N(8)
        return {
            "type": "P",
            "code": "CZE",
            "number": number,
            "surname": sn,
            "given_names": gn,
            "nationality": "ČESKÁ REPUBLIKA/CZECH REPUBLIC",
            "number1": f"{N(6)}/{N(4)}",
            "birth": f"{f.date_of_birth().strftime('%m.%d.%Y')}",
            "sex": sex,
            "bp": bp,
            "issue": issue,
            "expiry": expiry,
            "authority": bp,
            "number2": f"P<CZE{sn}<<{gn}".ljust(44, "<"),
            "number3": f"{number}<{N(1)}CZE{N(7)}{sex}{N(16)}".ljust(42, "<") + N(2),
        }
