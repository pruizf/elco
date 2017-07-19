"""Reads inputs for EL"""

import codecs
import os

import utils as ut


class DefReader(object):
    """Default input reader"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.txtcache = {}

    def read(self, ipt):
        """
        Returns an id and the text for every element in ipt.
        Creates a random id if just given a text
        """
        if os.path.isfile(ipt):
            if self.cfg.DBG:
                print "- Reading {}".format(ipt)
            with codecs.open(ipt, "r", "utf8") as ih:
                return {ih.name: ih.read()}
        elif os.path.isdir(ipt):
            fn2txt = {}
            print "-- READING DIR: {}".format(ipt)
            for fn in os.listdir(ipt):
                if self.cfg.DBG:
                    print "- Reading {} ".format(fn)
                with codecs.open(os.path.join(ipt, fn), "r", "utf8") as ih:
                    fn2txt[os.path.basename(ih.name)] = ih.read()
            #TODO should be generator
            return fn2txt
        elif isinstance(ipt, str):
            try:
                return {self.txtcache[ipt]: ipt}
            except KeyError:
                key = ut.Utils.random_id(self.cfg.random_id_length)
                self.txtcache[ipt] = key
                return {key: ipt}

