"""Aida Service writes stuff with json escapes. Testing how to unescape them"""

__author__ = 'Pablo Ruiz'
__date__ = '03/01/16'
__email__ = 'pabloruizfabo@gmail.com'

import codecs
import shutil


escapes = "/home/pablo/projects/el/elclients/data/json_escapes.txt"
#tfn = "/home/pablo/projects/el/elclient_other/elclientres2/100000025580548097_raida_405.txt"
#tfn = "/home/pablo/projects/el/elclient_other/elclientlogs/conll_enb_all_combine_alt_436_neleval"
#tfno = "/home/pablo/projects/el/elclient_other/elclientres2/100000025580548097_raida_405_OUT3.txt"
#tfno = "/home/pablo/projects/el/elclient_other/elclientlogs/conll_enb_all_combine_alt_436_neleval_OUT2"

tfn = "/home/pablo/projects/el/NEEL/wk/indiv_system_results_merged_selected/neel_raida_all_999.txt"
tfno = "/home/pablo/projects/el/NEEL/wk/indiv_system_results_merged_selected/neel_raida_all_999.txt"

#/home/pablo/projects/el/elclient_other/elclientres2/100000025580548097_raida_405.txt


shutil.copy(tfn, tfn + ".bkp")

txt = codecs.open(escapes, "r", "utf8").readlines()
reps = {}
for ll in txt:
    if ll.startswith("#"):
        continue
    try:
        sl = ll.split("\t")
        code = ur"\{}".format(sl[0].lower())
        ch = sl[1].strip()
        reps[code] = ch
    except IndexError:
        continue

ori = codecs.open(tfn, "r", "utf8").read()
modif = ori

print "Type: {}".format(type(modif))
for co in reps:
    modif = modif.replace(co, reps[co])

with codecs.open(tfno, "w", "utf8") as ouf:
    ouf.write(modif)
