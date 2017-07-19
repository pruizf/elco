"""To combine annotations from different services"""

__author__ = 'Pablo Ruiz'
__date__ = '24/12/15'
__email__ = 'pabloruizfabo@gmail.com'


import codecs
import copy
import inspect
import logging
import os
import sys
import time


here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)

import config as cfg
import analysis as an
import clients as cl
import model as md
import utils


lgr = logging.getLogger(__name__)
utils.Utils.specify_log(lgr, cfg.rover_log, logging.INFO)

myutils = utils.Utils(cfg)


class Group(object):
    """
    Represents groups of overlapping annotations.
    Regroups annotations into L{LinkGroup} based on the entity they point to.
    Selects an annotation using two steps:
      - Selects best entity in each L{LinkGroup} according to ROVER
      - Also selects a mention to represent the entity.
    @note: L{LinkGroup} creation and entity selection happen upon
    L{Group} creation: the L{Group}constructor calls all the relevant methods.
    """

    myweights = cfg.Weights.vals[cfg.mywscheme][cfg.myevmode]

    def __init__(self, annotlist):
        self.annotlist = annotlist
        self.linkgroups = self.create_linkgroups()
        self.bestp_linkgroups = []
        self.higher_linkgroups = []
        # populate
        self.find_bestp_linkgroups()
        self.find_higher_linkgroups()
        self.selected_linkgroup = self.select_linkgroup()
        if self.selected_linkgroup is not None:
            self.selected_annotation = \
                self.selected_linkgroup.select_annotation()
            # add the services that voted for the Entity
            self.selected_annotation.ent_voters = \
                self.selected_linkgroup.services.keys()
        else:
            self.selected_annotation = None

    def create_linkgroups(self):
        """
        Create groups of anotations containing each link (i.e.
        each DBpedia entity)
        @note: 'link' is the 'link' attribute of the L{md.Entity} of an
        L{md.Annotation}
        """
        linkgroups = {}
        links = set([an.enti.link for an in self.annotlist])
        for link in links:
            linkgroups.setdefault(link, LinkGroup())
            linkgroups[link].link = link
            # to vote mentions (i.e. how many annotators use each)
            linkgroups[link].mentionvotes = {}
            for an in self.annotlist:
                if an.enti.link == link:
                    linkgroups[link].services.setdefault(an.service, 0)
                    linkgroups[link].services[an.service] += 1
                    linkgroups[link].annots.append(an)
                    linkgroups[link].mentions.append(an.mention.surface)
                    linkgroups[link].mentionvotes.setdefault(
                        an.mention.surface, 0)
                    # mention vote by counting annotations having each mention
                    linkgroups[link].mentionvotes[an.mention.surface] += 1
            linkgroups[link].rover = self.compute_rover(linkgroups[link], cfg)
        return linkgroups

    @staticmethod
    def compute_rover(lg, cfg, service_list=None):
        """
        Computes the ROVER score for an entity based on annotators having
        produced it. Reference:
        http://www.lrec-conf.org/proceedings/lrec2008/pdf/908_paper.pdf
        @note: ok to use len(cfg.ranks) since only active
        annotators in cfg.systems_to_rank will make it to cfg.ranks
        """
        lgr.debug(u">> Start Rvr [{}], ({})".format(lg.link,
                  len(cfg.ranks)))
        if service_list is None:
            service_list = cfg.ranks
        rover = 0.0
        for service in [s for s in lg.services if s in service_list]:
            # N - (r + rank_corr) * p (from N - (r - 1) * p)
            old = rover
            rover += \
                ( len(cfg.ranks) - (cfg.ranks[service] +
                                              cfg.rank_spacer) ) * \
                  Group.myweights[service]
            myutils.log_rover(lg.link, service, old, rover, lgr)
        rover /= len(cfg.ranks)
        lgr.debug(u"    = Rvr [{}]: {}".format(lg.link, rover))
        return rover

    def find_bestp_linkgroups(self):
        """
        Find L{LinkGroup} in the group that have, among its voters,
        the annotator which obtained the best precision in the config.
        """
        for lg in self.linkgroups.values():
            if cfg.best_service in lg.services:
                self.bestp_linkgroups.append(lg)

    def find_higher_linkgroups(self):
        """
        Find L{LinkGroup} in the group that have a rover higher than the best
        possible precision in the config
        """
        for lg in self.linkgroups.values():
            if (lg.rover > max(Group.myweights.values()) and
                lg not in self.bestp_linkgroups):
                self.higher_linkgroups.append(lg)

    def select_linkgroup(self):
        """
        Selects the best annotation for a linkgroup based on rover scores and
        on whether the best service has voted for the annotation or not.
        I.e. you don't contradict the best service unless there's a higher rover
        coming from a group of voters that does not include the best.
        @note: bestp means service with best P (originally the weights were
        Precisions, that's why the 'P')
        @note: 'higher' means a service having produced an annot w a rover
        higher than the highest rover obtained by the bestp service
        @note: condition "BH0" (see code) is like a security that best-p service
        will win unless enough votes against. With the 1.75 a we used
        for the *SEM exps, the best-p service wins of itself if it's the only voter (see
        /home/pablo/projects/ned/ana/notes_re_voting_and_bestp_alone_etc.txt)
        """
        # bestp > 0
        if len(self.bestp_linkgroups) > 0:
            max_bestp = max([lg.rover for lg in self.bestp_linkgroups])
            # bestp and higher > 0 both
            if len(self.higher_linkgroups) > 0:
                candidate_linkgroups = sorted([
                    lg for lg in self.higher_linkgroups
                    if lg.rover > max_bestp], key=lambda lg: lg.rover)
                #TODO: what do when more than one annot or vote per service?
                # higher candidates exist (i.e. with a rover higher than
                # the maximum rover provided by the service with the best P
                if len(candidate_linkgroups) > 0:
                    candidate_linkgroups[0].selected = True
                    candidate_linkgroups[0].selreason = "HgtB"
                    return candidate_linkgroups[0]
                # only bestp candidates exist
                else:
                    candidate_linkgroups = [lg for lg in self.bestp_linkgroups
                                            if lg.rover == max_bestp]
                    candidate_linkgroups[0].selected = True
                    candidate_linkgroups[0].selreason = "BgtH"
                    return candidate_linkgroups[0]
            # bestp > 0 but higher empty
            else:
                selected_linkgroups = sorted(self.bestp_linkgroups,
                    key=lambda lg: lg.rover, reverse=True)
                #TODO: what do when more than one annot or vote per service?
                selected_linkgroups[0].selected = True
                selected_linkgroups[0].selreason = "BH0"
                return selected_linkgroups[0]
        # bestp empty, higher > 0
        else:
            if len(self.higher_linkgroups) > 0:
                candidate_linkgroups = sorted([
                    lg for lg in self.higher_linkgroups
                    if lg.rover > max(Group.myweights.values())],
                    key=lambda lg: lg.rover)
                # test if higher candidates exist
                if len(candidate_linkgroups) >= 1:
                    candidate_linkgroups[0].selected = True
                    candidate_linkgroups[0].selreason = "HB0"
                    return candidate_linkgroups[0]
                else:
                    return None
            # both bestp and higher empty
            else:
                return None

    def __unicode__(self):
        outlist = [u"{} GROUP {}".format("=" * 8, "=" * 8)]
        for annot in self.annotlist:
            if isinstance(annot, md.Annotation):
                myannot1 = annot.__unicode__()
                outlist.append(myannot1)
        outlist.append(u"{} BestP_LG {}".format("=" * 4, "=" * 4))
        if len(self.bestp_linkgroups) == 0:
            outlist[-1] = "".join((outlist[-1], ": 0"))
        for lg in self.bestp_linkgroups:
            outlist.append(lg.__unicode__(with_annots=False))
        outlist.append(u"{} Highr_LG {}".format("=" * 4, "=" * 4))
        if len(self.higher_linkgroups) == 0:
            outlist[-1] = "".join((outlist[-1], ": 0"))
        for lg in self.higher_linkgroups:
            outlist.append(lg.__unicode__(with_annots=False))
        outlist.append(u"{} SelectedLinkGroup {}".format("=" * 4, "=" * 4))
        if self.selected_linkgroup is not None:
            outlist.append(self.selected_linkgroup.__unicode__(
                with_annots=False))
        else:
            outlist[-1] = "".join((outlist[-1], ": 0"))
        return "\n".join(outlist)

    def __str__(self):
        return unicode(self).encode("utf8")


