"""Classes to run the other modules (input reader, EL clients and output writers)"""
import codecs
import time

import analysis as al
import clients
import model as md
import utils as ut


class RunnerManager(object):
    """
    To create the runner based on config.
    @ivar cfg: config values, e.g. L{config}
    """

    def __init__(self, cfg):
        self.cfg = cfg

    def create_runner(self, linker, reader, writer):
        """ Create runner based on config
        @param linker: the service to create the runner for
        @param reader: a L{readers} object to feed inputs to runner
        @param writer: a L{writers} object to write results
        """
        try:
            assert linker in self.cfg.activate
        except AssertionError:
            print "Allowed services: {}".format(
                ", ".join(self.cfg.activate.keys()))
        if linker == self.cfg.TNames.TM:
            client = clients.TagmeClient(self.cfg)
            runner = TagmeRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.SP:
            client = clients.SpotlightClient(self.cfg)
            runner = SpotlightRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.PS:
            client = clients.SpotstatClient(self.cfg)
            runner = SpotstatRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.WD:
            client = clients.WikipediaMinerClientDexter(self.cfg)
            runner = WikipediaMinerRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.WI:
            client = clients.WikipediaMinerClientRemote(self.cfg)
            runner = WikipediaMinerRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.AI:
            client = clients.AidaClient(self.cfg)
            runner = AidaRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.RA:
            client = clients.AidaRemoteClient(self.cfg)
            runner = AidaRemoteRunner(self.cfg, client, reader, writer)
        elif linker == self.cfg.TNames.BF:
            client = clients.BabelfyClient(self.cfg)
            runner = BabelfyRunner(self.cfg, client, reader, writer)
        else:
            return False
        return runner


class DefRunner(object):
    """
    Using config in cfg, assigns client to cl, an input reader to rd,
    and a module to postprocess results with to wr.
    @ivar cfg: Config infos or L{config}
    @ivar cl: A client (L{clients}) to obtain responses
    @ivar rd: A reader (L{readers}) to give input to client
    @ivar wr: A writer (L{writers}) to post-process responses
    @ivar donefn: hash to keep track of done filenames
    """

    def __init__(self, cfg, cl, rd, wr):
        self.cfg = cfg
        self.cl = cl
        self.rd = rd
        self.wr = wr
        self.donefn = {}

    def _run_one(self, fn, text, cpsob):
        """
        Creates a request for a text, gets response and obtains annotations.
        @param fn: file-name for text
        @param text: text to do request for
        @param cpsob: a L{model.Corpus} object
        """
        print "- Running file: {}".format(fn),
        pay = self.cl.create_payload(text)
        print "    Getting response",
        try:
            res = self.cl.get_response(pay)
        except clients.EmptyTextException as e:
            print e.args[0]["message"]
            return {}, {}
        time.sleep(self.cfg.waitfor)
        print "    Parsing annotations"
        anns = al.AnnotationParser.parse(fn, self.cl, res, cpsob)
        return res, anns

    def run_all(self, ipt, skiplist, cpsob):
        """
        Calls L{_run_one} for each item given as input, yielding
        the response, parsed annotations, document object and file name
        @param ipt: full path to input to run (or text-string to run)
        @param skiplist: filenames (one per line) to skip, if any
        """
        uts = ut.Utils(self.cfg)
        cat_ind = uts.load_entity_category_indicators()
        #input
        fn2txt = self.rd.read(ipt)
        try:
            dispipt = ipt[0:100]
        except IndexError:
            dispipt = ipt
        try:
            skips = [x.strip() for x in codecs.open(
                     skiplist, "r", "utf8").readlines()]
        except IOError:
            skips = []
        # run calls
        print "-- [{}] RUNNING COLLECTION: {}, {}".format(self.cl.name, dispipt,
                                                          time.asctime(time.localtime()))
        dones = 0
        todo = self.cfg.limit
        for fn in sorted(fn2txt):
            if fn in skips:
                print "Skipping {}".format(repr(fn))
                continue
            # create doc objs
            dob = md.Document(fn, text=fn2txt[fn])
            dob.find_sentence_positions()
            # annots
            try:
                res, anns = self._run_one(fn, ut.Utils.norm_text(fn2txt[fn]), cpsob)
            except ValueError, msg:
                print "\n! Error with file: {}".format(fn)
                print "\n" + msg.message
                res, anns = {}, {}
            uts.add_sentence_number_to_annots(anns, dob)
            for link in [an.enti.link for posi, an in anns.items()]:
                cpsob.normalize_entity_categories(link, cat_ind)
            dones += 1
            yield res, anns, dob, fn

            if dones == todo:
                break

    def write_results(self, res, anns, fn, cpsob, runid="001", outdir=None,
                      outresps=None):
        """
        Writes responses for en EL request, with option to
          - append to a single file for all requests
          - write to a separate file for each request
        @param res: the client response
        @param anns: parsed annotations
        @param fn: filename
        @param cpsob: L{model.Corpus} object
        @param runid: run-id to identify output files
        @param outdir: directory to output annotations
        @param outresps: directory to output client responses
        """
        # raw responses always to individual files
        self.wr.write_raw_responses({fn: res},
                                    self.cl.name, runid=runid, outdir=outresps)
        # annotations to a single file for all corpus
        if self.cfg.oneoutforall:
            if len(self.donefn) >= 1:
                self.wr.write_to_single({fn: anns},
                    self.cl.name, cpsob, runid=runid,
                    has_categ=self.cfg.add_categs, outdir=outdir)
            else:
                self.wr.write_to_single({fn: anns},
                    self.cl.name, cpsob, runid=runid,
                    has_categ=self.cfg.add_categs,
                    write_header=True, outdir=outdir)
        # annotations to individual files for each "file"
        else:
            self.wr.write_to_multi({fn: anns}, self.cl.name,
                cpsob, runid=runid, has_categ=self.cfg.add_categs,
                outdir=outdir)
        self.donefn[fn] = 1


class TagmeRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(TagmeRunner, self).__init__(cfg, cl, rd, wr)


class SpotlightRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(SpotlightRunner, self).__init__(cfg, cl, rd, wr)

    def _run_one(self, fn, text, cpsob):
        """
        See L{DefRunner}
        @note: Override since no need to create payload; pyspotlight
        library called by L{clients.SpotlightClient} creates it.
        """
        print "- Running file: {}".format(fn),
        print "    Getting response",
        res = self.cl.get_response(text)
        print "    Parsing annotations"
        anns = al.AnnotationParser.parse(fn, self.cl, res, cpsob)
        return res, anns


class SpotstatRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(SpotstatRunner, self).__init__(cfg, cl, rd, wr)

    def _run_one(self, fn, text, cpsob):
        """
        See L{DefRunner}
        @note: Override since no need to create payload; pyspotlight
        library called by L{clients.SpotlightClient} creates it.
        """
        print "- Running file: {}".format(fn),
        print "    Getting response",
        res = self.cl.get_response(text)
        print "    Parsing annotations"
        anns = al.AnnotationParser.parse(fn, self.cl, res, cpsob)
        return res, anns


class WikipediaMinerRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(WikipediaMinerRunner, self).__init__(cfg, cl, rd, wr)


class AidaRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(AidaRunner, self).__init__(cfg, cl, rd, wr)


class AidaRemoteRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(AidaRemoteRunner, self).__init__(cfg, cl, rd, wr)


class BabelfyRunner(DefRunner):

    def __init__(self, cfg, cl, rd, wr):
        super(BabelfyRunner, self).__init__(cfg, cl, rd, wr)

    def _run_one(self, fn, text, cpsob):
        """
        See L{DefRunner}
        @note: Override since need param text passed to
        L{analysis.AnnotationParser.parse} so that can get the mention
        based on character offsets (the API will not return the mention,
        just the offsets)
        """
        print "- Running file: {}".format(fn),
        pay = self.cl.create_payload(text)
        print "    Getting response",
        res = self.cl.get_response(pay)
        print "    Parsing annotations"
        anns = al.AnnotationParser.parse(fn, self.cl, res, cpsob, text=text)
        return res, anns
