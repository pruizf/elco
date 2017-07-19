"""Config"""

import inspect
import os

# BASIC =======================================================================
cpsname = "conll"  # name to identify corpus with in output files
DBG = False
limit = 100000000000#00000000  # max files to run (for tests)
waitfor = 0  # sleep between connections
myinput = "ABSOLUTE PATH TO INPUT"
files2skip = "ABSOLUTE PATH TO LIST OF FILES WHOSE NAMES WILL BE IGNORED"
oneoutforall = True  # write responses for whole corpus to the same output file (True)
                     # or write to individual files
mywscheme = "conll"  # chosen weighting scheme for rover
#mywscheme = "tweets"  # chosen weighting scheme for rover
myevmode = "sam"     # chosen evaluation mode
mention_selection = "votes"  # way to select mentions for entity that wins rover
# parameter to space result weights in rover formula
if mywscheme == "tweets":
    rank_spacer = -2.5
else:
    rank_spacer = -1.75
assert mention_selection in ("longest", "service", "votes", "mix")
overlap = "alt"      # way to group annotations based on mention overlap
use_confidence = False  # use confidence thresholds in L{MinConf} or not


# EL modules ==================================================================
class TNames(object):
    TM = "tagme"
    SP = "spotlight"
    PS = "spotstat"  # spotlight statistical backend
    WI = "wminer"    # unused since public service down
    WD = "wmdexter"  # Dexter wminer implementation
    I2 = "ilwi2013"  # illinois wikifier
    I3 = "ilwi31"    # illinois wikifier 3
    AI = "aida"      # aida deployed locally
    RA = "raida"     # aida public service
    BF = "babelfy"


# activate modules ------------------------------------------------------------
use_all_linkers = bool(0)

activate = {
    TNames.TM: {"general": bool(1), "rover": bool(0)},
    TNames.SP: {"general": bool(0), "rover": bool(0)},
    TNames.PS: {"general": bool(0), "rover": bool(0)},
    TNames.WI: {"general": bool(0), "rover": bool(0)},  # unused
    TNames.WD: {"general": bool(0), "rover": bool(0)},
    TNames.I2: {"general": bool(0), "rover": bool(0)},
    TNames.I3: {"general": bool(0), "rover": bool(0)},
    TNames.AI: {"general": bool(0), "rover": bool(0)},
    TNames.RA: {"general": bool(0), "rover": bool(0)},
    TNames.BF: {"general": bool(0), "rover": bool(0)}
}

# order to run linkers (category outputs complement each other based on this)
linker_order = (TNames.TM, TNames.PS, TNames.SP, TNames.WI,
                TNames.AI, TNames.RA, TNames.BF)
# linker_order = (TNames.TM, TNames.PS, TNames.SP, TNames.WD,
#                 TNames.AI, TNames.RA,
#                 TNames.I2, TNames.I3, TNames.BF, TNames.WI)
assert [lo in activate for lo in linker_order]

# module params ---------------------------------------------------------------
# The minimum confidence here is 0, so that L{clients} get all possible responses.
# Then L{analysis.AnnotationParser} uses values in L{MinConf} below to create
# L{model.Annotation} objects
params = {
    # TNames.TM: {"url": "http://tagme.di.unipi.it/tag",
    TNames.TM: {"url": "https://tagme.d4science.org/tagme/tag",
                "minconf": 0.0,
                "key": "ADD YOUR KEY",
                "include_categories": True,
                "lang": "en"},
    TNames.SP: {"url": "http://spotlight.dbpedia.org/rest/annotate",
                "minconf": 0.0},
    #TNames.PS: {"url": "http://spotlight.sztaki.hu:2222/rest/annotate",
    TNames.PS: {"url": "http://localhost:2222/rest/annotate",
                "minconf": 0.0},
    # disconnected
    TNames.WI: {"url": "http://wikipedia-miner.cms.waikato.ac.nz/services/wikify",
    #TNames.WI: {"url": "http://galan.ehu.es/wikiminer/wikify",
                # to get categories
                "catsvc": "http://wikipedia-miner.cms.waikato.ac.nz/services/exploreArticle",
                "minconf": 0.0},
    TNames.WD: {"url": "http://localhost:8080/dexter-webapp/api/rest/annotate",
                "minconf": 0.0},
    TNames.AI: {"url": "http://localhost:8080/aida/service/disambiguate-defaultsettings",
    # TNames.AI: {"url": "http://localhost:8080/aida/service/disambiguate",
    #            "minconf": 0.0, "tech": "LOCAL"}, # GRAPH is default
                "minconf": 0.0},  # GRAPH is default
    TNames.RA: {"url": "https://gate.d5.mpi-inf.mpg.de/aida/service/disambiguate",
                "minconf": 0.0},
    TNames.BF: {"url": "https://babelfy.io/v1/disambiguate",
                "minconf": 0.0,
                "key1": "ADD YOUR KEY",     # 1000 requests per day each
                "lang": 'EN'}
}