class LinkGroup(object):
    """A group of annotations that point to the same entity"""
    def __init__(self):
        self.link = None
        self.services = {}
        self.mentions = []
        self.mentionvotes = {}
        self.rover = None
        self.annots = []
        self.selected = None
        self.selreason = None

    def select_annots_with_longest_mention(self):
        cands = sorted([an for an in self.annots], key=lambda an:
                        len(an.mention.surface), reverse=True)
        if len(cands) > 0:
            return cands[0]
        return None

    def select_annots_from_best_service(self):
        raise NotImplementedError

    def select_annots_with_most_votes(self):
        """
        Actually selects the annotation whose MENTION had most votes
        """
        # Votes come from L{self.create_linkgroups}
        #linkgroups[link].mentionvotes[an.mention.surface] += 1
        #TODO: what if several annotations have reached the max nbr of votes?
        #(in other words now im getting whatever mention the sort on .items()
        #returns first, i'm not really allowing more than one cand!)
        maxvotes = sorted(self.mentionvotes.items(), key=lambda x: -x[-1])[0][0]
        # maxvotes = sorted(self.mentionvotes.items(), key=lambda x:
        #                   (-x[-1], -len(x[0])))[0][0]
        #log.write(repr(self.mentionvotes) + "\n")
        cands = [an for an in self.annots if an.mention.surface == maxvotes]
        if len(cands) > 1:
            filtered = sorted(cands, key=lambda x: len(x.mention.surface),
                              reverse=True)
            # store services that have voted for this mention
            filtered[0].mtn_voters = [an.service for an in cands]
            return filtered[0]
        elif len(cands) > 0:
            # store services that have voted for this mention
            cands[0].mtn_voters = [an.service for an in cands]
            return cands[0]
        return None

    def select_annots_mix(self):
        raise NotImplementedError

    def select_annotation(self):
        """
        Select an annotation in linkgroup with the selection function
        specified in the config.
        """
        if cfg.mention_selection == "longest":
            return self.select_annots_with_longest_mention()
        if cfg.mention_selection == "service":
            return self.select_annots_from_best_service()
        if cfg.mention_selection == "votes":
            return self.select_annots_with_most_votes()
        if cfg.mention_selection == "mix":
            return self.select_annots_with_most_votes()

    def __unicode__(self, with_annots=True):
        if self.selected:
            outlist = [u"== **SEL_{} LinkGroup [{}] ==".format(
                self.selreason, self.link)]
        else:
            outlist = [u"== __REJ LinkGroup [{}] ==".format(self.link)]
        outlist.append(u"{}Votes: {}".format(u" " * 2,
            u"; ".join([", ".join((svc, str(self.services[svc])))
                       for svc in self.services])))
        outlist.append(u"{}Mentions: {}".format(u" " * 2,
            u", ".join([m for m in self.mentions])))
        outlist.append("{}Rover: {}".format(" " * 2, self.rover))
        if with_annots:
            for an in self.annots:
                outlist.append(u"{}{}".format(" " * 4,
                                              an.__unicode__()))
        return "".join(("\n".join(outlist), "\n"))

    def __str__(self):
        return unicode(self).encode("utf8")


