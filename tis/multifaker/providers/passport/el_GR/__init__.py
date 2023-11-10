from multifaker.providers.passport import Provider as BaseProvider
from multifaker.providers.passport import f, N, L, LN, FN, D
import random

from multifaker.providers.lorem.el_GR import Provider as LoremProvider

# faker_el = _Faker()


class Provider(BaseProvider, LoremProvider):
    """护照信息"""

    def passport(self):
        number = f"{L(2)}{N(7)}"
        birth = f.date_of_birth().strftime("%d %b %Y")
        issue = f.date_this_decade().strftime("%d %b %Y")
        birth = birth[:-4] + birth[-2:]
        issue = issue[:-4] + issue[-2:]

        expiry = issue[:-2] + str(int(issue[-2:]) + 5).ljust(2, "0")
        # expiry = expiry[:-4] + expiry[-2]
        sex = self.sex()
        name_en = LN()
        surname_en = FN()

        return {
            "type": "P",
            "code": "ΕΛΛ",
            "code_en": "/GRC",
            "number": number,
            "surname": self.word().upper(),
            "surname_en": surname_en,
            "name": self.word().upper(),
            "name_en": name_en,
            "nationality": "ΕΛΛΗΝΙΚΗ",
            "nationality_en": "/HELLENIG",
            "sex": sex,
            "birth": birth,
            "bp": self.word().upper(),
            "bp1": "GRC",
            "bp_en": f"{f.country().upper()}",
            "issue": issue,
            "expiry": expiry,
            "authority": "Α.Ε.Α/Δ.Δ-N.P.C.",
            "height": f"1,{random.randint(50, 90)}",
            "number1": f"P<GRC{surname_en}<<{name_en}".ljust(44, "<"),
            "number2": f"{number}{N(1)}GRC{N(7)}{sex}{N(7)}".ljust(42, "<") + N(2),
        }
