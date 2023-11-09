from multifaker.providers.passport import Provider as BaseProvider
from multifaker.providers.passport import f, N, L, LN, FN, D
import random


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        surname = LN()
        given_names = FN()
        middle_name = LN()
        sex = self.sex()
        issue = D()
        expiry = issue[:-4] + str(int(issue[-4:]) + 10)
        number = f"P{N(7)}A"

        return {
            "type": "P",
            "code": "PHL",
            "number": number,
            "surname": surname,
            "given_names": given_names,
            "middle_name": middle_name,
            "birth": D(),
            "nationality": "FILIPINO",
            "sex": sex,
            "bp": f"{f.country()}",
            "issue": issue,
            "expiry": expiry,
            "authority": f"{LN()} {FN()}",
            "number1": f"P<PHL{surname}<<{given_names}".ljust(44, "<"),
            "number2": f"{number}{N(1)}PHL{N(7)}{sex}{N(7)}".ljust(42, "<") + N(2),
        }
