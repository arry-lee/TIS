import random

from multifaker.providers.passport import D, FN, L, LN, N, f
from multifaker.providers.passport import Provider as BaseProvider


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        number = N(8)
        sex = self.sex()
        issue = D()
        expiry = issue[:-4] + str(int(issue[-4:]) + 10)
        sn1 = FN()
        sn2 = FN()
        gn = LN()
        return {
            "type": "P",
            "code": "NPL",
            "number": number,
            "surname": f"{sn1} {sn2}",
            "given_names": gn,
            "nationality": "NEPALESE",
            "birth": D(),
            "number1": f"{N(2)}-{N(2)}-{N(2)}-{N(5)}",
            "sex": sex,
            "bp": f.country().upper(),
            "authority": "MOFA,DEPARTMET OF PASSPORT",
            "issue": issue,
            "expiry": expiry,
            "number2": f"P<NPL{sn1}<{sn2}<<{gn}".ljust(44, "<"),
            "number3": f"{number}<{N(1)}NPL{N(7)}{sex}{N(18)}".ljust(42, "<") + N(2),
        }
