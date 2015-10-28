
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
Where `<name>` is a name[@domain.com] ID. If the domain part is omittted, the
server decides where to look up.

```
reverse lookup (5): {
    "action": 5,
    "id": <id>
}
```
Where ID is a Tox ID's public key. If the key exists and the account associated with it is not marked private a name will be returned.

```
search (6): {
    "action": 6
    "name": <query name>
    "page": <page number>
}
```
Where "name" is the partial name that will be searched for and "page" is the offset (page * ENTRIES_PER_SEARCH) for the returned list.
Note: This query returns a list of users, not IDs. If you have a full toxme name and want to lookup the ID, use lookup(3).

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
    "bio": <a bio string (cf https://toxme.io/friends/0, the bio appears in the speech bubbles)>
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

# Bad payload (possibly not encrypted with the correct key)
ERROR_BAD_PAYLOAD = {"c": -3}

# Name is taken.
ERROR_NAME_TAKEN = {"c": -25}

# The public key given is bound to a name already.
ERROR_DUPE_ID = {"c": -26}

# Invalid char or type was used in a request.
ERROR_INVALID_CHAR = {"c": -27}

# Invalid name was sent
ERROR_INVALID_NAME = {"c": -29}

# Name not found
ERROR_UNKNOWN_NAME = {"c": -30}

# Sent invalid data in place of an ID
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

For lookup(3), information is included about the ID:
```
{
    "version": "Tox V3 (local)",
    "source": 1,
    "tox_id": "56A1ADE4B65B86BCD51CC73E2CD4E542179F47959FE3E0E21B4B0ACDADE51855D34D34D37CB5",
    "c": 0,
    "url": "tox:groupbot@toxme.io",
    "name": "groupbot",
    "regdomain": "toxme.io",
    "verify": {
        "status": 1,
        "detail": "Good (signed by local authority)"
    }
}
```

For search(4), an array of users that matched the query name is returned. Each user dict contains their full 
toxme name and bio. The array will always be of length ENTRIES_PER_SEARCH (30) or shorter. If no matching names are 
found the users array is empty.
```
{
    "c": 0,
    "users": [{
        "name": <name>
        "bio": <bio>
    }]
}