# paths
basedir = os.path.join(os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe()))))
datadir = os.path.join(os.path.join(basedir, "data"))
resdir = os.path.join(os.path.join(basedir, os.pardir),
                      "elclient_other" + os.sep + "elclientres2")
outdir = os.path.join(os.path.join(basedir, os.pardir),
                      "elclient_other" + os.sep + "elclientout2")
logdir = os.path.join(os.path.join(basedir, os.pardir),
                      "elclient_other" + os.sep + "elclientlogs")
runidf = os.path.join(os.path.join(basedir, os.pardir),
                      "elclient_other" + os.sep + "runid")
runidnbr = 1

res_pickle = os.path.join(outdir, "{}.pgz".format(cpsname))


# entity classification =======================================================
add_categs = True
categ_cache = os.path.join(datadir, "categ_cache.p")
perind = os.path.join(datadir, "percat.xml")
orgind = os.path.join(datadir, "orgcat.xml")
locind = os.path.join(datadir, "loccat.xml")

# linker specific config
DBPRESPREF = u'http://dbpedia.org/resource/'
AIDA_KBPREFIX = u"YAGO:"

# if true, category information returned by the service will be added
#   to available information for an entity
redo_ents = {TNames.TM: bool(0),
             TNames.SP: bool(1),
             TNames.PS: bool(1),
             TNames.WD: bool(0),
             TNames.WI: bool(0),
             TNames.AI: bool(0),
             TNames.RA: bool(0),
             TNames.BF: bool(0)}


# output config ===============================================================
random_id_length = 6
class OModes(object):
    TSV = "tsv"
    DEF = TSV

omode = OModes.DEF


# evaluation ==================================================================
# modes (like in Cornolti 2013 BAT Framework)
class EvModes(object):
    WAM = "wam"  # weak annotation match
    SAM = "sam"  # strong annotation match
    ENT = "ent"  # entity match


# System Thresholds ============================================================

