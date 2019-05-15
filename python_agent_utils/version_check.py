def are_version_compatible(ver_a, ver_b):
    """
    Expects a 2 part version like a.b with a and b both integers
    """
    (a_1, a_2) = ver_a.split('.')
    (b_1, b_2) = ver_b.split('.')
    (a_1, a_2) = (int(a_1), int(a_2))
    (b_1, b_2) = (int(b_1), int(b_2))
    if a_1 < b_1:
        return False
    if (b_2 > a_2) and (a_1 != b_1):
        return False
    return True
