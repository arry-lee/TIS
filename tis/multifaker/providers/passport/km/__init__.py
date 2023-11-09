import random

from multifaker.providers.passport import D, FN, L, LN, N, f
from multifaker.providers.passport import Provider as BaseProvider


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        number = f"N{N(7)}"
        sn1 = FN()
        sn2 = FN()
        gn = LN()
        sex = self.sex()
        month = [
            "JAN/JAN",
            "FEV/FEB",  #
            "MARS/MAR",
            "AVR/APR",  #
            "MEI/MAY",
            "JUNE/JUN",  #
            "JULY/JUL",
            "AUG/AUG",
            "SEPT/SEP",  #
            "OCT/OCT",
            "NOV/NOV",  #
            "DEC/DEC",
        ]
        month_dict = {m[-3:]: m[:-4] for m in month}
        birth = D().split()
        birth.insert(2, "/" + month_dict[birth[1]])
        birth = " ".join(birth)
        issue = D().split()
        issue.insert(2, "/" + month_dict[issue[1]])
        issue = " ".join(issue)
        expiry = issue[:-4] + str(int(issue[-4:]) + 5)
        return {
            "number": number,
            "type": "PN",
            "code": "KHM",
            "surname": f"{sn1} {sn2}",
            "given_name": f"{gn}",
            "nationality": "CAMBODIAN",
            "birth": birth,
            "bp": f.country().upper(),
            "sex": sex,
            "issue": issue,
            "authority": "MIN PHNOM PENH",
            "expiry": expiry,
            "number1": f"PNKHM{sn1}<{sn2}<<{gn}".ljust(44, "<"),
            "number2": f"{number}<{N(1)}KHM{N(7)}M{N(15)}".ljust(42, "<") + N(2),
        }
