"""
    多语言假数据生成模块
    生成各种语言的假数据
  1. Italian                    2. Hindi                      3. French
  4. Spanish; Castilian         5. Vietnamese                 6. Arabic
  7. Macedonian                 8. Bosnian-Croatian-Serbian   9. Norwegian Nynorsk
 10. Azerbaijani               11. Bulgarian                 12. Georgian
 13. Galician                  14. Amharic                   15. Yiddish
 16. Norwegian                 17. Estonian                  18. Japanese
 19. Haitian; Haitian Creole   20. Belarusian                21. Greek, Modern
 22. Welsh                     23. Albanian                  24. Marathi (Marāṭhī)
 25. Armenian                  26. Slovene                   27. Korean
 28. Irish                     29. Bengali                   30. Serbian
 31. Finnish                   32. Catalan; Valencian        33. Croatian
 34. Dutch                     35. Swedish                   36. Tagalog
 37. Danish                    38. Kannada                   39. Maltese
 40. Swahili                   41. Latvian                   42. Telugu
 43. Ukrainian                 44. Romanian, Moldavian, ...  45. Persian
 46. Latin                     47. Slovak                    48. Icelandic
 49. Portuguese                50. Urdu                      51. Gujarati
 52. Tamil                     53. Khmer                     54. Malay
 55. Afrikaans                 56. Basque                    57. Polish
 58. German                    59. Esperanto                 60. Indonesian
 61. Chinese                   62. Czech                     63. Hebrew (modern)
 64. Lithuanian                65. Turkish                   66. Bosnian
 67. Hungarian                 68. Thai                      69. Russian
"""

from faker import Faker as _Faker

FAKER_ZH = _Faker('zh_CN')
FAKER_EN = _Faker('en')

LANG_TUPLE = [
    ("id", "Indonesian", "印尼语"),  # 60. Indonesian
    ("fil_PH", "Filipino", "菲律宾语"),
    ("nl_be", "Dutch", "荷兰语"),  # 34. Dutch
    ("cs", "Czech", "捷克语"),  # 62. Czech
    ("el_GR", "Greek", "希腊语"),  # 21. Greek, Modern
    ("bn", "Bengali", "孟加拉语"),  # 29. Bengali
    ("ne", "Nepali", "尼泊尔语"),
    ("si", "Sinhala", "僧伽罗语"),
    ("km", "Khmer", "柬埔寨语"),  # 53. Khmer
    ("lo_LA", "Lao", "老挝语"),
    ("ms_MY", "Malay", "马来语"),
]  # 54. Malay

LANG_CODES = (
    "bn",
    "cs",
    "fil_PH",
    "el_GR",
    "id",
    "km",
    "lo_LA",
    "ms_MY",
    "ne",
    "nl_be",
    "si",
)


class Faker:  # noqa
    """已经存在的语种和不存在的语种假数据引擎类
    设计各个语言假数据引擎为单例模式
    
    """
    singleton_map = {}
    
    def __new__(cls, locale=None):
        if locale in cls.singleton_map:
            return cls.singleton_map.get(locale)
        
        if locale in LANG_CODES:
            klass = _Faker(providers=[f"multifaker.providers.lorem.{locale}",
                                      f"multifaker.providers.passport.{locale}"])
            klass.locale = locale
            cls.singleton_map[locale] = klass
            return klass
        
        if locale in ("HKG", "tw", "MO"):
            klass = _Faker(locale="zh_CN")
            klass.locale = locale
            return klass
        return _Faker(locale=locale)