class MinConfs(object):
    """
    Confidence thresholds considered optimal for each system and evaluation mode
    (tests with Cornolti's BAT)
    """
    # test corpus names
    CONLL = "conll"
    IITB = "iitb"
    TWEE = "tweets"
    SMVL = "semeval"
    MSNBC = "msnbc"
    AQUAINT = "aquaint"

    # thresholds
    vals = {
        CONLL: {  # evaluated on conll B (BAT framework)
            # note: WD WAM is fake (copied the ENT, neleval has no WAM per se ...)
            TNames.TM: {EvModes.SAM: 0.219, EvModes.WAM: 0.219, EvModes.ENT: 0.234},
            TNames.SP: {EvModes.SAM: 0.086, EvModes.WAM: 0.094, EvModes.ENT: 0.094},
            TNames.PS: {EvModes.SAM: 0.086, EvModes.WAM: 0.094, EvModes.ENT: 0.094}, # copied from SP
            TNames.WI: {EvModes.SAM: 0.57, EvModes.WAM: 0.477, EvModes.ENT: 0.477},
            TNames.WD: {EvModes.SAM: 0.05, EvModes.WAM: 0.05, EvModes.ENT: 0.05}, # untested
            TNames.AI: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.RA: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.BF: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
        },

        IITB: {  # evaluated on iitb (BAT framework in 2015, own work in 2016)
            TNames.TM: {EvModes.SAM: 0.086, EvModes.WAM: 0.094, EvModes.ENT: 0.102},
            TNames.SP: {EvModes.SAM: 0.016, EvModes.WAM: 0.016, EvModes.ENT: 0.008},
            TNames.PS: {EvModes.SAM: 0.016, EvModes.WAM: 0.016, EvModes.ENT: 0.008},
            #TODO isn't WI 0.219 and 0.195 for WAM and ENT (like in the previous version)?
            # (this only matters to reproduce old results, cos WI no longer accessible)
            #TNames.WI: {EvModes.SAM: 0.25, EvModes.WAM: 0.016, EvModes.ENT: 0.008},
            TNames.WI: {EvModes.SAM: 0.25, EvModes.WAM: 0.016, EvModes.ENT: 0.008},
            TNames.WD: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.AI: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.RA: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.BF: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
        },

        MSNBC: {
            TNames.TM: {EvModes.SAM: 0.188, EvModes.WAM: 0.188, EvModes.ENT: 0.328},
            TNames.SP: {EvModes.SAM: 0.063, EvModes.WAM: 0.047, EvModes.ENT: 0.063},
            TNames.PS: {EvModes.SAM: 0.063, EvModes.WAM: 0.047, EvModes.ENT: 0.063},
            TNames.WI: {EvModes.SAM: 0.664, EvModes.WAM: 0.57, EvModes.ENT: 0.664},
            TNames.AI: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.RA: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.BF: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
        },

        AQUAINT: {
            TNames.TM: {EvModes.SAM: 0.188, EvModes.WAM: 0.188, EvModes.ENT: 0.188},
            TNames.SP: {EvModes.SAM: 0.055, EvModes.WAM: 0.047, EvModes.ENT: 0.055},
            TNames.PS: {EvModes.SAM: 0.055, EvModes.WAM: 0.047, EvModes.ENT: 0.055},
            TNames.WI: {EvModes.SAM: 0.57, EvModes.WAM: 0.57, EvModes.ENT: 0.523},
            TNames.AI: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.RA: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.BF: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
        },

        TWEE: {
            TNames.TM: {EvModes.SAM: 0.35, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.SP: {EvModes.SAM: 0.95, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.PS: {EvModes.SAM: 0.95, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.WI: {EvModes.SAM: 0.3, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.WD: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.I2: {EvModes.SAM: 0.1, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.I3: {EvModes.SAM: 0.1, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            # TNames.AI: {EvModes.SAM: 0.25, EvModes.WAM: 0.0, EvModes.ENT: 0.0}, # unmapped
            # TNames.RA: {EvModes.SAM: 0.25, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.AI: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},   # mapped
            TNames.RA: {EvModes.SAM: 0.2, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
            TNames.BF: {EvModes.SAM: 0.0, EvModes.WAM: 0.0, EvModes.ENT: 0.0},
        },

        SMVL: { # used for semeval 2015 task 13 English (BAT paper, Table 11)
            TNames.TM: {EvModes.SAM: 0.102, EvModes.WAM: 0.102},
            TNames.SP: {EvModes.SAM: 0.023, EvModes.WAM: 0.023},
            TNames.PS: {EvModes.SAM: 0.023, EvModes.WAM: 0.023},
            TNames.WI: {EvModes.SAM: 0.219, EvModes.WAM: 0.219},
            TNames.BF: {EvModes.SAM: 0.0, EvModes.WAM: 0.0},
            TNames.AI: {EvModes.SAM: 0.0, EvModes.WAM: 0.0},
        }
    }


# SYSTEM COMBINATION ==========================================================

class Weights(object):
    """
    System weighting schemes for ROVER, based on evaluating the systems
    on different test corpora.
    The values correspond to precision (unless specified otherwise)
    on the test corpus (actually like a dev corpus).
    We have four dev corpora: conll, iitb, tweets (neel 2016) and
    semeval (2015 task 13)
    """
    # test corpus names
    CONLL = "conll"
    IITB = "iitb"
    TWEE = "tweets"
    SMVL = "semeval"

    # weights
    vals = {
        # WD WAM is a copy of ENT
        CONLL: {  # evaluated on conll B
            EvModes.SAM: {TNames.TM: 0.548, TNames.WI: 0.453,
                          TNames.WD: 0.584,
                          TNames.AI: 0.767, TNames.RA: 0.767,
                          TNames.SP: 0.281, TNames.PS: 0.281,
                          TNames.BF: 0.347},
            EvModes.WAM: {TNames.TM: 0.610, TNames.WI: 0.458,
                          TNames.WD: 0.625,
                          TNames.AI: 0.767, TNames.RA: 0.767,
                          TNames.SP: 0.280, TNames.PS: 0.280,
                          TNames.BF: 0.347},
            EvModes.ENT: {TNames.TM: 0.528, TNames.WI: 0.453,
                          TNames.WD: 0.625,
                          TNames.AI: 0.767, TNames.RA: 0.767,
                          TNames.SP: 0.281, TNames.PS: 0.281,  # not documented
                          TNames.BF: 0.347
                         }
            },

        IITB: {  # evaluated on iitb
            EvModes.SAM: {TNames.TM: 0.411, TNames.WI: 0.552,
                          TNames.WD: 0.308,
                          TNames.AI: 0.502, TNames.RA: 0.502,
                          TNames.SP: 0.410, TNames.PS: 0.410,
                          TNames.BF: 0.468},
            EvModes.WAM: {TNames.TM: 0.409, TNames.WI: 0.549,
                          TNames.WD: 0.450,
                          TNames.AI: 0.502, TNames.RA: 0.502,
                          TNames.SP: 0.408, TNames.PS: 0.408,
                          TNames.BF: 0.347},
            EvModes.ENT: {TNames.TM: 0.476, TNames.WI: 0.613,
                          TNames.WD: 0.450,
                          TNames.AI: 0.614, TNames.RA: 0.614,
                          TNames.SP: 0.366,  # not documented
                          TNames.PS: 0.366,  # not documented
                          TNames.BF: 0.484   # note documented
            }
        },

        TWEE: {
            EvModes.SAM: {TNames.TM: 0.641, TNames.WI: 0.386,
                          TNames.RA: 0.668, TNames.AI: 0.571,
                          TNames.SP: 0.272, TNames.PS: 0.272,
                          TNames.WD: 0.349, TNames.I2: 0.346,
                          TNames.I3: 0.175, TNames.BF: 0.1},
            EvModes.WAM: {TNames.TM: 0.610, TNames.WI: 0.458,
                          TNames.AI: 0.767, TNames.RA: 0.767,
                          TNames.SP: 0.280, TNames.BF: 0.347},
            EvModes.ENT: {TNames.TM: 0.528, TNames.WI: 0.453,
                          TNames.AI: 0.767, TNames.RA: 0.767,
                          TNames.SP: 0.281, TNames.PS: 0.281,  # not documented
                          TNames.BF: 0.347                     # not documented
            }
        },

        SMVL: { # used for semeval 2015 task 13 English
            EvModes.WAM: {TNames.TM: 0.452, TNames.WI: 0.568,
                          TNames.SP: 0.462, TNames.PS: 0462},
        }
    }

assert mywscheme in (Weights.CONLL, Weights.IITB, Weights.TWEE, Weights.SMVL)

#TODO: to make this easier, can i list ALL possible annotators in Weights and systems_to_rank?
#TODO: and then check *automatically* that any INACTIVE annotator as per 'activate'
#TODO: above is inactive in systems_to_rank
# this would mean that activate has two uses: when running main, it defines which linkers
# to run. For main_combine, it defines which results to mix)

# Systems chosen to rank for each weighting scheme
systems_to_rank = {
    Weights.CONLL: {TNames.TM: 1, TNames.WI: 1, TNames.SP: 1, TNames.PS: 0,
                    TNames.AI: 1, TNames.RA: 0,
                    TNames.WD: 1, TNames.BF: 0},
    Weights.IITB:  {TNames.TM: 1, TNames.WI: 1, TNames.SP: 1, TNames.PS: 0,
                    TNames.AI: 1, TNames.RA: 0, TNames.BF: 1},
    # ALL
    # Weights.TWEE:  {TNames.TM: 1, TNames.WI: 0, TNames.SP: 0, TNames.PS: 1,
    #                 TNames.AI: 0, TNames.RA: 1,
    #                 TNames.WD: 1, TNames.I2: 1, TNames.I3: 1,
    #                 TNames.BF: 0},
    Weights.TWEE:  {TNames.TM: 1, TNames.WI: 0, TNames.SP: 0, TNames.PS: 1,
                    TNames.AI: 0, TNames.RA: 1,
                    TNames.WD: 1, TNames.I2: 0, TNames.I3: 0,
                    TNames.BF: 0},
    Weights.SMVL:  {TNames.TM: 1, TNames.WI: 1, TNames.SP: 0, TNames.PS: 1,
                    TNames.AI: 0, TNames.RA: 0, TNames.BF: 0},
}

# prevent two active versions of same tool
assert not (systems_to_rank[mywscheme][TNames.SP] and
            systems_to_rank[mywscheme][TNames.PS])
assert not (systems_to_rank[mywscheme][TNames.AI] and
            systems_to_rank[mywscheme][TNames.RA])

# Ranks for chosen systems by system weight, for the chosen weighting scheme
# and evaluation mode (needed for ROVER formula)
ranks = {}
sorter = Weights.vals[mywscheme][myevmode]
for sy in [stm for stm in systems_to_rank[mywscheme]
           if systems_to_rank[mywscheme][stm]]:
    ranks.update({sy: sorted(sorter, key=lambda sm: sorter[sm],
                      reverse=True).index(sy)})
best_service = sorted(ranks.items(), key=lambda item: item[-1])[0][0]


# cooccurrence ================================================================

cooc_print = False
use_cooc_header = True
cooc_header = ["Source", "Target", "Weight"]

cooc_annots = {TNames.TM: bool(1),
               TNames.SP: bool(0),
               TNames.PS: bool(1),
               TNames.WI: bool(1),
               TNames.AI: bool(1),
               TNames.RA: bool(0),
               TNames.BF: bool(1)}

# prevent two active versions of same tool
assert not (cooc_annots[TNames.AI] and cooc_annots[TNames.RA])
assert not (cooc_annots[TNames.SP] and cooc_annots[TNames.PS])

cooc_def_minconf = True  # use default confidences for coocurrences

cooc_minconf = {TNames.TM: float(0.0),
                TNames.SP: float(0.0),
                TNames.PS: float(0.0),
                TNames.WI: float(0.0),
                TNames.AI: float(0.0),
                TNames.RA: float(0.0),
                TNames.BF: float(0.0)}

cooc_categs = {'ALL': bool(1),
               'ORG': bool(1),
               'PER': bool(1),
               'LOC': bool(1)}


# logging =====================================================================

# messages ------------------------------------------------
file_progress = 1000    # log progress every 1000 calls
node_progress = 10000   # nodes in co-occurrence graphs
sent_progress = 10000   # sentences
written_progress = 100000    # files written

# files ---------------------------------------------------
rover_log = os.path.join(logdir, "rover_log2.txt")
groupobjs = os.path.join(logdir, "groupobjs_{}")
linkgroups = os.path.join(logdir, "linkgroups_{}")
selected = os.path.join(logdir, "selected_{}")
combined_fake_id = 1002  # this is a run id used in main_combine_new
                         # (unrelated to runid computed with utils)
# used in filenames for combined results.
# this results only available in a single file for the whole corpus
#
combined_fn_suffix = u"{}_combine_all_{}_{}"


# db ==========================================================================
db = 'elclients2'
host = 'localhost'
user = 'NAME OF USER'
pw = 'PASSWORD'
