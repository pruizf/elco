"""Writes EL responses"""

import codecs
import json
import os
import re
import string

import model as md


class DefWriter(object):
    """Default annotation writer"""

    HEADERS = {
        "single": ["doc", "mtn", "start", "end", "label", "service", "conf",
                   "sentence"],
        "multi": ["doc", "mtn", "start", "end", "label", "service", "conf",
                  "sentence"]
    }

    def __init__(self, cfg):
        self.cfg = cfg

    def write_raw_responses(self, di, clname, runid="001",
                            outdir=None):
        for ke in sorted(di):
            if outdir is None:
                outdir = self.cfg.resdir
            outfn = os.path.join(outdir,
                os.path.basename(os.path.splitext(ke)[0]) + \
                "_" + clname + "_" + string.zfill(runid, 3) + ".txt")
            print "  - Writing raw response: {}".format(
                os.path.realpath(outfn))
            with codecs.open(outfn, "w", "utf8") as out:
                if (isinstance(di[ke], dict) or
                    isinstance(di[ke], list)):
                    out.write(json.dumps(di[ke]))
                elif isinstance(di[ke], str):
                    out.write(di[ke].decode("utf8"))


class Dict2TsvWriter(DefWriter):
    """
    Takes dictionary of annotation-dict hashed by fn and position,
    writes TSV.
    """

    def __init__(self, cfg):
        super(Dict2TsvWriter, self).__init__(cfg)

    @staticmethod
    def _parse_annotation_hash(di, clname, cps, mode="single", fn=None):
        """
        Parse annotations in a way that can be written out
        by other methods in the class.
        @param di: hash of annotations
        @param clname: name of the client (spotlight etc.)
        @param cps: the corpus object whose results to write
        @param mode: 'single' means single output file for all corpus,
        'multi' means individual output files per input file.
        @return: List of tsv strings representing annotations
        @rtype: list
        """
        assert mode in ("single", "multi")
        # files with no annotations
        if not di:
            if mode == "single":
                outlists = [fn]
            else:
                outlists = []
        else:
            outlists = []
        # files with
        for po in sorted(di):
            if isinstance(di[po], dict):
                outlist = [di[po]["fmention"],
                           str(di[po]["start"]), str(di[po]["end"]),
                           di[po]["link"], clname,
                           str(di[po]["confidence"])]
                try:
                    if di[po]["snbr"]:
                        outlist.append(str(di[po]["snbr"]))
                except KeyError:
                    print "! No snbr: {}".format(repr(di[po]))
                try:
                    if cps.entities[di[po]["link"]].categs["normcat"]:
                        outlist.append(
                            cps.entities[di[po]["link"]].categs["normcat"])
                except KeyError:
                    print "! No normcat: {}".format(repr(di[po]["link"]))
            elif isinstance(di[po], md.Annotation):
                outlist = [di[po].fmention,
                           str(di[po].start), str(di[po].end),
                           di[po].link, clname,
                           str(di[po].confidence)]
            else:
                outlist = []
                print "! type error with var containing annotations"
            if mode == "single":
                outlist = [fn] + outlist
            outlists.append("\t".join(outlist))
        return outlists

    def write_to_multi(self, di, clname, cps, runid="001", has_categ=False,
                       outdir=None):
        """
        Write annotations from a hash to multiple output files
        (one file per key in hash, keys are filenames).
        @param di: hash with annotations by fn and position
        @param clname: name of the client (babelfy, etc.)
        @param runid: id for the run
        """
        for ke in di:
            if outdir is None:
                outdir = self.cfg.outdir
            outfn = os.path.join(outdir,
                    os.path.basename(os.path.splitext(ke)[0]) + \
                    "_" + clname + "_" + string.zfill(runid, 3) + ".txt")
            print "  - Writing annotations: {}".format(
                os.path.realpath(outfn))
            with codecs.open(outfn, "w", "utf8") as out:
                outlists = ["\t".join(DefWriter.HEADERS["multi"])]
                if has_categ:
                    outlists[0] += "\tcateg"
                outlists.extend(self._parse_annotation_hash(di[ke], clname,
                                                            cps, mode="multi"))
                out.write("\n".join(outlists))

    def write_to_single(self, di, clname, cps, runid="001", has_categ=False,
                        write_header=False, outdir=None):
        """
        Write annotations from a hash to a single output file
        for the hash.
        @param di: hash with annotations by fn and position
        @param clname: name of the client (babelfy, etc.)
        @param cps: the corpus object whose results to write
        @param runid: id for the run
        """
        if outdir is None:
            outdir = self.cfg.outdir
        outfn = os.path.join(outdir,
                cps.name + "_" + clname + "_all_" +
                string.zfill(runid, 3) + ".txt")
        with codecs.open(outfn, "a", "utf8") as out:
            if write_header:
                myheader = "\t".join(DefWriter.HEADERS["single"])
                if has_categ:
                    myheader += "\tcateg"
                out.write("".join((myheader, "\n")))
            for ke in sorted(di):
                print "  - Appends annotations: {}".format(
                    os.path.realpath(outfn))
                outlists = self._parse_annotation_hash(di[ke], clname, cps,
                                                       mode="single", fn=ke)
                try:
                    out.write("".join(("\n".join(outlists), "\n")))
                except UnicodeDecodeError:
                    out.write("".join("\n".join(
                        [re.sub("\xef\xbb\xbf", "", item) for item in outlists])))


