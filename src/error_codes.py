"""
* error_codes.py
* Author: stal, stqism; April 2014
* Copyright (c) 2014 Zodiac Labs.
* Further licensing information: see LICENSE.
"""

ERROR_OK = {"c": 0}

# Client didn't POST to /api
ERROR_METHOD_UNSUPPORTED = {"c": -1}

# Client is not using a secure connection
ERROR_NOTSECURE = {"c": -2}

# Bad encrypted payload (not encrypted with our key)
ERROR_BAD_PAYLOAD = {"c": -3}

# Name is taken.
ERROR_NAME_TAKEN = {"c": -25}

# The public key given is bound to a name already.
ERROR_DUPE_ID = {"c": -26}

# No spaces allowed.
ERROR_INVALID_CHAR = {"c": -27}

ERROR_BAD_PASSWORD = {"c": -28}

ERROR_INVALID_NAME = {"c": -29}

# Lookup failed because of an error on the other domain's side.
ERROR_LOOKUP_FAILED = {"c": -41}

# Lookup failed because that user doesn't exist on the domain
ERROR_NO_USER = {"c": -42}

# Lookup failed because of an error on our side.
ERROR_LOOKUP_INTERNAL = {"c": -43}

# Client is publishing IDs too fast
ERROR_RATE_LIMIT = {"c": -4}

#reverse lookup not found
ERROR_UNKNOWN_NAME = {"c": -30}

#sent bullshit in place of an ID
ERROR_INVALID_ID = {"c": -31}

DESCRIPTIONS = {
    -1: "You must send POST requests to /api.",
    -2: "Please try again using a HTTPS connection.",
    -3: "I was unable to read your encrypted payload.",
    -4: "You're making too many requests. Wait an hour and try again.",
    -25: "This name is already in use.",
    -26: "This Tox ID is already registered under another name.",
    -27: "Please don't use a space in your name.",
    -28: "Password incorrect.",
    -29: "You can't use this name.",
    -30: "Name not found",
    -31: "Tox ID not sent",
    -41: "Lookup failed because the other server replied with invalid data.",
    -42: "That user does not exist.",
    -43: "Internal lookup error. Please file a bug.",
}
