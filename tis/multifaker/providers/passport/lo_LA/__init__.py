import random

from multifaker.providers.passport import D, FN, L, LN, N, f
from multifaker.providers.passport import Provider as BaseProvider


class Provider(BaseProvider):
    """护照信息"""

    def passport(self):
        issue = D().title()
        expiry = issue[:-4] + str(int(issue[-4:]) + 5)
        return {
            "issue": issue,
            "expiry": expiry,
            "entries": "Multiple",
            "issue_area": f.country().upper(),
            "date": f"{D().title()}",
            "number": N(9),
            "type": "C-B1",
            "remarks": "ກະຊວງ ສາທາລະນະສກ",
            "kc": "NON",
        }