class Combiner(object):
    """
    Combines annots based on a config. Provides some methods to manage the
    objects used to combine the annotations.
    """
    def __init__(self, cf):
        self.cfg = cfg
        self.ar = cl.AnnotationReader(self.cfg)

    def collect_annotations_for_service(self, infi, svc, collected=None):
        """
        Read annotations from results file
        @param infi: filename for results file
        @param svc: service for annotations (svc name needed to combine annots)
        @param collected: dict to store annots (create or update)
        @return: dict with annotations for all services
        """
        print "- Reading annots for service [{}], {}".format(
            svc, time.asctime(time.localtime()))
        cps = md.Corpus(self.cfg)
        # for now filenames are indeed provided by the client to this class
        if collected is None:
            return {svc: self.ar.read_file(svc, cps, "", ipt=infi)}
        else:
            collected.update(
                {svc: self.ar.read_file(svc, cps, "", ipt=infi)})
            return collected

    def add_to_combined(self, rdir, svc2id, svc2fn=None):
        """
        Add to a hash containing all services annots.
        @param svc2id: hash of run-ids or filenames per service to combine
        """
        # using custom file-names
        if svc2fn is not None:
            d2sort = svc2fn
            template = u"{}".format()
            resfiles = [os.path.join(rdir, template.format(myfn)) for _, myfn in
                        sorted(d2sort.items(),
                        key=lambda pair: cfg.linker_order.index(pair[0]))]
        # using file names based on a template, and a results dir
        else:
            d2sort = svc2id
            #template = u"{}_{}_all_{}.txt"
            template = u"{}-{}-sam{}.mapped"
            resfiles = [os.path.join(
                        rdir, template.format(cfg.cpsname, svcname, runnbr))
                        for svcname, runnbr in sorted(d2sort.items(),
                        key=lambda pair: cfg.linker_order.index(pair[0]))]
        # collective results
        sortsvc = sorted(d2sort, key=cfg.linker_order.index)
          # first service needs an empty dict
        abysvc = self.collect_annotations_for_service(
            resfiles[0], sortsvc[0], collected={})
        DataDumper.dump_individual_results(sortsvc[0], abysvc)
          # later services add to first service's results
        for idx, svc in enumerate(sortsvc[1:]):
            abysvc = self.collect_annotations_for_service(
                resfiles[idx+1], svc, abysvc)
            DataDumper.dump_individual_results(svc, abysvc)
        return abysvc


    @staticmethod
    def merge_annotations_per_position(svc2a):
        """
        Takes hash by service, filename and position, with L{md.Annotation} as values
        Returns hash by fn and position, with LISTS of L{md.Annotation} as values.
        @param svc2a: dict with annotations hashed by service, fn and position
        """
        #TODO: may need to deduplicate PER SERVICE in the fn2a of svc2a
        #      (actually for now decided to dedup before write-out, to
        #       give the combination proc more choices to match across linkers)
        #TODO: could filter per confidence here if not done earlier
        #TODO: (if so, pass it the config and it won't be static)
        print "- Accumulating annotations by position, {}".format(
            time.asctime(time.localtime()))
        posi2a = {}
        for svc, fn2a in svc2a.items():
            for fn, fposi2a in fn2a.items():
                posi2a.setdefault(fn, {})
                for posi, annot in fposi2a.items():
                    if annot.confidence >= 0.0:
                        posi2a[fn].setdefault(posi, [])
                        posi2a[fn][posi].append(annot)
        return posi2a

    @staticmethod
    def group_overlapping_annots(annots):
        """
        Group annotations based on positions for overlapping mentions
        @param annots: hash by fn and position, vals are L{md.Annotation} lists
        @return: hash of lists of overlapping L{md.Annotation} by fn
        @note: annots can be created w L{merge_annotations_per_position} above
        """
        print "- Grouping overlapping annots, {}".format(
            time.asctime(time.localtime()))
        groups = {}
        for fn in annots:
            groups.setdefault(fn, [])
            dones = []
            posis = sorted(annots[fn])
            for idx, posi in enumerate(posis):
                #if fn.startswith("1166testb") and posi == (27, 32):
                #    import pdb
                #    pdb.set_trace()
                overlaps = []
                if posi in dones:
                    continue
                # find overlapping positions
                iidx = idx
                # TODO: this can be buggy, see 1166testb_FREESTYLE	TIGNES
                # That's why I apply a cleanup after
                try:
                    while (iidx + 1 <= len(posis) - 1 and
                           #TODO: this skips files with ONE annot only
                           (utils.Utils.overlaps(posis[idx], posis[iidx + 1]))
                            or utils.Utils.overlaps(posis[iidx], posis[iidx + 1])):
                           #utils.Utils.overlaps(posis[iidx], posis[iidx + 1])):
                        overlaps.append(posis[iidx+1])
                        iidx += 1
                    groups[fn].append([])
                    assert isinstance(annots[fn][posi], list)  # to be sure
                    groups[fn][-1].extend(annots[fn][posi])
                    for ov in overlaps:
                        groups[fn][-1].extend([annot for annot in annots[fn][ov]])
                    dones.append(posi)
                    dones.extend(overlaps)
                    dones.pop(-1)
                except IndexError:
                    pass
        # Clean up (remove groups that are included in other groups)
        #TODO: debug instead of doing a cleanup
        groupscopy = copy.deepcopy(groups)
        for fn in sorted(groupscopy):
            one_posis = []
            several_posis = []
            for idx, group in enumerate(groupscopy[fn]):
                if len(set([(annot.mention.start, annot.mention.end)
                            for annot in group])) == 1:
                    one_posis.append(
                        (idx, list(set([(annot.mention.start, annot.mention.end)
                        for annot in group]))[0]))
                if len(set([(annot.mention.start, annot.mention.end)
                            for annot in group])) > 1:
                    several_posis.extend(
                        list(set([(annot.mention.start, annot.mention.end)
                        for annot in group])))
            removed = 0
            for posi in one_posis:
                if posi[1] in several_posis:
                    groups[fn].pop(posi[0] - removed)
                    removed += 1
        return groups

    #TODO: analysis.AnnotationParser.choose_annotation_with_longest_mention
    #TODO: does the overlap method there work (instead of this)

    @staticmethod
    def group_overlapping_annots_alt(annots):
        """Groups, hashed by fn"""
        print "- Grouping overlapping annots ALT, {}".format(
            time.asctime(time.localtime()))
        groups = {}
        for fn in annots:
            groups.setdefault(fn, [])
            dones = []
            posis = sorted(annots[fn])
            for idx, posi in enumerate(posis):
                #if fn.startswith("1166testb") and posi == (27, 32):
                #    import pdb
                #    pdb.set_trace()
                overlaps = []
                if posi in dones:
                    continue
                # find overlapping positions
                iidx = idx
                # TODO: this can be buggy, see 1166testb_FREESTYLE	TIGNES
                while (iidx + 1 <= len(posis) - 1 and
                       #gl.range_overlaps(posis[idx], posis[iidx + 1])):
                       utils.Utils.overlaps(posis[iidx], posis[iidx + 1])):
                    overlaps.append(posis[iidx+1])
                    iidx += 1
                groups[fn].append([])
                assert isinstance(annots[fn][posi], list)  # to be sure
                groups[fn][-1].extend(annots[fn][posi])
                for ov in overlaps:
                    groups[fn][-1].extend([annot for annot in annots[fn][ov]])
                dones.append(posi)
                dones.extend(overlaps)
                #dones.pop(-1)
        return groups


    @staticmethod
    def create_and_score_group_objects(grouped_annots):
        """
        Creates L{Group} objects and applies rover to them using methods in
        L{Group} and L{LinkGroup}.
        @param grouped_annots: hash by fn with lists of overlapping
        L{md.Annotation} (based on mention positions)
        """
        print "- Creating and scoring group objects: {}".format(
            time.asctime(time.localtime()))
        groupo = {}
        for fn in grouped_annots:
            groupo.setdefault(fn, [])
            for group in grouped_annots[fn]:
                groupo[fn].append(Group(group))
        return groupo


