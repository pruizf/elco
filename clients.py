"""Entity Linking Clients"""

import codecs
import json
import os
import logging
import re
import requests
import spotlight
import time

import model as md
import analysis


logging.getLogger("requests").setLevel(logging.WARNING)


class EmptyTextException(Exception): pass


class WSClient(object):
    """
    Calls Entity Linking Web Services and returns responses
    @ivar cfg: config module
    """
    def __init__(self, cfg):
        self.cfg = cfg

    def create_payload(self, text=None, opts=None):
        """Creates the client request (abstract)"""
        raise NotImplementedError

    def get_response(self, payload=None):
        """Gets the service response (abstract)"""
        raise NotImplementedError


class TagmeClient(WSClient):
    """
    Client for Tagme WS.
    @ivar cfg: The config to use
    """

    def __init__(self, cfg):
        super(TagmeClient, self).__init__(cfg)
        self.name = self.cfg.TNames.TM
        self.pars = self.cfg.params[self.name]
        self.connparams = {'gcube-token': self.pars["key"],
                           'include_categories': json.dumps(True),
                           'text': None,
                           'lang': self.pars["lang"]}

    def create_payload(self, text, opts=None):
        """Create payload for a requests call, with options and text"""
        payload = {}
        payload.update(self.connparams)
        payload["text"] = text
        return payload

    def get_response(self, payload):
        """
        Call TagMe API and return a JSON response
        @return: Json response
        @rtype: dict
        """
        if payload["text"] == "":
            raise EmptyTextException({"message": "\n! Empty text"})
        try:
            req = requests.post(self.pars["url"], data=payload)
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        resp = req.json()
        return resp


class SpotlightClient(WSClient):
    """Calls DBpedia Spotlight (Lucene backend) using pyspotlight module"""

    def __init__(self, cfg):
        super(SpotlightClient, self).__init__(cfg)
        self.name = self.cfg.TNames.SP
        self.pars = self.cfg.params[self.name]

    def get_response(self, text):
        """@rtype: dict"""
        try:
            annotations = spotlight.annotate(
                self.pars["url"], text,
                confidence=self.pars["minconf"])
        except spotlight.SpotlightException, msg:
            print "SpotlightException: {}".format(msg)
            return {}
        except requests.HTTPError, msg2:
            print "HTTPError: {0}\nTEXT: \"{1}\"".format(
                repr(msg2), repr(text))
            return {}
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        return annotations


class SpotstatClient(WSClient):
    """
    Calls DBpedia Spotlight (statistical backend)
    """

    # Example call
    #curl "http://spotlight.sztaki.hu:2222/rest/annotate"
    # --data-urlencode "text=President Obama called Wednesday on Cogress to extend a tax break"
    # --data "confidence=0.2" --data "support=20" -H "Accept:application/json"

    def __init__(self, cfg):
        super(SpotstatClient, self).__init__(cfg)
        self.name = self.cfg.TNames.PS
        self.headers = {"Accept": 'application/json'}
        self.pars = {"confidence": self.cfg.params[self.name]["minconf"],
                     "url": self.cfg.params[self.name]["url"]}

    def get_response(self, text):
        """@rtype: requests.models.Response"""
        self.pars.update({"text": text})
        try:
            annotations = requests.get(self.pars["url"],
                headers=self.headers,
                params=self.pars)
        except spotlight.SpotlightException, msg:
            print "SpotlightException: {}".format(msg)
            return {}
        except requests.HTTPError, msg:
            print "HTTPError: {0}\nTEXT: \"{1}\"".format(
                repr(msg), repr(text))
            return {}
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        return annotations


class WikipediaMinerClientDexter(WSClient):
    """
    Apply Wikipedia Miner Toolkit via Dexter integration
    Expects Dexter on localhost:8080
    """
    # curl "http://localhost:8080/dexter-webapp/api/rest/annotate?
    # text=this%20is%20a%20test%20about%20Michelle%20Obama
    # &n=50&dsb=tagme&wn=true&debug=false&format=text&min-conf=0.5"
    # &n=50&dsb=tagme&wn=true&debug=false&format=text&min-conf=0.5"
    def __init__(self, cfg):
        super(WikipediaMinerClientDexter, self).__init__(cfg)
        self.name = self.cfg.TNames.WD
        self.pars = self.cfg.params[self.name]
        self.headers = {"Accept": 'application/json'}

    def create_payload(self, text, options=None):
        """
        @param options: dict with options other than the text
        @type options: dict
        """
        if options is None:
            payload = {'text': text, 'n': 10000, 'dsb': 'wikiminer',
                       'wn': json.dumps(True),
                       'min-conf': self.pars["minconf"],
                       'debug': json.dumps(True)}
        else:
            payload = {'text': text}
            payload.update(options)
        return payload

    def get_response(self, payload):
        """
        Return the response object
        @rtype: requests.models.Response
        @note: POST didn't work in my tests
        """
        if payload["text"] == "":
            raise EmptyTextException({"message": "Empty text"})
            return
        try:
            resp = requests.get(self.pars["url"], params=payload,
                                headers=self.headers)
        except requests.HTTPError, msg2:
            print "HTTPError: {0}\nTEXT: \"{1}\"".format(
                repr(msg2), repr(payload["text"]))
            return {}
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        return resp


