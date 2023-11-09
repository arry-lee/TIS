from faker import Faker

from multifaker.providers.lorem import Provider as LoremProvider

faker_engine = Faker("zh_CN")


class Provider(LoremProvider):
    """Implement lorem provider for ``si`` locale."""

    def words(self, nb=3, ext_word_list=None, unique=False):
        return faker_engine.words(nb, ext_word_list, unique)