class DataDumper(object):
    """To write out the objects in this module"""

    def __init__(self, cfg):
        self.cfg = cfg

    def write_groupobjs(self, gos, out=None, suffix=""):
        """
        Write out L{} objects
        @param gos: Lists of group objects hased by filename
        @param out: output file
        """
        if out is None:
            out = self.cfg.groupobjs.format(suffix)
        if not os.path.exists(os.path.split(out)[0]):
            os.makedirs(os.path.split(out)[0])
        print "- Writing group objects to: {}".format(out)
        with codecs.open(out, "w", "utf8") as outf:
            for fn in sorted(gos):
                outf.write("{} {} {}\n".format("=" * 4, fn, "=" * 48))
                for group in sorted(gos[fn], key=lambda grp: min(
                        [ann.mention.start for ann in grp.annotlist])):
                    outf.write(unicode(group))
                    outf.write("\n")

    def write_linkgroups(self, gos, out=None, suffix=""):
        """
        Write out the L{LinkGroup} objects in a hash of L{Group} by filename
        @param gos: hash of L{Group} by filename
        @param out: output file name
        """
        if out is None:
            out = self.cfg.linkgroups.format(suffix)
        if not os.path.exists(os.path.split(out)[0]):
            os.makedirs(os.path.split(out)[0])
        print "- Writing link groups to: {}".format(out)
        with codecs.open(out, "w", "utf8") as outf:
            for fn in sorted(gos):
                for group in gos[fn]:
                    outf.write("{0} GROUP {0}\n".format("=" * 8))
                    for annot in group.annotlist:
                        outf.write("".join((fn, "\t", unicode(annot), "\n")))
                    for lg in group.linkgroups.values():
                        outf.write(lg.__unicode__(with_annots=True))

    def write_selected_annotations(self, gos, out=None, suffix=""):
        """
        Writes selected annotations from group objects
        @param gos: hash of L{Group} objects by filename
        @param out: output file name
        """
        if out is None:
            out = self.cfg.selected.format(suffix)
        if not os.path.exists(os.path.split(out)[0]):
            os.makedirs(os.path.split(out)[0])
        print "- Writing selected annots to: {}".format(out)
        with codecs.open(out, "w", "utf8") as outf:
            for fn in sorted(gos):
                outlines = []
                for group in gos[fn]:
                    if group.selected_annotation is not None:
                        if ("\t".join((fn, unicode(group.selected_annotation)))
                            not in outlines):
                            outlines.append("\t".join(
                            (fn, unicode(group.selected_annotation))))
                            # add services that voted for the link to make its group
                            # the selected L{md.LinkGroup}
                            outlines[-1] = u"{}\t{}".format(outlines[-1],
                                "|".join(sorted(group.selected_annotation.ent_voters,
                                         key=lambda lk:cfg.linker_order.index(lk))))
                            # add services that voted for the mention to select an
                            # L{md.Annotation} from the selected L{md.LinkGroup}
                            outlines[-1] = u"{}\t{}".format(outlines[-1],
                                ":".join(sorted(group.selected_annotation.mtn_voters,
                                         key=lambda lk:cfg.linker_order.index(lk))))
                #import pdb;pdb.set_trace()
                outf.write("\n".join(outlines))
                outf.write("\n")

    @staticmethod
    def get_all_selected_annotations(groupobjs):
        """
        Make a corpus-level hash by fn for all selected L{md.Annotation},
        since the selection procedure is at L{Group} and L{LinkGroup} level
        """
        sel = {}
        for fn in sorted(groupobjs):
            sel[fn] = []
            for group in groupobjs[fn]:
                if group.selected_annotation is not None:
                    sel[fn].append(group.selected_annotation)
        return sel

    @staticmethod
    def write_neleval_unstitched(aos, outfn):
        """
        Takes dict of L{md.annotation} objects hashed by fn and writes
        them in a format that can be read by Wikilinks neleval ('unstitched' format)
        @param aos: dict {fn: [list of L{md.Annotation}]}
        @type aos: dict
        @note: outfn gets '_neleval' appended to it unless it already ended so
        """
        print "- Writing selected annots [neleval format] to: {}".format(outfn)
        outlines = []
        uniq = copy.deepcopy(aos)
        for fn in aos:
            delcount = 0
            for idx, ao in enumerate(aos[fn]):
                if idx + 1 < len(aos[fn]):
                    ao1 = aos[fn][idx]
                    ao2 = aos[fn][idx + 1]
                    if utils.Utils.overlaps((ao1.mention.start, ao1.mention.end),
                                            (ao2.mention.start, ao2.mention.end)):
                        if len(ao1.mention.surface) > len(ao2.mention.surface):
                            del uniq[fn][idx + 1 - delcount]
                        else:
                            del uniq[fn][idx - delcount]
                        delcount += 1

        for fn, anl in sorted(uniq.items()):
            for an in sorted(anl, key=lambda ann: int(ann.mention.start)):
                outline = [fn, str(an.mention.start), str(an.mention.end),
                           an.enti.link]
                if outline not in outlines:
                    outlines.append(outline)
        if not outfn.endswith("_neleval"):
            outfn += "_neleval"
        with codecs.open(outfn, "w", "utf8") as outfh:
            for ll in outlines:
                outfh.write("".join(("\t".join(ll), "\n")))

    @staticmethod
    def dump_individual_results(svc, accan, noverlap=False, indivres=None):
        #accan: accumulated annots
        # indivres: to give a custom filename, otherwise it will be a template
        if noverlap:
            all_chosen = {}
            for fn in accan[svc]:
                # no overlaps
                all_chosen[fn] = \
                    an.AnnotationParser.choose_annotation_with_longest_mention(
                    accan[svc][fn])
        else:
            all_chosen = accan[svc]
        # still need to filter by confidence !
        chosen2 = {}
        for fn in all_chosen:
            chosen2[fn] = [ann for posi, ann in sorted(all_chosen[fn].items())
                           if ann.confidence >=
                           cfg.MinConfs.vals[cfg.mywscheme][svc][cfg.myevmode]]
        #cb.DataDumper.write_neleval_unstitched(chosen2,
        DataDumper.write_neleval_unstitched(chosen2,
            os.path.join(cfg.logdir, u"{}_{}_all_{}_neleval_indiv".format(
                cfg.cpsname, svc, cfg.combined_fake_id)))


def main():
    pass


if __name__ == "__main__":
    main()