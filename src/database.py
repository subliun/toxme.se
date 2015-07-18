"""
* database.py
* Author: stal, stqism; April 2014
* Copyright (c) 2014 Zodiac Labs.
* Further licensing information: see LICENSE.
"""
import sqlalchemy
import sqlalchemy.exc
from sqlalchemy import Integer, DateTime, Unicode, Column, String, Binary
from sqlalchemy.ext.declarative import declarative_base
from string import printable
import re
import threading
import math
import hashlib

"""
Module summary: manages the database of users.
"""

NON_SPECIAL = set(printable) - {":", ";", "(", ")"}
BASE = declarative_base()
DJB_SPECIAL = re.compile(r"([;=:])")
PRESENCE_CACHE_CEILING = 1000
OCT_ENCODE = lambda c: "\\" + "{0:o}".format(ord(c.group(0))).zfill(3)

class User(BASE):
    __tablename__ = "records"
    user_id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    bio = Column(Unicode)
    public_key = Column(String, unique=True) # 64
    checksum = Column(String) # 4
    privacy = Column(Integer)
    timestamp = Column(DateTime)
    sig = Column(String)
    pin = Column(String)
    password = Column(Binary, nullable=False)

    def is_searchable(self):
        """Whether searching will find this user."""
        return self.privacy > 0

    def tox_id(self):
        return "".join((self.public_key, self.pin, self.checksum))

    def record(self, escaped=1):
        """Return a record for this user, escaping weird bytes in
           octal format.
           If our PIN is available, we return a tox1 record."""
        rec = "v=tox1;id={0}{1}{2};sign={3}".format(self.public_key,
                                                    self.pin, self.checksum,
                                                    self.sig)
        if escaped:
            return DJB_SPECIAL.sub(OCT_ENCODE, rec)
        else:
            return rec

    def fqdn(self, suffix):
        """Return the FQDN for this User.
           User("stal").fqdn("id.kirara.ca") -> "stal._tox.id.kirara.ca."
           User("stal").fqdn("id.kirara.ca.") -> "stal._tox.id.kirara.ca."
        """
        o = []
        rep = lambda char: ("\\" + "{0:o}".format(char).zfill(3)
                            if chr(char) not in NON_SPECIAL else chr(char))
        for ch in self.name.encode("utf8"):
            o.append(rep(ch))
        return "._tox.".join(("".join(o), "".join((suffix, "."))
                             if not suffix.endswith(".") else suffix))

    def is_password_matching(self, checkpass):
        salt, correct_digest = self.password[:16], self.password[16:]
        hash_ = hashlib.sha512(salt)
        hash_.update(checkpass.encode("utf8"))
        if hash_.digest() == correct_digest:
            return 1
        else:
            return 0

class StaleUser(object):
    def __init__(self, u):
        self.user_id = u.user_id
        self.name = u.name
        self.bio = u.bio
        self.public_key = u.public_key
        self.checksum = u.checksum
        self.privacy = u.privacy
        self.timestamp = u.timestamp
        self.sig = u.sig
        self.pin = u.pin
        self.password = u.password

    def is_searchable(self):
        return User.is_searchable(self)

    def tox_id(self):
        return User.tox_id(self)

    def record(self, escaped=1):
        return User.record(self, escaped)

    def fqdn(self, suffix):
        return User.fqdn(self, suffix)

    def is_password_matching(self, checkpass):
        return User.is_password_matching(self, checkpass)

