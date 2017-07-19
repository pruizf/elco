"""Types of data we'll need"""

import inspect
import os
import sys

from nltk import sent_tokenize

here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)

import config as cfg
import utils


class Corpus(object):
    """
    Sees a corpus as a collection of L{Entity} and L{Mention}
    #TODO: collection of documents?
    @ivar cf: a config (module or dict)
    @ivar name: corpus name (default from config)
    @ivar entities: L{Entity} dict hashed by label (L{Entity.link})
    @ivar mentions: L{Mention} dict hashed by mention-key (L{Mention.men_id})
    """

    def __init__(self, cf, name=None):
        self.cf = cf
        self.name = name
        self.categ_cache = {}
        if self.name is None:
            self.name = self.cf.cpsname
        self.mentions = {}
        self.entities = {}

    def add_entity_to_corpus(self, link, svc, annot=None, redo_ents=False):
        """
        If entity not added to L{Corpus.entities}, add it
        and add categories for it as well
        @param link: entity label
        @param svc: svc having produced the annotation on the basis of which
        this entity is being treated.
        @param annot: the annotation we're treating
        @note: annot can be None if no need to use its categs
        """
        if link not in self.entities:
            eo = Entity(link)
            if self.cf.add_categs:
                try:
                    if annot is not None:
                        eo.categs.update(eo.parse_categs(link, annot, svc))
                except NotImplementedError:
                    pass
            self.entities[link] = eo
        else:
            if redo_ents:
                self.entities[link].categs.update(
                    Entity.parse_categs(link, annot, svc))
        if svc not in self.entities[link].services:
            self.entities[link].services.append(svc)

    def add_mention_to_corpus(self, key, surface):
        """
        Adds a L{Mention} to L{Corpus.mentions} if the mention-key
        is not found there.
        @param key: a key to hash the mention with
        @param surface: string representing the mention
        @note: the key is created elsewhere and L{Mention} attributes
        must be reconstructed from the key
        """
        bits = key.split(u"###")
        docid, start, end = bits[0], int(bits[1]), int(bits[2])
        if key not in self.mentions:
            mt = Mention(key, surface, start, end)
            self.mentions[key] = mt

    def normalize_entity_categories(self, link, indic):
        """
        Produce a single category based on the entity's categories.
        Set this category to the entity's "normcat" field
        @param link: label for the entity to work with
        @param indic: hash with info re normalized categ for WP categ labels
        @note: Category codes are *NOE* (no info), *COD* (concept by default),
        *PER* (Person), *ORG* (Organization), *LOC* (Location),
        *TCO* (DBpedia TopicalConcpet), *COG* (a generic concept, like "Country",
        rather than an instance of a country)
        """
        # no categ info
        try:
            if not self.entities[link].categs:
                self.entities[link].normcat = "NOE"
        except KeyError:
            return
        if self.entities[link].normcat in (None, "COD"):
            # spotlight info
            try:
                if "Person" in self.entities[link].categs["dbpediao"]:
                    self.entities[link].normcat = "PER"
                    return
                elif "Organisation" in self.entities[link].categs["dbpediao"]:
                    self.entities[link].normcat = "ORG"
                    return
                elif "Place" in self.entities[link].categs["dbpediao"]:
                    self.entities[link].normcat = "LOC"
                    return
                elif "TopicalConcept" in self.entities[link].categs["dbpediao"]:
                    self.entities[link].normcat = "TCO"
                    return
            except KeyError:
                pass
            # wikipedia categs info (TagME, WMiner etc.)
            # all the indicators are lowercase
            try:
                if (link.lower() in indic["PER"]["gene"]
                    or link.lower() in indic["ORG"]["gene"]
                    or link.lower() in indic["LOC"]["gene"]):
                    self.entities[link].normcat = "COG"
                    return
                for pi in indic["PER"]["indi"]:
                    for cat in self.entities[link].categs["wiki"]:
                        if pi in cat.lower():
                            hasanti = [i for i in indic["PER"]["anti"]
                                       if i in cat.lower()]
                            if len(hasanti) == 0:
                                self.entities[link].normcat = "PER"
                                return
                for oi in indic["ORG"]["indi"]:
                    for cat in self.entities[link].categs["wiki"]:
                        if oi in cat.lower():
                            hasanti = [i for i in indic["ORG"]["anti"]
                                       if i in cat.lower()]
                            if len(hasanti) == 0:
                                self.entities[link].normcat = "ORG"
                                return
                for li in indic["LOC"]["indi"]:
                    for cat in self.entities[link].categs["wiki"]:
                        if li in cat.lower():
                            hasanti = [i for i in indic["LOC"]["anti"]
                                       if i in cat.lower()]
                            if len(hasanti) == 0:
                                self.entities[link].normcat = "LOC"
                                return
            except KeyError:
                pass
            # default
            self.entities[link].normcat = "COD"
            return


