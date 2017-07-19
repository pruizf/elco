"""Creates entity cooccurrence tables"""

import codecs
import inspect
import itertools
import json
from lxml import etree
import os
import string
import sys
import time
import urllib

here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)

import config as cfg
import clients
import model as md
import utils


myutils = utils.Utils(cfg)


class CorpusMgr(object):
    """Methods to manage corpus elements"""

    def __init__(self):
        pass

    @staticmethod
    def create_mention_key(fn, start, end):
        """Create a key for the L{model.Corpus} mention-hash"""
        return u"{}###{}###{}".format(os.path.splitext(fn)[0], start, end)


class AnnotationParser(object):
    """
    Methods to parse the annotations returned by L{clients}
    into L{model.Annotation}
    """

    def __init__(self):
        pass

    @staticmethod
    def parse(fn, cl, resp, cpsob, text=None):
        """
        Parse the annotations into L{model.Annotation} using the method
        required by the client which produced them (from L{clients}).
        @param fn: filename (used for mention-ids)
        @param cl: the client that produced the annotation
        @param resp: the response returned by the client
        @type resp: tool-specific (see methods below), but often json
        @param cpsob: a L{model.Corpus} object
        @param text: the text that was sent to the client. Only needed for
        L{parse_babelfy}
        @return: Hash with position tuples as keys, and L{model.Annotation}
        objs as values
        @rtype: dict
        @note: redo_ents in the parse_{cl.name} methods means:
          - If False, don't add any info to an entity that
            is already in L{model.Corpus.entities}.
          - If True, add info (e.g. categories from a new linker)
            to an entity that is already in L{model.Corpus.entities}
        For now only Spotlight is adding categories on top of TagMe's
        """
        if cl.name == cfg.TNames.TM:
            return AnnotationParser.parse_tagme(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.SP:
            return AnnotationParser.parse_spotlight(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.PS:
            return AnnotationParser.parse_spotstat(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.WD:
            return AnnotationParser.parse_wminer(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.WI:
            return AnnotationParser.parse_wminer_remote(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.AI:
            return AnnotationParser.parse_aida(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.RA:
            return AnnotationParser.parse_raida(
                fn, cl, resp, cpsob, redo_ents=cfg.redo_ents[cl.name])
        elif cl.name == cfg.TNames.BF:
            return AnnotationParser.parse_babelfy(fn, cl, resp, cpsob,
                text=text, redo_ents=cfg.redo_ents[cl.name])

    @staticmethod
    def parse_tagme(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        """
        if not resp:
            return {}
        anresp ={}
        for an in resp["annotations"]:
            if (cfg.use_confidence and float(an["rho"]) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            try:
                link = myutils.norm_label(an["title"])
                cpsob.add_entity_to_corpus(link, cl.name, an,
                                           redo_ents=redo_ents)
            except KeyError:
                continue
            surface = an["spot"]
            start, end = an["start"], an["end"]
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)

            cpsob.add_mention_to_corpus(mtnkey, surface)
            anresp[(start, end)] = \
                md.Annotation(cpsob.mentions[mtnkey],
                              cpsob.entities[link])
            anresp[(start, end)].fmention = \
                utils.Utils.norm_mention(surface)
            anresp[(start, end)].confidence = float(an["rho"])
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def parse_spotlight(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        @note: response as returned by pyspotlight
        """
        if not resp:
            return {}
        anresp = {}
        for an in resp:
            if (cfg.use_confidence and float(an["similarityScore"]) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            try:
                start = an["offset"]
                end = an["offset"] + len(unicode(an["surfaceForm"]))
                surface = an["surfaceForm"]
            except KeyError:
                print "!! KeyError for annot: {}".format(repr(an))
                continue
            try:
                # unquote takes and gives str, act accordingly
                # http://stackoverflow.com/questions/5139249
                link = urllib.unquote((an["URI"].replace(
                    cl.cfg.DBPRESPREF, u"")).encode("utf8")).decode("utf8")
                cpsob.add_entity_to_corpus(link, cl.name, an,
                                           redo_ents=redo_ents)
            except KeyError:
                continue
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)
            cpsob.add_mention_to_corpus(mtnkey, surface)
            anresp[(start, end)] = md.Annotation(cpsob.mentions[mtnkey],
                cpsob.entities[link])
            anresp[(start, end)].fmention = \
                utils.Utils.norm_mention(surface)
            anresp[(start, end)].confidence = float(an["similarityScore"])
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def parse_spotstat(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        """
        if not resp:
            return {}
        anresp = {}
        jso = resp.json()
        # annotations are in 'Resources' element of the response
        if "Resources" not in jso:
            return {}
        for an in jso["Resources"]:
            if (cfg.use_confidence and float(an["@similarityScore"]) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            try:
                start = an["@offset"]
                end = int(an["@offset"]) + len(unicode(an["@surfaceForm"]))
                surface = an["@surfaceForm"]
            except KeyError:
                print "!! KeyError for annot: {}".format(repr(an))
                continue
            try:
                # unquote takes and gives str, act accordingly
                # http://stackoverflow.com/questions/5139249
                link = urllib.unquote((an["@URI"].replace(
                    cl.cfg.DBPRESPREF, u"")).encode("utf8")).decode("utf8")
                cpsob.add_entity_to_corpus(link, cl.name, an,
                                           redo_ents=redo_ents)
            except KeyError:
                continue
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)
            cpsob.add_mention_to_corpus(mtnkey, surface)
            anresp[(start, end)] = md.Annotation(cpsob.mentions[mtnkey],
                cpsob.entities[link])
            anresp[(start, end)].fmention = \
                utils.Utils.norm_mention(surface)
            anresp[(start, end)].confidence = float(an["@similarityScore"])
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def parse_wminer(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        """
        if not resp:
            return {}
        anresp = {}
        jso = resp.json()
        for topic in jso['spots']:
            if (cfg.use_confidence and float(topic['score']) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            start = int(topic['start'])
            end = int(topic['end'])
            link = myutils.norm_label(topic['wikiname'])
            surface = topic['mention']
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)
            cpsob.add_entity_to_corpus(link, cl.name, topic,
                redo_ents=redo_ents)
            cpsob.add_mention_to_corpus(mtnkey, surface)

            anresp[(start, end)] = md.Annotation(
                cpsob.mentions[mtnkey], cpsob.entities[link])
            anresp[(start, end)].fmention = \
                utils.Utils.norm_mention(surface)
            anresp[(start, end)].confidence = float(topic['score'])
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def parse_wminer_remote(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        @deprecated
        @note: use L{parse_wminer} instead
        """
        if not resp:
            return {}
        posi2topic = {}
        # clean up response
        try:
            tree = etree.fromstring(resp)
        except etree.XMLSyntaxError:
            return {}
        srctext = tree.xpath("//request/param[@name='source']")[0].text
        #TODO: Run deduplication here? (or at least give option?)
        for topic in tree.xpath("//detectedTopic"):
            if (cfg.use_confidence and float(topic.attrib["weight"]) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            for ref in topic.xpath("references//reference"):
                start = int(ref.attrib["start"])
                end = int(ref.attrib["end"])
                link = myutils.norm_label(topic.attrib["title"])
                surface = srctext[start:end]
                mtnkey = CorpusMgr.create_mention_key(fn, start, end)

                cpsob.add_entity_to_corpus(link, cl.name, ref,
                    redo_ents=redo_ents)
                cpsob.add_mention_to_corpus(mtnkey, surface)

                posi2topic[(start, end)] = md.Annotation(
                    cpsob.mentions[mtnkey], cpsob.entities[link])
                posi2topic[(start, end)].fmention = \
                    utils.Utils.norm_mention(surface)
                posi2topic[(start, end)].confidence = float(topic.attrib["weight"])
                posi2topic[(start, end)].service = cl.name
        return posi2topic

    @staticmethod
    def parse_aida(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        @type resp: json
        """
        if not resp:
            return {}
        anresp = {}
        entlist = resp["allEntities"]
        for ent in entlist:
            if (cfg.use_confidence and
                float(resp[u"entityMetadata"][ent]["importance"]) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            # res["mentions"] contains all info i store but confidence
            annot = [ann for ann in resp["mentions"] if "bestEntity"
                     in ann and ann["bestEntity"]["kbIdentifier"] == ent][0]
            start, end = int(annot["offset"]), int(annot["offset"] + annot["length"])
            surface = annot["name"]
            # confidence is in res["entityMetadata"] indexed by entity name
            confidence = float(resp[u"entityMetadata"][ent]["importance"])
            link = myutils.norm_label(
                resp[u"entityMetadata"][ent]["readableRepr"])
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)
            cpsob.add_entity_to_corpus(link, cl.name, ent,
                redo_ents=redo_ents)
            cpsob.add_mention_to_corpus(mtnkey, surface)
            anresp[(start, end)] = md.Annotation(
                cpsob.mentions[mtnkey],
                cpsob.entities[link])
            anresp[(start, end)].fmention = utils.Utils.norm_mention(surface)
            anresp[(start, end)].confidence = confidence
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def parse_raida(fn, cl, resp, cpsob, redo_ents):
        """
        See L{parse}
        @type resp: json
        """
        if not resp:
            return {}
        anresp = {}
        #resp = json.loads(resp)
        entlist = resp["allEntities"]
        for ent in resp["mentions"]:
            if "bestEntity" in ent:
                link = myutils.norm_label(
                    ent["bestEntity"]["kbIdentifier"].replace(
                        cfg.AIDA_KBPREFIX, ""), svc=cl.name)
                confidence = float(ent["bestEntity"]["disambiguationScore"])
                if (cfg.use_confidence and confidence <
                    cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                    continue
            else:
                continue
            start = int(ent["offset"])
            end = int(ent["offset"]) + int(ent["length"])
            surface = ent["name"]
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)

            cpsob.add_entity_to_corpus(link, cl.name, ent,
                redo_ents=redo_ents)
            cpsob.add_mention_to_corpus(mtnkey, surface)
            anresp[(start, end)] = md.Annotation(
                cpsob.mentions[mtnkey],
                cpsob.entities[link])
            anresp[(start, end)].fmention = \
                utils.Utils.norm_mention(surface)
            anresp[(start, end)].confidence = confidence
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def parse_babelfy(fn, cl, resp, cpsob, text, redo_ents):
        """
        See L{parse}
        @note: only accepts annotations that have a DBpedia page
        """
        if not resp:
            return {}
        data = json.loads(resp)
        anresp = {}
        for res in data:
            if (cfg.use_confidence and float(res["score"]) <
                cfg.MinConfs.vals[cfg.mywscheme][cl.name][cfg.myevmode]):
                continue
            dbp_url = res["DBpediaURL"]
            if dbp_url in (None, ""):
                continue
            start = res["charFragment"]["start"]
            end = res["charFragment"]["end"] + 1
            link = dbp_url.replace(cfg.DBPRESPREF, "")
            mention = text[start:end]
            confidence = res["score"]
            mtnkey = CorpusMgr.create_mention_key(fn, start, end)

            cpsob.add_entity_to_corpus(link, cl.name, res,
                redo_ents=redo_ents)
            cpsob.add_mention_to_corpus(mtnkey, mention)

            anresp[(start, end)] = md.Annotation(
                cpsob.mentions[mtnkey],
                cpsob.entities[link])
            anresp[(start, end)].fmention = \
                utils.Utils.norm_mention(mention)
            anresp[(start, end)].confidence = confidence
            anresp[(start, end)].service = cl.name
        return anresp

    @staticmethod
    def choose_annotation_with_longest_mention(anns):
        """Choose among overlapping annotations based on mention length"""
        if not anns:
            return {}
        chosen = {}
        sanns = sorted(anns)
        dones = []
        for idx, posi in enumerate(sanns):
            if posi in dones:
                continue
            iidx = idx
            cands = [posi]
            while (iidx + 1 <= len(sanns) - 1 and
                  (utils.Utils.overlaps(sanns[idx], sanns[iidx + 1]) or
                   utils.Utils.overlaps(sanns[iidx], sanns[iidx + 1]))):
                cands.append(sanns[iidx + 1])
                iidx += 1
            if len(cands) > 1:
                posi2keep = sorted(cands, key=lambda po:
                                   len(anns[po].mention.surface),
                                   reverse=True)[0]
                chosen[posi2keep] = anns[posi2keep]
            else:
                chosen[cands[0]] = anns[cands[0]]
            dones.extend(cands)
        return chosen


class CooccurrenceMgr():
    """Takes care of calculating co-occurrence between entities"""

    def __init__(self):
        pass

    @staticmethod
    def filter_entity_dict(cf, di):
        """
        Filter dict of entities according to config
        dict shape is {fn: {(start, end): ...}}
        """
        #TODO: is this tested?? (ent["service"] looks weird)
        filt = {}
        for fn, ents in di.items():
            for po, ent in ents.items():
                if not cf.cooc_annots[ent["service"]]:
                    continue
                elif ent["confidence"] < cf.cooc_minconf[ent["service"]]:
                    continue
                else:
                    try:
                        if (not cf.cooc_categ["ALL"] and
                            ent["etype"] not in cf.cooc_categ):
                            continue
                        else:
                            filt.setdefault(fn, {})
                            filt[fn][po] = ent
                    except KeyError:
                        filt.setdefault(fn, {})
                        filt[fn][po] = ent
        return filt

    @staticmethod
    def filter_entity_objs(cf, di):
        """Filter dict of L{model.Annotation} according to config"""
        #TODO: is this tested?? (ent["service"] looks weird)
        filt = {}
        for fn, ents in di.items():
            for po, ent in ents.items():
                keep = False
                for svc in ent.services:
                    if cf.cooc_annots[svc]:
                        keep = True
                        break
                if not keep:
                    continue
                elif ent.confidence < cf.cooc_minconf[ent["service"]]:
                    continue
                else:
                    try:
                        if (not cf.cooc_categ["ALL"] and
                            ent.normcat not in cf.cooc_categ):
                            continue
                        else:
                            filt.setdefault(fn, {})
                            filt[fn][po] = ent
                    except KeyError:
                        filt.setdefault(fn, {})
                        filt[fn][po] = ent
        return filt

    @staticmethod
    def create_entity_edges_from_annotation_dict(di):
        """
        Create lists of edges per sentence from a dict of annotation-dict
        dict format is {fn: {(start, end): {"key1": val1 ...}, }}
        """
        print "- Start coocs"
        edges = {}
        # mk lists of entities by sentence
        ebysent = {}
        dones = 0
        for fn, annots in di.items():
            # empty annots
            if not annots:
                continue
            try:
                total_sents = max([en["snbr"] for posi, en in annots.items()])
            except KeyError, msg:
                print "KeyError, {}".format(msg)
                continue
            for sn in range(1, total_sents + 1):
                ebysent[tuple([en["link"] for posi, en
                        in annots.items() if en["snbr"] == sn])] = 1
            dones += 1
            if dones % cfg.node_progress == 0:
                print "Done nodes for {} files: {}".format(
                    dones, time.asctime(time.localtime()))
        print "Total sentences: {}".format(len(ebysent))
        print "Total nodes: {}".format(sum([len(k) for k in ebysent]))
        return ebysent

    @staticmethod
    def create_entity_edges_from_annotation_objs(di):
        """
        Create lists of edges per sentence from a dict of L{model.Annotation}
        dict format is {fn: {(start, end): L{model.Annotation}, ... }}
        """
        print "- Start coocs"
        edges = {}
        # mk lists of entities by sentence
        ebysent = {}
        dones = 0
        for fn, annots in di.items():
            # empty annots
            if not annots:
                continue
            try:
                total_sents = max([an.snbr for posi, an in annots.items()])
            except KeyError, msg:
                print "KeyError, {}".format(msg)
                continue
            except AttributeError, msg:
                print "AttributeError, {}".format(msg)
                continue
            for sn in range(1, total_sents + 1):
                ebysent[tuple([an.enti.link for posi, an
                        in annots.items() if an.snbr == sn])] = 1
            dones += 1
            if dones % cfg.node_progress == 0:
                print "Done nodes for {} files: {}".format(
                    dones, time.asctime(time.localtime()))
        print "Total sentences: {}".format(len(ebysent))
        print "Total nodes: {}".format(sum([len(k) for k in ebysent]))
        return ebysent


    @staticmethod
    def count_edges(ebysent, directed=False):
        """
        Count edges in corpus based on lists of edges by sentences
        @param ebysent: hash with lists of edges per sentence as keys
        and a dummy value.
        """
        edges = {}
        done_sents = 0
        for lst in ebysent:
            if not directed:
                pairs = [tuple(sorted((i[0], i[1])))
                         for i in itertools.combinations(lst, 2)
                         if i[0] != i[1]]
            else:
                pairs = [i for i in itertools.combinations(lst, 2)
                         if i[0] != i[1]]
            for pair in pairs:
                edges.setdefault(pair, 0)
                edges[pair] += 1
            done_sents += 1
            if done_sents % cfg.sent_progress == 0:
                print "Done sentences: {}".format(done_sents)
        return edges

    @staticmethod
    def write_edge_dict_as_tsv(ed, outfn=None, printout=cfg.cooc_print,
                               svc="", cps=cfg.cpsname,
                               runid=string.zfill(str(myutils.read_runid()), 3),
                               use_header=cfg.use_cooc_header):
        """Write out the edges as tsv, sorted by decreasing weight"""
        if use_header:
            outl = [cfg.cooc_header]
        else:
            outl = []
        print "- Sorting [{}] edges by weight: {}".format(len(ed),
                                                       time.asctime(time.localtime()))
        print "Done sorting: {}".format(time.asctime(time.localtime()))
        for e in sorted(ed, key=lambda k: ed[k], reverse=True):
            outl.append((e[0], e[1], str(ed[e])))
        if printout:
            for ll in outl:
                print "\t".join(ll)
        else:
            if outfn is None:
                outf = "_".join((cps, svc, runid)) + "_cooc_new.txt"
                outff = os.path.join(cfg.outdir, outf)
            else:
                outff = outfn
            print "Output file: {}".format(outff)
            with codecs.open(outff, "w", "utf8") as out:
                wtn_ll = 0
                for ll in outl:
                    out.write("".join(("\t".join(ll), "\n")))
                    wtn_ll += 1
                    if wtn_ll % cfg.written_progress == 0:
                        print "Written {} lines, {}".format(wtn_ll,
                            time.asctime(time.localtime()))


# TEST
if __name__ == "__main__":
    ar = clients.AnnotationReader(cfg)
    cc = CooccurrenceMgr()
    print "Tests with individual files"
    svc2anns = {}
    svc2edges = {}
    svc2edgecounts = {}
    mycorpus = md.Corpus(cfg)
    if False:
        for svc in [s for s in cfg.activate if cfg.activate[s]["general"]]:
            print svc
            # read_file fine cos contains annots for whole corpus (whole run)
            #annots = ar.read_file(svc, mycorpus, "064", has_snbr=True,
            annots = ar.read_file(svc, mycorpus, "361", has_snbr=True,
                                  has_normcat=False)
            svc2anns[svc] = annots
            svc2edges[svc] = cc.create_entity_edges_from_annotation_objs(
                svc2anns[svc])
            svc2edgecounts[svc] = cc.count_edges(svc2edges[svc])
            cc.write_edge_dict_as_tsv(svc2edgecounts[svc], svc=svc, runid="064")
    if True:
        print "Tests with a large corpus"
        for svc in ["spotlight"]:
            svc2anns = {}
            svc2edges = {}
            print "Reading"
            annots = ar.read_dir(
                #"/home/pablo/projects/el/elclient_other/elclientout_bentham", "spotlight",
                #"/home/pablo/projects/ie/wk/support_examples_for_ui_right_panel/el_out", "spotlight",
                "/home/pablo/projects/ie/wk/ui_wireframe/other/screenshots/support_examples_for_ui_right_panel/el_out_full", "spotlight",
                #mycorpus, "", oneoutforall=False, has_snbr=True, has_normcat=False)  # options i had for Bentham corpus (or for uibo wireframe)
                mycorpus, "", oneoutforall=True, has_snbr=True, has_normcat=True)     # used these options for ENB (as in uibo app DB format)
            print "Done reading"
            edges_per_sentence = cc.create_entity_edges_from_annotation_objs(
                annots)
            counted_edges = cc.count_edges(edges_per_sentence)
            cc.write_edge_dict_as_tsv(counted_edges, svc=svc, runid="TEST4")
