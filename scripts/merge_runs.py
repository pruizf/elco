"""
To join results from different runs
@note: i think use of this is to not rerun a batch if it does not finish
"""

__author__ = 'Pablo Ruiz'
__date__ = '16/01/16'
__email__ = 'pabloruizfabo@gmail.com'


import codecs
import os
import shutil


cpsname = "neel"
linker = "wminer"
runs = {
    "tagme": [383, 384, 387, 3831],
    "spotstat": [427, 428],
    "wminer": [388],
    "aida": [456, 457, 458, 459],
    "raida": [393],
    "babelfy": [429, 430, 438, 439, 442, 443, 452, 453, 460, 463, 464, 465, 466, 467]
}

#runs = [456, 457, 458, 459] #aida
#runs = [429, 430, 438, 439, 442, 443, 452, 453, 460, 463, 464, 465, 466, 467] #babelfy
origdir = "/home/pablo/projects/el/elclient_other/elclientout2"
resdir = "/home/pablo/projects/el/NEEL/wk/indiv_system_results"
mergeddir = "/home/pablo/projects/el/NEEL/wk/indiv_system_results_merged"
mergedrun = 999
# ids
refset = "/home/pablo/projects/el/NEEL/2016_NEEL_Gold_Standard_copy_pr/Training Set/NEEL2016-training.tsv"
doneids = os.path.join(resdir, "{}_{}_{}_dones.txt".format(cpsname, linker, mergedrun))
todoids = os.path.join(resdir, "{}_{}_{}_todo.txt".format(cpsname, linker, mergedrun))
weirdids = os.path.join(resdir, "{}_{}_{}_weird.txt".format(cpsname, linker, mergedrun))


# merge runs
runlines = {}
lines2write = []
for run in runs[linker]:
    print run
    orifn = os.path.join(origdir, "{}_{}_all_{}.txt".format(cpsname, linker, run))
    fn = os.path.join(resdir, "{}_{}_all_{}.txt".format(cpsname, linker, run))
    try:
        shutil.copyfile(orifn, fn)
        #print "Copied {} to {}".format(orifn, fn)
    except IOError:
        print "Error", orifn
        continue
    ofn = os.path.join(mergeddir, "{}_{}_all_{}.txt".format(cpsname, linker, mergedrun))
    added = 0
    with codecs.open(fn, "r", "utf8") as fdi:
        line = fdi.readline()
        while line:
            if line.startswith("doc\tmtn"):
                lines2write.append(line)
                line = fdi.readline()
                continue
            sl = line.strip().split("\t")
            if tuple(sl[0:5]) in runlines:
                #if run == 442:
                #    print line
                line = fdi.readline()
                continue
            else:
                runlines[tuple(sl[0:5])] = True
                lines2write.append(line)
                added += 1
                line = fdi.readline()
        print "Added:", added
    with codecs.open(ofn, "w", "utf8") as fdo:
        fdo.write("".join(lines2write))


# figure out what missing
with codecs.open(refset, "r", "utf8") as ifd:
    refids = [ll.split("\t")[0] for ll in ifd]

sysids = [info[0] for info in runlines]

todos = set(refids).difference(set(sysids))
dones = set(refids).intersection(set(sysids))
weird = set(sysids).difference(set(refids))

with codecs.open(doneids, "w", "utf8") as donefdi:
    for tid in sorted(dones):
        donefdi.write(u"{}\n".format(tid))

with codecs.open(todoids, "w", "utf8") as todofdi:
    for tid in sorted(todos):
        todofdi.write(u"{}\n".format(tid))

with codecs.open(weirdids, "w", "utf8") as weirdfdi:
    for tid in sorted(weird):
        weirdfdi.write(u"{}\n".format(tid))

if len(list(weird)):
    print "Weird: print weird"
