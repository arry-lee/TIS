from faker import Faker as _Faker

from .locale_codes import lang_codes


class Faker:  # noqa
    """已经存在的语种和不存在的语种假数据引擎类"""

    def __new__(cls, locale=None):
        if locale in lang_codes:
            klass = _Faker(providers=[f"multifaker.providers.lorem.{locale}"])
            klass.locale = locale
            return klass
        if locale in ("HKG", "tw", "MO"):
            klass = _Faker(locale="zh_CN")
            klass.locale = locale
            return klass
        return _Faker(locale=locale)
