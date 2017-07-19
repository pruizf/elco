"""Utilities for app"""

import argparse
from copy import deepcopy
import gzip
from lxml import etree
import logging
import os
import pickle
import string
import random
import re


class Utils(object):
    """
    General tools for app
    @warning: L{lcbool}  method is deprecated. Use json.loads() instead.
    """

    def __init__(self, cfg):
        self.cfg = cfg

    ## SETUP ##

    def run_argparse(self):
        """Run the argparse-based cli parser for options or defaults"""
        parser = argparse.ArgumentParser(
                     description="App to work with Entity Linking",
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-c', '--corpus', dest='corpus_name',
                            help='String representing the name of the corpus. '
                                 '(Used to name output files etc.). '
                                 'A default can be set in config.py ',
                            default=self.cfg.cpsname)
        parser.add_argument('-i', '--input',
                            help='Input file, directory or text. '
                                 'A default can be set in config.py ',
                            dest='myinput', default=self.cfg.myinput)
        parser.add_argument('-o', '--output', dest='myout',
                            help='Output file or files. Default names are created '
                                 'dynamically by code in writers.py module')
        parser.add_argument('-r', '--resp_output', dest='myoutresps',
                            help='Output directory for client responses. '
                                 'A default is created dynamically by code in '
                                 'writers.py module')
        parser.add_argument('-s', '--skip_list', dest='myskiplist',
                            default=self.cfg.files2skip,
                            help='File with filenames to skip')
        return parser.parse_args()

    def setup(self, outdir=None, outresps=None):
        """Create directories needed to run app"""
        dirs2create = [self.cfg.datadir, self.cfg.logdir,
                       self.cfg.outdir, self.cfg.resdir]
        if outdir is not None:
            dirs2create.append(outdir)
        if outresps is not None:
            dirs2create.append(outresps)
        for dn in dirs2create:
            if not os.path.exists(dn):
                print "Creating dir {}".format(dn)
                os.makedirs(dn)

    def read_runid(self):
        """Read the id that will identify each run in output files"""
        if not os.path.exists(self.cfg.runidf):
            return self.cfg.runidnbr
        else:
            with open(self.cfg.runidf, "r") as inf:
                return int(inf.read().strip())

    def increase_runid(self, ri):
        """Increase the id that identifies a run in output files"""
        ri = int(ri) + 1
        return ri

    def write_runid(self, ri):
        """Write a run id to the file for it in config"""
        with open(self.cfg.runidf, "w") as outf:
            outf.write(string.zfill(ri, 3))

    @staticmethod
    def random_id(size):
        #https://stackoverflow.com/questions/2257441/
        return ''.join(random.SystemRandom().choice(
            string.ascii_letters + string.digits)
            for _ in range(size))

    def cleanup(self, ri, maintain_id=False):
        """
        Tidies up after a run
        @param maintain_id: if true, run-id won't be increased
        """
        if not maintain_id:
            self.write_runid(self.increase_runid(ri))
        else:
            self.write_runid(ri)

    @staticmethod
    def load_zipped_pickle(fn):
        """
        Loads a compressed pickle from disk
        http://code.activestate.com/recipes/189972-zip-and-pickle/
        """
        fo = gzip.GzipFile(fn, 'rb')
        object = pickle.load(fo)
        fo.close()
        return object

    @staticmethod
    def save_zipped_pickle(ob, fn, protocol=-1):
        """
        Save an pickle to a compressed disk file.
        http://code.activestate.com/recipes/189972-zip-and-pickle/
        """
        fo = gzip.GzipFile(fn, 'wb')
        pickle.dump(ob, fo, protocol)
        fo.close()

    ## FORMATTING ##

    @staticmethod
    def norm_mention(mtn):
        """
        Sanitize mention, e.g.:
         - Some annotators tag across whitespace. Remove spaces
         - Spotlight gives INF as inf
        """
        if repr(mtn) == 'inf':
            mtn = u'inf'
        mtn = re.sub("\n+", " ", mtn)
        mtn = re.sub("\s{2,}", " ", mtn)
        return mtn

    def norm_label(self, lbl, svc=None):
        """To display all labels in same format"""
        lbl = re.sub(" ", "_", lbl)
        # remote AIDA needs different normalization
        #TODO: integrate all the replacements in data/json_escapes.txt
        if svc == self.cfg.TNames.RA:
            lbl = lbl.replace("\u0028", "(")
            lbl = lbl.replace("\u0029", ")")
        return lbl

    @staticmethod
    def norm_text(txt):
        """Apply to text before client request"""
        return txt.strip()

    @staticmethod
    def lcbool(bo):
        """
        Return Python True False as lc string
        @deprecated: use json.loads(True) instead
        """
        assert isinstance(bo, bool)
        return str(bo).lower()

    ### ANALYSIS ###

    @staticmethod
    def add_sentence_number_to_annots(andi, dob):
        """
        Add sentence number so each annot in annot dict.
        @param andi: annotation dictionary, hashed by position
        @param dob: L{model.Document} object
        """
        for posi in andi:
            andi[posi].snbr = \
                andi[posi].find_sentence_number(dob.stposis)
        return andi

    def load_entity_category_indicators(self):
        """
        Load list of entity-category indicators to analyze
        entity category lists with, and determine entity-type.
        Also can creates lemmatized variant for each indicator
        @return: Dict with the following keys:
          - "PER", "ORG", and each of those has in turn "indi", "anti", "gene"
        """
        print "Loading category indicators"
        indi = {"PER": {}, "ORG": {}, "LOC": {}}
        pertree = etree.parse(self.cfg.perind)
        orgtree = etree.parse(self.cfg.orgind)
        loctree = etree.parse(self.cfg.locind)
        indi["PER"]["indi"] = [x.lower()
                               for x in pertree.xpath("//indicator[@active='1']/text()")]
        indi["PER"]["gene"] = [x.lower()
                               for x in pertree.xpath("//generic[@active='1']/text()")]
        indi["PER"]["anti"] = [x.lower()
                               for x in pertree.xpath("//anti[@active='1']/text()")]
        indi["ORG"]["indi"] = [x.lower()
                               for x in orgtree.xpath("//indicator[@active='1']/text()")]
        indi["ORG"]["anti"] = []
        indi["ORG"]["gene"] = [x.lower()
                               for x in orgtree.xpath("//generic[@active='1']/text()")]
        indi["LOC"]["indi"] = [x.lower()
                               for x in loctree.xpath("//indicator[@active='1']/text()")]
        indi["LOC"]["gene"] = []
        indi["LOC"]["anti"] = []
        return indi

    ## OVERLAPPING MENTIONS BY SAME LINKER ##

    @staticmethod
    def overlaps(r1, r2):
        """
        Return true if range r1 overlaps with range r2
        @param r1: range 1
        @type r1: tuple
        @param r2: range 1
        @type r2: tuple
        """
        p1 = r1[0] #start 1
        e1 = r1[1] #end 1
        p2 = r2[0] #start 2
        e2 = r2[1] #end 2
        try:
            assert (p1 < e1) and (p2 < e2)
        except AssertionError:
            print "! ", r1, r2
            return None
        return (((p1 == p2) and (e1 == e2))
                or ((p1 == p2) and (e1 < e2))
                or ((p1 == p2) and (e2 < e1))
                or ((e1 == e2) and (p1 < p2))
                or ((e1 == e2) and (p2 < p1))
                or ((p1 < p2) and (p2 < e1))
                or ((p2 < p1) and (p1 < e2)))

    @staticmethod
    def pick_overlapping_mention(we1, we2, la1, la2):
        """
        @param we1: weight1
        @param we2: weight2
        @param la1: length of label 1
        @param la2: length of label 2
        """
        if we1 > we2:
            return 1
        elif we2 > we1:
            return 2
        elif len(la1) > len(la2):
            return 1
        return 2

    @classmethod
    def deduplicate_mentions(cls, mdico):
        """
        Given a dico with mention position tuples, choose among overlapping mentions.
        @param mdico: dico with mention-position tuples
        @return: deduplicated mentions dico
        """
        dones = {} # done comparisons
        _mdico4modif = deepcopy(mdico) #can't iterate while modifying iterable right?
        for spot1 in mdico:
            for spot2 in mdico:
                if spot1 == spot2:
                    continue
                # in dhned version, had added docSco in same hash
                if spot1 == "docSco" or spot2 == "docSco":
                    continue
                dones.setdefault(spot1, [])
                dones.setdefault(spot2, [])
                if spot2 in dones[spot1]:
                    continue
                if cls.overlaps(spot1, spot2):
                    chosen = cls.pick_overlapping_mention(mdico[spot1]["weight"],
                                                            mdico[spot2]["weight"],
                                                            mdico[spot1]["label"],
                                                            mdico[spot2]["label"])
                    if chosen == 1:
                        try:
                            _mdico4modif.pop(spot2) # this prints to console
                        except KeyError:
                            print "!! Pb Wikiminer Client OVERLAP RES:\n  {}\n  {}".format(
                                mdico[spot1], mdico[spot2])
                        dones[spot1].append(spot2)
                        dones[spot2].append(spot1)
                    elif chosen == 2:
                        try:
                            _mdico4modif.pop(spot1) # this prints to console
                        except KeyError:
                            print "!! Pb Wikiminer Client OVERLAP RES:\n  {}\n  {}".format(
                                mdico[spot1], mdico[spot2])
                        dones[spot1].append(spot2)
                        dones[spot2].append(spot1)
        return _mdico4modif

    ## LOGGING ##

    @staticmethod
    def specify_log(mylgr, myfn, mylevel):
        """
        Provide infos for logger object to be created properly
        @param mylgr: a logger object
        @param myfn: filename to write to
        @param mylevel: a logging level
        """
        mylgr.setLevel(mylevel)
        lfh = logging.FileHandler(myfn)
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        frmt = logging.Formatter(formatstr)
        lfh.setFormatter(frmt)
        mylgr.propagate = False
        mylgr.addHandler(lfh)

    def log_rover(self, link, service, old, linkrover, algr):
        """Log ROVER computation infos"""
        myweights = self.cfg.Weights.vals[self.cfg.mywscheme][self.cfg.myevmode]
        algr.debug("    {0} + ( {1} - ( {2} + {3} ) ) * {4} = {5}".format(old,
                                                    len(self.cfg.ranks),
                                                    self.cfg.ranks[service],
                                                    self.cfg.rank_spacer,
                                                    myweights[service],
                                                    linkrover))

if __name__ == "__main__":
    import config as cfg
    myutils = Utils(cfg)
    myutils.setup()