class WikipediaMinerClientRemote(WSClient):
    """
    Calls Wikipedia Miner Web Service from
    http://wikipedia-miner.cms.waikato.ac.nz/services/
    As of January 2016, this service seems to be disconnected.
    @note: use L{WikipediaMinerClientDexter}
    @deprecated
    """
    def __init__(self, cfg):
        super(WikipediaMinerClientRemote, self).__init__(cfg)
        self.name = self.cfg.TNames.WI
        self.pars = self.cfg.params[self.name]

    def create_payload(self, text, options=None):
        """
        @param options: dict with options other than the text
        @type options: dict
        """
        if options is None:
            payload = {'source': text, 'references': 'true',
                       'minProbability': self.pars["minconf"]}
        else:
            payload = {'source': text}
            payload.update(options)
        return payload

    def get_response(self, payload):
        """
        Return the response as text format
        @rtype: text
        """
        if payload["source"] == "":
            raise EmptyTextException({"message": "Empty text"})
            return
        try:
            req = requests.post(self.pars["url"], data=payload)
        except requests.HTTPError, msg2:
            print "HTTPError: {0}\nTEXT: \"{1}\"".format(
                repr(msg2), repr(payload["source"]))
            return {}
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        resp = req.text
        return resp


class AidaClient(WSClient):
    """
    Calls AIDA REST API for an instance running locally at location
    in L{config}.
    """

    VERBOSE = False

    def __init__(self, cfg):
        super(AidaClient, self).__init__(cfg)
        self.name = self.cfg.TNames.AI
        self.pars = self.cfg.params[self.name]

    def create_payload(self, text, options=None):
        """@type options: dict"""
        if options is None:
            payload = {"text": text, "tech": "GRAPH"}
        else:
            payload = {"text": text}
            payload.update(options)
        return payload

    def get_response(self, payload):
        if payload["text"] == "":
            raise EmptyTextException({"message": "Empty text"})
            return
        try:
            req = requests.post(self.pars["url"], data=payload)
        except requests.HTTPError, msg2:
            print "HTTPError: {0}\nTEXT: \"{1}\"".format(
                repr(msg2), repr(payload["text"]))
            return {}
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        if self.VERBOSE:
            print req.url
        resp = req.json()
        return resp


class AidaRemoteClient(WSClient):
    """Calls AIDA public REST API."""

    VERBOSE = False

    def __init__(self, cfg):
        super(AidaRemoteClient, self).__init__(cfg)
        self.name = self.cfg.TNames.RA
        self.pars = self.cfg.params[self.name]

    def create_payload(self, text, options=None):
        """@type options: dict"""
        if options is None:
            payload = {"text": text, "tech": "GRAPH"}
            # http://stackoverflow.com/questions/17980362
            # {"fast_mode": json.dumps(True)} json.dumps for booleans
            payload = json.dumps(payload)
        else:
            payload = {"text": text}
            payload.update(options)
        return payload

    def get_response(self, payload):
        if json.loads(payload)["text"] == "":
            raise EmptyTextException({"message": "Empty text"})
            return
        try:
            req = requests.post(self.pars["url"], data=payload)
        except requests.HTTPError, msg2:
            print "HTTPError: {0}\nTEXT: \"{1}\"".format(
                repr(msg2), repr(payload["text"]))
            return {}
        except requests.exceptions.ConnectionError:
            print "! ConnectionError"
            return {}
        if self.VERBOSE:
            print req.url
        resp = req.json()
        return resp


class BabelfyClient(WSClient):
    """Calls Babelfy REST API."""

    def __init__(self, cfg):
        super(BabelfyClient, self).__init__(cfg)
        self.name = self.cfg.TNames.BF
        self.pars = self.cfg.params[self.name]

    def create_payload(self, text, options=None):
        if options is None:
            options = {'text': text.encode("utf8"),
                       'lang': self.pars["lang"],
                       'key': self.pars["key"]}
        return options

    def get_response(self, payload):
        res = requests.post(self.pars["url"],
                            headers={'Accept-encoding': 'gzip'},
                            data=payload)
        return res.content


