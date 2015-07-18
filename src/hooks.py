"""
* hooks_djb.py
* Author: stal, stqism; April 2014
* Copyright (c) 2014 Zodiac Labs.
* Further licensing information: see LICENSE.
"""
import os
import subprocess
import time
import logging
import threading

LOGGER = None
NEEDS_UPDATE = 0

def thread_run(root, database, ttl, home):
    global NEEDS_UPDATE
    while 1:
        if NEEDS_UPDATE:
            djbdns_write_file(root, database, ttl, home)
            NEEDS_UPDATE = 0
        time.sleep(10)

def init(config, database):
    global LOGGER, did_update_record, did_delete_record, NEEDS_UPDATE
    NEEDS_UPDATE = 1
    LOGGER = logging.getLogger("djb_hooks")
    t = threading.Thread(target=thread_run, args=(config["djbdns_root"],
                         database, config["dns_record_ttl"],
                         config["registration_domain"]))
    t.daemon = True
    t.start()

def did_update_record(nul, rec):
    global NEEDS_UPDATE
    NEEDS_UPDATE = 1

did_delete_record = did_update_record

def djbdns_write_file(root, database, ttl, home):
    data_name = os.path.join(root, "data")
    master = open(data_name, "w")
    header_name = os.path.join(root, "header.yuu")
    with open(header_name, "r") as header:
        h = header.read()
        master.write(h)
        master.write("\n")

    master.write("# This data automatically updated by yuu. Please edit"
                  " header.yuu instead.\n")
    for obj in database.iterate_all_users():
        master.write("'{0}:{1}:{2}\n".format(obj.fqdn(home), obj.record(), ttl))
    master.close()

    prev = os.getcwd()
    os.chdir(root)
    subprocess.check_output(["make"])
    os.chdir(prev)
    LOGGER.info("Update succeeded.")
