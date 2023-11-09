import random
import string

from faker import Faker
from faker.providers import BaseProvider

f = Faker("en")
# N = f.random_number  # 随机数字

def N(n=1):
    """随机数字串"""
    return str(f.random_number(n)).ljust(n,'0')

def L(n=1):
    """随机字母"""
    return "".join(random.sample(string.ascii_uppercase, n))


def D():
    """随机日期"""
    return f.date_this_decade().strftime("%d %b %Y").upper()


def LN():
    return f.last_name().upper()


def FN():
    return f.first_name().upper()


class Provider(BaseProvider):
    
    def sex(self):
        return random.choice("FM")
    
    def passport(self):
        pass
