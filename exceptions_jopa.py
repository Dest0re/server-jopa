class ArgumentError(Exception):
    pass


class MemberNotFound(Exception):
    def __init__(self, *args: int):
        super().__init__(*args)
