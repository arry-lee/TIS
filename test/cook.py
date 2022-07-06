from awesometable import AwesomeTable


class TextTable(AwesomeTable):
    def __init__(self, field_names=None, **kwargs):
        super().__init__(field_names, kwargs=kwargs)

        # self._horizontal_char = "墙"
        # self._vertical_char = "墙"
        # self._junction_char = "墙"
        # self._top_junction_char = "墙"
        # self._bottom_junction_char = "墙"
        # self._right_junction_char = "墙"
        # self._left_junction_char = "墙"
        # self._top_right_junction_char = "角"
        # self._top_left_junction_char = "角"
        # self._bottom_right_junction_char = "角"
        # self._bottom_left_junction_char = "角"


a = TextTable()

a.add_row(["我"])

print(a)