class Token(object):
    """
    A string of characters.
    @ivar surface: the string
    @ivar start: initial character position
    @ivar end: final character position
    """

    def __init__(self, surface, start, end):
        self.surface = surface
        self.start = int(start)
        self.end = int(end)

    def __unicode__(self):
        return u"{0}\t{1}\t{2}".format(self.surface,
                                       self.start, self.end)

    def __str__(self):
        return unicode(self).encode("utf8")


class Mention(Token):
    """
    String of characters picked by an EL service to assign an entity to it.
    @ivar men_id: unique id for the mention.
    """

    def __init__(self, men_id, surface, start, end):
        super(Mention, self).__init__(surface, start, end)
        self.men_id = men_id

    def __unicode__(self):
        return u"{0}\t{1}\t{2}\t{3}".format(self.surface,
                                            self.start, self.end,
                                            self.men_id)


class Entity(object):
    """
    An entity from a knowledge-base (Wikipedia, DBpedia ...)
    @ivar link: entity label
    @ivar services: list of services having output it
    @ivar categs: dict of categories
    @ivar normcat: normalized category ("ORG", "LOC" etc)
    @note: needs access to a config module or dict
    """

    def __init__(self, link, categ_cache=None):
        self.link = link
        self.services = []
        self.categs = {}
        self.normcat = None

    @staticmethod
    def _retrieve_categ_from_cache(link, categ_cache=None):
        """To have possibility of passing a hash with categories by entity"""
        if categ_cache is None:
            categ_cache = {}
        if link in categ_cache:
            return categ_cache[link]
        else:
            return False

    @staticmethod
    def parse_categs(link, resp, service=None, categ_cache=None):
        """Add categories to an entity, parsing the annotation
        format for the service having annotated it"""
        done = Entity._retrieve_categ_from_cache(link, categ_cache)
        if not done:
            if service == cfg.TNames.TM:
                return Entity._parse_tagme_categs(resp)
            elif service == cfg.TNames.SP:
                return Entity._parse_spotlight_categs(resp)
            elif service == cfg.TNames.PS:
                return Entity._parse_spotstat_categs(resp)
            elif service == cfg.TNames.WD:
                return Entity._parse_wminer_categs(resp)
            elif service == cfg.TNames.AI:
                return Entity._parse_aida_categs(resp)
            elif service == cfg.TNames.RA:
                return Entity._parse_raida_categs(resp)
            elif service == cfg.TNames.BF:
                return Entity._parse_babelfy_categs(resp)

    @staticmethod
    def _parse_tagme_categs(ann):
        return {"wiki": [c.replace(" ", "_") for c in
                              ann["dbpedia_categories"]]}

    @staticmethod
    def _parse_spotlight_categs(ann):
        return {"dbpediao": [c.replace("DBpedia:", "") for c in
                ann["types"].split(",") if c.startswith("DBpedia")]}

    @staticmethod
    def _parse_spotstat_categs(ann):
        return {"dbpediao": [c.replace("DBpedia:", "") for c in
                ann["@types"].split(",") if c.startswith("DBpedia")]}

    @staticmethod
    def _parse_wminer_categs(resp):
        raise NotImplementedError

    @staticmethod
    def _parse_aida_categs(resp):
        raise NotImplementedError

    @staticmethod
    def _parse_raida_categs(resp):
        raise NotImplementedError

    @staticmethod
    def _parse_babelfy_categs(resp):
        raise NotImplementedError

    def __unicode__(self):
        outl = [self.link]
        try:
            outl.append(u"WIKI::{}".format(u"~".join(self.categs["wiki"])))
        except KeyError:
            outl.append(u"WIKI::")
        try:
            dbpe = u"~".join(self.categs["dbpediao"])
            if dbpe:
                outl.append(u"DBPE::{}".format(dbpe))
            else:
                outl.append(u"DBPE::")
        except (KeyError, NameError):
            outl.append(u"DBPE::")
        try:
            outl.append(u"NCAT::{}".format(self.categs["normcat"]))
        except KeyError:
            outl.append(u"NCAT::")
        if self.services:
            outl.append(u"~".join(self.services))
        return u"||".join(outl)

    def __str__(self):
        return unicode(self).encode("utf8")


