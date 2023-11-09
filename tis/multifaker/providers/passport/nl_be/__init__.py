from multifaker.providers.passport import Provider as BaseProvider
from multifaker.providers.passport import f, N, L, LN, FN, D
import random


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        sn = FN()
        sn1 = LN()
        gn = FN()
        gn1 = LN()
        number = f"{L(5)}{N(4)}"
        sex = self.sex()

        month = [
            "JAN/JAN",
            "FEB/FEB",
            "MAA/MAR",
            "APR/APR",
            "MEI/MAY",
            "JUN/JUN",
            "JUL/JUL",
            "AUG/AUG",
            "SEP/SEP",
            "OKT/OCT",
            "NOV/NOV",
            "DEC/DEC",
        ]
        month_dict = {m[4:]: m[:3] for m in month}

        issue = D().split()
        issue[1] = month_dict[issue[1]]
        issue = " ".join(issue)
        expiry = issue[:-4] + str(int(issue[-4:]) + 10)

        birth = D().split()
        birth[1] = month_dict[birth[1]]

        return {
            "type": "P",
            "code": "NLD",
            "nationality": "Nederlandse",
            "number": number,
            "surname": f"{sn.title()} {sn1.title()}",
            "surname1": f"e/v {LN().title()}",
            "given_names": f"{gn.title()} {gn1.title()}",
            "birth": f"{birth[0]} {birth[1]}",
            "birth1": f"{birth[2]}",
            "bp": f"{f.country()}",
            "sex": f"{'L/M' if sex == 'M' else 'V/F'}",
            "height": f"1,{random.randint(50, 90)}m",
            "issue": issue,
            "expiry": expiry,
            "authority": f"{f.name()}",
            "number1": f"P<NLD{sn}<{sn1}<<{gn}<{gn1}".ljust(44, "<"),
            "number2": f"{number}{N(1)}NLD{N(7)}{sex}{N(16)}".ljust(42, "<") + N(2),
        }
