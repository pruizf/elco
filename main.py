"""Runs app"""

import inspect
import os
import sys
import time

here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)

import config as cfg
import model as md
import utils
import readers as rd
import writers as wr
import runners as rn


def main():

    print "~~ START: {} ~~".format(time.asctime(time.localtime()))

    # cli arguments -----------------------------------------------------------

    utl = utils.Utils(cfg)
    argus = utl.run_argparse()

    # common elements to all linkers ------------------------------------------
    global mycps  # debug
    mycps = md.Corpus(cfg, name=argus.corpus_name)  # corpus object
    rmgr = rn.RunnerManager(cfg)  # runner manager
    utl.setup(outdir=argus.myout, outresps=argus.myoutresps)
    myrunid = utl.read_runid()
    myreader = rd.DefReader(cfg)
    mywriter = wr.Obj2TsvWriter(cfg)

    # linker specific ---------------------------------------------------------

    runners = []

    for linker in sorted(cfg.activate, key=cfg.linker_order.index):
        if cfg.use_all_linkers or cfg.activate[linker]["general"]:
            myrunner = rmgr.create_runner(linker, myreader, mywriter)
            if myrunner:
                runners.append(myrunner)
            else:
                print "! Error creating runner for [{}]".format(linker)

    # run ---------------------------------------------------------------------

    print "\n- Will get results for: {}\n".format(
        ", ".join([ru.cl.name for ru in runners]))

    try:
        for runner in runners:
            for resp, anns, dob, fn in \
                runner.run_all(argus.myinput, argus.myskiplist, mycps):
                # can deduplicate mentions or import to sql from here
                runner.write_results(resp, anns, fn, mycps, myrunid,
                                     outdir=argus.myout,
                                     outresps=argus.myoutresps)
    finally:
        # cleanup
        utl.cleanup(myrunid)

    print "~~ END: {} ~~".format(time.asctime(time.localtime()))

if __name__ == "__main__":
    main()