class Annotation(object):
    """
    Relates a L{Mention} to an L{Entity}
    @type mention: L{Mention}
    @type enti: L{Entity}
    """

    def __init__(self, mention, enti):
        self.mention = mention
        self.enti = enti
        self.confidence = None
        self.mmconfidence = -1  # minmax scaled
        self.normconfidence = -1
        self.service = None
        # ent_voters is a list of services that voted for self.enti
        # when using L{combination.Combiner.Group.select_linkgroup}
        self.ent_voters = []
        # likewise mtn_voters: list of services that voted for the mention
        # in the selected annotation
        self.mtn_voters = []

    def find_sentence_number(self, sentposis):
        """
        Given a hash {(start, end): sentnbr}, return sentnbr for a
        mention-position tuple
        @param sentposis: hash for the sentence positions
        """
        for posi in sentposis:
            if self.mention.start >= posi[0] and self.mention.end <= posi[1]:
                return sentposis[posi]

    def __unicode__(self, verbose=True):
        if self.confidence is None:
            confstr = ""
        else:
            confstr = str(round(float(self.confidence), 3))
        if verbose:
            return u"{0}\t({1}, {2})\t{3}\t{4}\t{5}\t{6}\t{7}".format(
                self.mention.surface,
                self.mention.start, self.mention.end,
                self.enti.link, confstr, str(round(float(self.mmconfidence), 3)),
                str(round(float(self.normconfidence), 3)), self.service)
        else:
            return u"{0}\t({1}, {2})\t{3}\t{4}\t{5}".format(
                self.mention.surface,
                self.mention.start, self.mention.end,
                self.enti.link, confstr, self.service)

    def __str__(self):
        return unicode(self).encode("utf8")


class Document(object):
    """
    Represents and analyzes documents.
    """

    def __init__(self, docid, *args, **kwargs):
        self.docid = docid
        self.entities = kwargs.get('entities', None)
        self.text = kwargs.get('text', None)
        # normalized text
        self.ftext = kwargs.get('ftext', None)
        if self.ftext is None:
            self.ftext = utils.Utils.norm_text(self.text)
        self.stposis = self.find_sentence_positions()
        # the rest are unused for now (come from previous version)
        self.dname = kwargs.get('dname', None)
        self.page = kwargs.get('page', None)
        self.date = kwargs.get('date', None)
        self.dtype = kwargs.get('dtype', None)
        self.turnid = kwargs.get('turnid', None)
        self.turnnbr = kwargs.get('turnnbr', None)
        self.speaker = kwargs.get('speaker', None)
        self.wikiminer_doc_score = float(kwargs.get('wikiminer_doc_score', 0.0))

    def find_sentence_positions(self, txt=None):
        """
        Given normalized text for a document, sentence-split it
        and return hash of sentence numbers by position.
        """
        posi2nbr = {}
        if txt is None:
            txt = self.ftext
        sts = sent_tokenize(txt)
        nbr = 1
        end = 0
        for st in sts:
            start = self.ftext[end:].find(st) + end
            end = start + len(st)
            posi2nbr[(start, end)] = nbr
            nbr += 1
        return posi2nbr

# Tests
if __name__ == "__main__":
    import readers as rd
    sys.path.append("/home/pablo/projects/ned/elclients")
    myrdr = rd.DefReader(cfg)
    ds = myrdr.read("/home/pablo/projects/bentham/tests_voyant_tools/voyant_out")
    done = 0
    todo = 2
    dob2sents = {}
    for fn in ds:
        print "- {}".format(fn)
        # normalized text is created upon instantiation
        dob = Document(fn, text=ds[fn])
        dob2sents = dob.find_sentence_positions()
        done += 1
        if done == todo:
            break
