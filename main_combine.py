"""
Annotation combination based on ready annotations. The services to combine
are in svc2ids or svc2fns.
Use svc2ids when all results are in same directory and a run-id identifies
each. (A template is used for the filename)
Use svc2fns to give paths for each service's result, without a template of
common directory.
"""

__author__ = 'Pablo Ruiz'
__date__ = '24/12/15'
__email__ = 'pabloruizfabo@gmail.com'


import inspect
import os
import sys
import time


here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)

import config as cfg
import combination as cb
import utils

# to force config reload
if "cfg" in dir(sys.modules["__main__"]): reload(cfg)


# Options ---------------------------------------------------------------------
FORCE_CONFID = True  # force to use L{cfg.MinConfs} values
                     # even if original config has them turned off
CUSTOM_FNAMES = False

#resdir = "/home/pablo/projects/el/NEEL/wk/indiv_system_results_merged_selected_mapped"
#resdir = "/home/pablo/projects/el/wk/outputs_new_linkers_jan2016/iitb/sam"
resdir = "/home/pablo/projects/el/wk/new_results/data/system_results_ec/mapped"

if FORCE_CONFID:
    cfg.use_confidence = True  # used by cl.AnnotationReader.read_file, called
                               # not statically by collect_annotations_for_service
                               # in a combiner instance created in this  module.
                               # so the instance will access this modif cfg value

# list services and run-ids for their results -------------
if not CUSTOM_FNAMES:
    # svc2ids = {cfg.TNames.TM: "", cfg.TNames.WD: "", cfg.TNames.SP: "",
    #            cfg.TNames.AI: ""}
    # old results
    svc2ids = {cfg.TNames.TM: "", cfg.TNames.WI: "", cfg.TNames.SP: "",
               cfg.TNames.AI: "", cfg.TNames.BF: ""}
    svc2fns = None
    dict4lencheck = svc2ids
# if need custom fnames, list services and fnames for their results -
else:
    svc2fns = {}
    svc2ids = None
    dict4lencheck = svc2fns


def main():
    """Run combination"""
    myutils = utils.Utils(cfg)
    myrunid = myutils.read_runid()
    try:
        cbr = cb.Combiner(cfg)
        dd = cb.DataDumper(cfg)
        try:
            assert len(dict4lencheck) == len(cfg.ranks)
        except AssertionError:
            print "! Attempt to combine [{}] linkers, but config expects [{}]".format(
                len(dict4lencheck), len(cfg.ranks))
            sys.exit(2)
        # accumulate annots per service
        aabysvc = cbr.add_to_combined(resdir, svc2ids, svc2fns)
        # combine
        abyposi = cb.Combiner.merge_annotations_per_position(aabysvc)
        if cfg.overlap == "alt":
            grouped_anns = cb.Combiner.group_overlapping_annots_alt(abyposi)
        else:
            grouped_anns = cb.Combiner.group_overlapping_annots(abyposi)
        groupobjs = cb.Combiner.create_and_score_group_objects(grouped_anns)
        selected_annots = cb.DataDumper.get_all_selected_annotations(groupobjs)

        suffix = cfg.combined_fn_suffix.format(cfg.cpsname, cfg.overlap,
                                               myrunid)
        # suffix helps define the filename
        dd.write_groupobjs(groupobjs, suffix=suffix)
        dd.write_linkgroups(groupobjs, suffix=suffix)
        dd.write_selected_annotations(groupobjs, suffix=suffix)
        cb.DataDumper.write_neleval_unstitched(selected_annots, os.path.join(
            cfg.logdir, suffix))
    finally:
        myutils.cleanup(myrunid)

    print "Linkers used: {}".format(",".join(sorted(dict4lencheck.keys(),
                                    key=cfg.linker_order.index)))
    print "Rank spacer: {}".format(cfg.rank_spacer)
    print "Done: {}".format(time.asctime(time.localtime()))


if __name__ == "__main__":
    main()
