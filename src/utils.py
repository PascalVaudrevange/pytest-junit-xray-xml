def find_items_from_user_properties(user_properties: list[tuple],
                                    name: str) -> list:
    result = [
        item_
        for name_, item_ in user_properties
        if name_ == name
    ]
    return result
