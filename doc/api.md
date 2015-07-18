**Changed 2014/06/22: Longer named parameters and deprecated PIN**

### How to read:
- JSON is inlined between { }.
- <> denotes substitution.
- [] denotes optionality.
- Everything else is taken literally.

Assume all requests are POSTed to /api.

### Anonymous APIs:
```
lookup (3): {
    "action": 3,
    "name": <name>
}
```
Where <name> is a name[@domain.com] ID. If the domain part is omittted, the
server decides where to look up.

```
reverse lookup (5): {
    "action": 5,
    "id": <name>
}
```
Where ID is a Tox ID's public key. If the key exists and the account associated with it is not marked private a name will be returned.

### "Authenticated" APIs:

"Authenticated" API payloads have the following format.
```
{
    "action": <action id>,
    "public_key": <the public key of the private key used to encrypt "e">,
    "encrypted": <action-dependent payload, encrypted with crypto_box: see below (base64)>,
    "nonce": <a 24-byte nonce (base64)>
}
```
The following payloads are JSON strings encrypted with crypto_box, then encoded
to base64.

push (1):
```
{
    "tox_id": <full Tox ID (hex, 72 chars)>
    "name": <name>
    "privacy": <looseness level; if it's > 1 it appears in /friends>
    "bio": <a bio string (cf https://toxme.se/friends/0, the bio appears in the speech bubbles)>
    "timestamp": <the current UTC time as unix timestamp>
}
```

delete (2):
```
{
    "public_key": <public key (64 chars hex)>
    "timestamp": <the current UTC time as unix timestamp>
}
```

### Return values:

Returns take the form
```
{
    "c": <error code>
}
```

Possible codes:
```
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
#name not found
ERROR_UNKNOWN_NAME = {"c": -30}
#sent invalid data in place of an ID
ERROR_INVALID_ID = {"c": -31}
# Lookup failed because of an error on the other domain's side.
ERROR_LOOKUP_FAILED = {"c": -41}
# Lookup failed because that user doesn't exist on the domain
ERROR_NO_USER = {"c": -42}
# Lookup failed because of an error on our side.
ERROR_LOOKUP_INTERNAL = {"c": -43}
# Client is publishing IDs too fast
ERROR_RATE_LIMIT = {"c": -4}
```

For push(1), a password is issued for editing the record without having
the private key.

```
{
    "c": 0,
    "password": <any string>
}
```

For lookup, information is included about the ID:
```
{
    "version": "Tox V2 (local; requires PIN)",
    "source": 1,
    "public_key": "56A1ADE4B65B86BCD51CC73E2CD4E542179F47959FE3E0E21B4B0ACDADE51855",
    "c": 0,
    "url": "tox://groupbot@toxme.se",
    "name": "groupbot",
    "regdomain": "toxme.se",
    "verify": {
        "status": 1,
        "detail": "Good (signed by local authority)"
    }
}
```
