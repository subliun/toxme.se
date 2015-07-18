import dnslib.server
import dnslib
import time
import binascii

import struct

NAME_LIMIT_HARD = 63

ch_A = ord("A")
ch_Z = ord("Z")
ch_a = ord("a")
ch_z = ord("z")
ch_ZERO = ord("0")
ch_FIVE = ord("5")

ir1 = lambda c: c <= ch_Z and c >= ch_A
ir2 = lambda c: c <= ch_z and c >= ch_a
ir3 = lambda c: c <= ch_FIVE and c >= ch_ZERO
BASE32_SRC = b"abcdefghijklmnopqrstuvwxyz012345"

# q: why not use python's base64 module?
# a: <+irungentoo> notsecure, I told you we should have used standard base32
#    <notsecure> Jfreegman, irungentoo wanted to use a-z,2-7 for base32,
#                I chose a-z,0-5
#    <notsecure> he said it would fuck with people using standard base32
#                functions
def notsecure32_decode(src):
    ret = []
    bits = 0
    op = 0
    for char in (ord(s) for s in src):
        if ir1(char):
            char -= ch_A
        elif ir2(char):
            char -= ch_a
        elif ir3(char):
            char = (char - ch_ZERO + 26)
        else:
            raise ValueError("this is an error apparently")

        op = (op | (char << bits)) % 256;
        bits += 5;

        if bits >= 8:
            bits -= 8
            ret.append(op)
            op = (char >> (5 - bits)) % 256;

    return bytes(ret)

# TODO optimize
def notsecure32_encode(src):
    sl = len(src)
    ret = []
    bits = 0
    i = 0
    while(i < sl):
        c1 = src[i]
        try:
            c2 = src[i + 1]
        except IndexError:
            c2 = 0
        a = BASE32_SRC[((c1 >> bits) | (c2 << (8 - bits))) & 0x1F]
        ret.append(a)
        bits += 5
        if bits >= 8:
            bits -= 8
            i += 1
    return bytes(ret)

class ToxResolver(dnslib.server.BaseResolver):
    def __init__(self, cryptocore, store, cfg):
        self.cryptocore = cryptocore
        self.store = store
        self.ttl = cfg["dns_record_ttl"]
        self.ireg = cfg["registration_domain"]
        self.home_addresses = cfg.get("home_addresses")
        self.home_addresses_6 = cfg.get("home_addresses_6")
        
        if not self.ireg.endswith("."):
            self.ireg = "".join((self.ireg, "."))
            
        self.authority_list = cfg["dns_authority_names"]
            
        self.soa_rd = dnslib.SOA(self.authority_list[0],
                                 cfg["dns_hostmaster"].replace("@", "."))
        self.soa = dnslib.RR("_tox.{0}".format(self.ireg), 6, ttl=86400,
                             rdata=self.soa_rd)

    def update_soa(self):
        self.soa_rd.times = (int(time.strftime("%Y%m%d99")), 3600, 600, 86400,
                             self.ttl)

    def resolve(self, request, handler):
        question = request.get_q()
        req_name = str(question.get_qname())
        # TXT = 16
        reply = request.reply()
        suffix = "._tox.{0}".format(self.ireg)

        if question.qtype != 16 and not req_name.endswith(self.ireg):
            reply.header.rcode = dnslib.RCODE.NXDOMAIN
            return reply

        if question.qtype == 16:
            if req_name == suffix[1:]:
                reply.add_answer(dnslib.RR(req_name, 16, ttl=0,
                    rdata=dnslib.TXT(self.cryptocore.public_key.encode("ascii"))))
                return reply
            if not req_name.endswith(suffix):
                reply.header.rcode = dnslib.RCODE.NXDOMAIN
                return reply
            user_name = req_name[:req_name.rfind(suffix)]
            if len(user_name) > NAME_LIMIT_HARD and user_name[0] == "_":
                encrypted = user_name.replace(".", "")[1:]
                try:
                    b = notsecure32_decode(encrypted)
                    nonce = b[:4] + (b"\0" * 20)
                    ck = b[4:36]
                    payload = b[36:]
                    name = self.cryptocore.dsrep_decode_name(ck, nonce, payload)
                except Exception:
                    print("error >_<")
                    reply.header.rcode = dnslib.RCODE.NXDOMAIN
                    return reply

                rec = self.store.get(name.decode("utf8"))
                if not rec:
                    reply.header.rcode = dnslib.RCODE.NXDOMAIN
                    return reply
                base = b"v=tox3;id="
                if rec.pin:
                    r_payload = "{0}{1}{2}".format(rec.public_key, rec.pin,
                                                   rec.checksum)
                else:
                    r_payload = "{0}00000000{1}".format(rec.public_key,
                                                        rec.checksum)
                msg = binascii.unhexlify(r_payload)
                nonce_reply = b[:4] + b"\x01" + (b"\0" * 19)
                ct = self.cryptocore.dsrec_encrypt_key(ck, nonce_reply, msg)

                key_part = notsecure32_encode(ct)
                reply.add_answer(dnslib.RR(req_name, 16, ttl=0,
                                 rdata=dnslib.TXT(b"".join((base, key_part)))))
                return reply
            else:
                rec = self.store.get(user_name)
                if not rec:
                    reply.header.rcode = dnslib.RCODE.NXDOMAIN
                    return reply
                else:
                    reply.add_answer(dnslib.RR(req_name, 16, ttl=0,
                                               rdata=dnslib.TXT(rec.record(0)
                                                            .encode("utf8"))))
                    return reply
        elif question.qtype == 6:
            self.update_soa()
            reply.add_answer(self.soa)
            return reply
        elif question.qtype == 2:
            for name in self.authority_list:
                reply.add_answer(dnslib.RR(req_name, 2, ttl=86400,
                                           rdata=dnslib.NS(name.encode("utf8"))
                                           ))
            return reply
        elif question.qtype == 1 and self.home_addresses:
            for ip in self.home_addresses:
                reply.add_answer(dnslib.RR(req_name, 1, ttl=3600,
                                           rdata=dnslib.A(ip)))
        elif question.qtype == 28 and self.home_addresses_6:
            for ip in self.home_addresses_6:
                reply.add_answer(dnslib.RR(req_name, 28, ttl=3600,
                                           rdata=dnslib.AAAA(ip)))
        else:
            reply.header.rcode = dnslib.RCODE.NXDOMAIN
            return reply
        return reply

# TODO tornado ioloop integration
def server(cryptocore, store, cfg):
    return dnslib.server.DNSServer(ToxResolver(cryptocore, store, cfg),
                                   port=53, address=cfg["dns_listen_addr"],
                                   logger=None,
                                   tcp=False)
