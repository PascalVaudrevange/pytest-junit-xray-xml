class MoreThanOneItemError(Exception):
    pass


class MoreThanOneTestSummaryError(MoreThanOneItemError):
    pass


class MoreThanOneTestKeyError(MoreThanOneItemError):
    pass


class MoreThanOneTestIdError(MoreThanOneItemError):
    pass
