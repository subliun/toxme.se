import time
import queue
import threading
import json
import logging
import dns.resolver
import dns.exception

import nacl.signing
import nacl.exceptions
import nacl.encoding

import error_codes

"""
* dns_discovery.py - A Tox DNS Discovery client/library.
*
* Run interactively: ./dns_discovery.py name@domain.moe
* Or as a library:
*     core = DNSCore(<number of threads>)
*     core.callback_dispatcher = <function that calls callbacks>
*     core.dispatch_lookup(<address>, <callback>)
*
* This file is released into the public domain.
"""

"""
Module summary: handles DNS lookups for the web API (search field).
This is an optional module.
"""

SIGNSTATUS_GOOD      = 1
SIGNSTATUS_BAD       = 2
SIGNSTATUS_UNDECIDED = 3

SOURCE_LOCAL  = 1
SOURCE_REMOTE = 2

# a very long time
QUITE_A_WHILE_FROM_NOW = 90000000000
DISALLOWED_CHARS = set(" @/")

# helpers

REC_TRANSFORMERS = {
    "tox1": lambda r: {
        "public_key": r["id"],
        "check": r["id"][-4:],
        "version": "Tox V1",
    },
    "tox2": lambda r: {
        "public_key": r["pub"],
        "check": r["check"],
        "version": "Tox V2 (PIN required)",
    },
}

# split a 'key=value;key=value' type string into python dict
def _parse_rec(rec):
    return {k: v for k, v in
            (pair.split("=", 1) for pair in rec.split(";") if pair)}

def _lookup_key_in_bag(domain):
    try:
        with open("keybag.json", "r") as keybag_f:
            keybag_contents = json.load(keybag_f)
    except IOError:
        return None
    
    if domain not in keybag_contents:
        return None
    else:
        k = nacl.signing.VerifyKey(keybag_contents[domain]["pubkey"],
                                   nacl.encoding.HexEncoder)
        return (k, int(time.time()) + QUITE_A_WHILE_FROM_NOW, SOURCE_LOCAL)

def _lookup_key_over_dns(domain):
    try:
        ans = dns.resolver.query("_tox.{0}".format(domain), "TXT")
    except dns.exception.DNSException:
        return None
    for txt in ans:
        try:
            values = _parse_rec("".join(txt.strings))
        except ValueError:
            continue
        if values.get("v") != "tox" or values.get("pub") is None:
            continue

        try:
            k = nacl.signing.VerifyKey(values.get("pub"),
                                       nacl.encoding.HexEncoder)
            return (k, int(time.time()) + ans.ttl, SOURCE_REMOTE)
        except (TypeError, nacl.exceptions.CryptoError):
            return None

# Look to the local keybag (if it exists) then DNS.
def _lookup_key(domain):
    return _lookup_key_in_bag(domain) or _lookup_key_over_dns(domain)