class Obj2TsvWriter(Dict2TsvWriter):
    """
    Takes dictionary of L{model.Annotation} hashed by fn and position,
    writes TSV.
    """

    def __init__(self, cfg):
        super(Obj2TsvWriter, self).__init__(cfg)

    @staticmethod
    def _parse_annotation_hash(di, clname, cps, mode="single", fn=None):
        """
        Parse annotations in a way that can be written out
        by other methods in the class.
        @param di: hash of L{model.Annotation}
        @param clname: name of the client (spotlight etc.)
        @param cps: the corpus object whose results to write
        @param mode: 'single' means single output file for all corpus,
        'multi' means individual output files per input file.
        @return: List of tsv strings representing annotations
        @rtype: list
        """
        assert mode in ("single", "multi")
        # files with no annotations
        if not di:
            if mode == "single":
                outlists = [fn]
            else:
                outlists = []
        else:
            outlists = []
        # files with
        for po in sorted(di):
            # fmention to write out
            if isinstance(di[po], dict):
                outlist = [di[po].fmention,
                           str(di[po].start), str(di[po].end),
                           di[po].link, clname,
                           str(di[po].confidence)]
                try:
                    if di[po].snbr:
                        outlist.append(str(di[po].snbr))
                except NameError:
                    print "! No snbr: {}".format(repr(di[po]))
                try:
                    outlist.append(cps.entities[di[po]].normcat)
                except KeyError:
                    print "! No normcat: {}".format(repr(di[po].link))
            elif isinstance(di[po], md.Annotation):
                outlist = [di[po].fmention,
                           str(di[po].mention.start), str(di[po].mention.end),
                           di[po].enti.link, clname,
                           str(di[po].confidence)]
                try:
                    if di[po].snbr:
                        outlist.append(str(di[po].snbr))
                except NameError:
                    print "! No snbr: {}".format(repr(di[po]))
                try:
                    outlist.append(cps.entities[di[po].enti.link].normcat)
                except KeyError:
                    print "! No normcat: {}".format(repr(di[po].enti.link))
            else:
                outlist = []
                print "! type error with var containing annotations"
            if mode == "single":
                outlist = [fn] + outlist
            try:
                outlists.append("\t".join(outlist))
            except UnicodeDecodeError:
                outlists.append("\t".join(
                    [re.sub("\xef\xbb\xbf", "", item) for item in outlist]))
        return outlists