class Database(object):
    def __init__(self, backing="sqlite:///:memory:", should_echo=1):
        self.presence_cache = {}
        self.backing = backing
        self.should_echo = should_echo
        self.lock = threading.RLock()
        self.cached_first_page = None
        self.cached_page_count = None
        self.cached_user_count = None

    def late_init(self):
        self.requests_serviced = 0
        self.dbc = sqlalchemy.create_engine(self.backing, echo=self.should_echo)
        BASE.metadata.create_all(self.dbc)
        self.gs = sqlalchemy.orm.sessionmaker(bind=self.dbc)

    def _cache_entity_ins(self, name, prefetch):
        if len(self.presence_cache) > PRESENCE_CACHE_CEILING:
            self.presence_cache.popitem()
        u = StaleUser(prefetch)
        self.presence_cache[name] = u
        return u

    def _cache_entity_sel(self, name):
        sess = self.gs()
        ex = sess.query(User).filter_by(name=name).first()
        if len(self.presence_cache) > PRESENCE_CACHE_CEILING:
            self.presence_cache.popitem()
        u = StaleUser(ex) if ex else None
        self.presence_cache[name] = u
        sess.close()
        return u

    def _cache_entity_rem(self, name, prefetch):
        self.presence_cache[name] = -1
        return prefetch

    def get(self, name):
        self.requests_serviced += 1
        e = self.presence_cache.get(name, -1)
        return e if e != -1 else self._cache_entity_sel(name)

    def get_page(self, num, length):
        if num != 0 or self.cached_first_page is None:
            sess, records = self.get_page_ig(num, length)
            sess.close()
            return records
        else:
            return self.cached_first_page

    def count_users(self):
        return (self.cached_user_count if self.cached_user_count is not None
                                       else self.count_users_ig())

    def count_pages(self, length):
        return (self.cached_page_count if self.cached_page_count is not None
                                       else self.count_pages_ig(length))

    def contains(self, name):
        e = self.presence_cache.get(name, -1)
        return 1 if e != -1 else bool(self._cache_entity_sel(name))

    def update_atomic(self, object_, s=None):
        s = s or self.gs()
        s.add(object_)
        try:
            s.commit()
            self._cache_entity_ins(object_.name, object_)
        except sqlalchemy.exc.IntegrityError as e:
            print(e)
            return 0
        finally:
            s.close()
        self.cached_first_page = None
        self.cached_page_count = None
        self.cached_user_count = None
        return 1

    def get_ig(self, name, sess=None):
        sess = sess or self.gs()
        ex = sess.query(User).filter_by(name=name).first()
        return sess, ex

    def get_by_id_ig(self, id, sess=None):
        sess = sess or self.gs()
        ex = sess.query(User).filter_by(public_key=id).first()
        return sess, ex

    def get_by_id(self, id, sess=None):
        sess = sess or self.gs()
        id = id.upper()
        pkey = id[0:64]

        ex = sess.query(User).filter_by(public_key=pkey).first()
        u = StaleUser(ex) if ex else None
        sess.close()
        print (u.privacy)
        return u

    def get_page_ig(self, num, length, sess=None):
        sess = sess or self.gs()
        ex = (sess.query(User).filter(User.privacy > 0).order_by(User.timestamp.desc())
                              .limit(length).offset(num * length))
        make_stale = lambda n: (self.presence_cache.get(n.name, 0)
                                or self._cache_entity_ins(n.name, n))
        if num == 0:
            self.cached_first_page = [make_stale(x) for x in ex]
            return sess, self.cached_first_page
        else:
            return sess, [make_stale(x) for x in ex]

    def count_pages_ig(self, length):
        sess = self.gs()
        count = sess.query(User).count()
        self.cached_page_count = math.ceil(float(count) / length)
        return self.cached_page_count

    def count_users_ig(self):
        sess = self.gs()
        self.cached_user_count = sess.query(User).count()
        return self.cached_user_count

    def iterate_all_users(self, mutates=0):
        sess = self.gs()
        results = sess.query(User)
        for obj in results:
            yield obj
        if mutates:
            sess.commit()
        sess.close()

    def delete_pk(self, pk):
        sess = self.gs()
        sess.query(User).filter_by(public_key=pk).delete()
        sess.commit()
        sess.close()
        self.cached_first_page = None
        self.cached_page_count = None
        self.cached_user_count = None