class DNSCore(object):
    def __init__(self, workers_num):
        self.lookup_cache = {}
        self.key_cache = {}
        self.callback_dispatcher = lambda callback, result: callback(result)
        
        self.logger = logging.getLogger("DNSCore")
        self.dispatch_queue = queue.Queue()
        self.workers = []
        for n in range(workers_num):
            thread = threading.Thread(target=self._run_worker, kwargs={
                "dqueue": self.dispatch_queue,
            })
            thread.daemon = True
            thread.start()
            self.workers.append(thread)

    def _cached_key(self, domain):
        if domain in self.key_cache and self.key_cache[domain][1] > time.time():
            return self.key_cache[domain][0], self.key_cache[domain][2]
        key = _lookup_key(domain)
        if key:
            self.key_cache[domain] = key
        return key[0], key[2]

    def _check_signature(self, name, check_text, sig, domain):
        key, source = self._cached_key(domain)
        if not key:
            return {
                "status": SIGNSTATUS_UNDECIDED,
                "detail": "? (no authority key found for {0})".format(domain)
            }
        try:
            namebytes = name.encode("utf8")
            dec = key.verify(sig, encoder=nacl.encoding.Base64Encoder)
            if dec != namebytes + nacl.encoding.HexEncoder.decode(check_text):
                raise nacl.exceptions.BadSignatureError("wrong content")
        except Exception:
            self.logger.info("couldn't verify signature...", exc_info=1)
            return {
                "status": SIGNSTATUS_BAD,
                "detail": "Bad (validation failed)",
            }
        else:
            if source == SOURCE_LOCAL:
                detail = "Good (have {0}'s key in local keybag)"
            else:
                detail = "Good (signed by publisher {0})"
            return {
                "status": SIGNSTATUS_GOOD,
                "detail": detail.format(domain),
            }

    def _build_response(self, user, domain, record_data):
        address = "@".join((user, domain))
        response = {
            "c": 0,
            "name": user,
            "regdomain": domain,
            "url": "".join(("tox://", address)),
            "source": SOURCE_REMOTE
        }
        
        version = record_data["v"]
        try:
            response.update(REC_TRANSFORMERS[version](record_data))
        except KeyError:
            return error_codes.ERROR_LOOKUP_FAILED
        
        if "sign" in record_data:
            if record_data["v"] == "tox1":
                check_text = response["public_key"]
            else:
                check_text = "".join((response["public_key"][:64],
                                      response["check"]))
            response["verify"] = (self._check_signature(user, check_text,
                                  record_data["sign"], domain))
        else:
            response["verify"] = {
                "status": SIGNSTATUS_UNDECIDED,
                "detail": "? (record doesn't have a signature)",
            }
        return response

    def _resolve_name(self, usr, domain):
        try:
            ans = dns.resolver.query("{0}._tox.{1}.".format(usr, domain), "TXT")
        except dns.resolver.NXDOMAIN:
            return error_codes.ERROR_NO_USER
        except dns.exception.DNSException:
            return error_codes.ERROR_LOOKUP_FAILED

        for opaque in ans:
            try:
                values = _parse_rec("".join(opaque.strings))
            except ValueError:
                continue

            v = values.get("v", None)
            if v not in {"tox1", "tox2"}:
                continue

            response = self._build_response(usr, domain, values)
            if response["c"] is 0:
                address = "@".join((usr, domain))
                self.lookup_cache[address] = (response, int(time.time())
                                                        + ans.ttl)
                return response
        else:
            return error_codes.ERROR_NO_USER

    def _run_worker(self, dqueue):
        """Generic worker function."""
        while 1:
            name, address, callback = dqueue.get()
            try:
                result = self._resolve_name(name, address)
            except Exception:
                self.logger.error("Exception was caught by worker thread!",
                                  exc_info=1)
                result = None
            finally:
                if callback:
                    self.callback_dispatcher(callback, result)

    def dispatch_lookup(self, addr, callback):
        addr = addr.lower()
        name, regdomain = addr.rsplit("@", 1)
        if not set(name).isdisjoint(DISALLOWED_CHARS):
            callback(error_codes.ERROR_BAD_PAYLOAD)
            return

        now = time.time()
        if addr in self.lookup_cache and self.lookup_cache[addr][1] > now:
            callback(self.lookup_cache[addr][0])
            return
        
        if self.workers:
            self.dispatch_queue.put((name, regdomain, callback))
        else:
            callback(self._resolve_name(name, regdomain))

        #if regdomain == self.home:
        #    rec = self.local_store.get(name.lower())
        #    if not rec:
        #        return cb(ERROR_NO_USER)
        #    if not rec.is_searchable():
        #        return cb(ERROR_NO_USER)
        #    base_ret = {
        #        "c": 0,
        #        "name": rec.name,
        #        "regdomain": regdomain.lower(),
        #        "public_key": rec.public_key,
        #        "url": "tox://{0}@{1}".format(rec.name, regdomain),
        #        "verify": {
        #            "status": SIGNSTATUS_GOOD,
        #            "detail": "Good (signed by local authority)",
        #        },
        #        "source": SOURCE_LOCAL
        #    }
        #    if rec.is_public():
        #        base_ret["version"] = "Tox V1 (local; public)"
        #        base_ret["public_key"] = (rec.public_key + rec.nospam
        #                                  + rec.checksum())
        #    else:
        #        base_ret["version"] = "Tox V2 (local; requires PIN)"
        #    return cb(base_ret)

def _print_answer(result):
    print("\033[1mDiscovery ID\033[0m:",
          result["name"] + "@" + result["regdomain"])
    print("\033[1mPublic key\033[0m:  ", result["public_key"])
    print("\033[1mChecksum\033[0m:    ", result["check"])

    if result["verify"]["status"] == 1:
        sig = "\033[32m{0}\033[0m".format(result["verify"]["detail"])
    elif result["verify"]["status"] == 2:
        sig = "\033[31m{0}\033[0m".format(result["verify"]["detail"])
    else:
        sig = result["verify"]["detail"]
    print("\033[1mSignature\033[0m:   ", sig)

def main():
    import sys
    address = sys.argv[1]
    core = DNSCore(0)
    core.dispatch_lookup(address, _print_answer)

if __name__ == "__main__":
    main()
    