class AnnotationReader(object):
    """
    Reads annotations from files formatted as in L{writers}
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.cpsmgr = analysis.CorpusMgr()

    def read_file(self, svc, cpsob, runid, ipt=None,
                  oneoutforall=True, has_snbr=True, has_normcat=True):
        """
        Read a single annotation file. If no path is given, assumes that it's
        a file containing annots for a corpus, and figures out the path from
        the other keyword arguments. Otherwise reads the path given.
        @param svc: service for annotations
        @param cpsob: L{model.Corpus} obj
        @param runid: run-id for the annotations to read
        @param ipt: file name
        @param oneoutforall: if True, means that input contains annots for a directory
        @param has_snbr: if True, one of the last two columns is the sent nbr
        @param has_normcat: if True, one of the last two columns is the normalized categ
        """
        assert not (ipt is None and oneoutforall is False)
        if ipt is None and oneoutforall:
            fn = "".join(("_".join((cpsob.name, svc, "all", runid)), ".txt"))
            ffn = os.path.join(self.cfg.outdir, fn)
        else:
            fn = ipt
            ffn = ipt
        annots = {}
        with codecs.open(ffn, "r", "utf8") as inf:
            try:
                line = inf.readline()
            except UnicodeDecodeError:
                print "UnicodeDecodeError. Skipping: {}".format(ffn)
                return annots
            while line:
                # skip header
                if line.startswith("doc\tmtn\tstart\tend\t"):
                    line = inf.readline()
                    continue
                sl = line.strip().split("\t")
                if oneoutforall:
                    ke = sl[0]
                    sh = 0
                else:
                    ke = os.path.basename(ffn)
                    sh = 1
                # empty file name
                if not ke:
                    continue
                annots.setdefault(ke, {})
                try:
                    if (self.cfg.use_confidence and float(sl[6-sh]) <
                        self.cfg.MinConfs.vals[self.cfg.mywscheme]\
                        [svc][self.cfg.myevmode]):
                        line = inf.readline()
                        continue
                    start, end, link = int(sl[2-sh]), int(sl[3-sh]), sl[4-sh]
                    # if ke == 'enb1207e.txt' and start == 258:
                    #     import pdb;pdb.set_trace()
                    annots[ke].setdefault((start, end), {})
                    mtnkey = self.cpsmgr.create_mention_key(ke, start, end)
                    cpsob.add_entity_to_corpus(link, svc)
                    cpsob.add_mention_to_corpus(mtnkey, sl[1-sh])
                    entity = cpsob.entities[link]
                    mention = cpsob.mentions[mtnkey]
                    annots[ke][(start, end)] = md.Annotation(mention, entity)
                    annots[ke][(start, end)].fmention = sl[1-sh]
                    annots[ke][(start, end)].service = sl[5-sh]
                    annots[ke][(start, end)].confidence = \
                        float(sl[6-sh])
                    try:
                        if has_snbr:
                            if has_normcat:
                                annots[ke][(start, end)].snbr = int(sl[-2])
                                annots[ke][(start, end)].normcat = sl[-1]
                            else:
                                annots[ke][(start, end)].snbr = int(sl[-1])
                        if has_normcat:
                            if has_snbr:
                                annots[ke][(start, end)].snbr = int(sl[-2])
                                annots[ke][(start, end)].normcat = sl[-1]
                            else:
                                annots[ke][(start, end)].normcat = sl[-1]
                    except ValueError:
                        if self.cfg.DBG:
                            print "ValueError: {}, {}".format(ffn, repr(sl))
                        pass
                except IndexError:
                    # if len(sl) == 1:
                    #     line = inf.readline()
                    #     print "IndexErrorSKIPPED (only fn, no annots): {}, [{}]".format(
                    #         ffn, sl[0])
                    #     continue
                    #import pdb;pdb.set_trace()
                    print "IndexError: {}, [{}]".format(ffn, line.strip())
                    line = inf.readline()
                    continue
                line = inf.readline()
        return annots

    def read_dir(self, dr, svc, cpsob, runid, oneoutforall=False, mask=None,
                 has_snbr=True, has_normcat=True):
        """
        Read annotation directory.
        @param dr: directory
        @param svc: service having produced the annots
        @param cpsob: L{model.Corpus} obj
        @param runid: run-id for the annots
        @param oneoutforall: if True, each file is understood as containing annots
        for a corpus (with the first column as the file name)
        @param mask: regex pattern (as string) to filter files in the directory
        """
        all_annots = {}
        if mask is None:
            todo = os.listdir(dr)
        else:
            todo = [f for f in os.listdir(dr) if re.match(mask, f)]
        dones = 0
        for fn in todo:
            annots = self.read_file(svc, cpsob, runid,
                                    oneoutforall=oneoutforall,
                                    ipt=os.path.join(dr, fn),
                                    has_snbr=has_snbr,
                                    has_normcat=has_normcat)
            all_annots.update(annots)
            dones += 1
            if dones % self.cfg.file_progress == 0:
                print "- Done {} files. [{}]".format(dones, time.asctime(time.localtime()))
        return all_annots
