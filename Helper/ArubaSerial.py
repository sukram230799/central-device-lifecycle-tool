import re


def validate_sn(serial):
    return re.fullmatch('(C|S)(N|G)[A-Z0-9]+', serial)
