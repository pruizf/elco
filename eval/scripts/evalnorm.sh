#!/bin/sh

# DEPRECATED SINCE I'M NO LONGER EVALUATING AGAINST ASCII-ONLY RESULTS

MAPPER=/home/pablo/projects/ned/dhned/scripts/apply_wp_mapping.py
NORM=/home/pablo/projects/ned/dhned/scripts/write_in_ascii.py
MAP="/home/pablo/projects/ned/dhned/eval/gold/maps-conll-and-iitb-23feb"

EVALUATOR="/home/pablo/projects/ned/eval/neleval/nel"
PREFIX=/home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length

if [ -z "$1" ]; then
  echo "$0 run corpus new"
  exit 1
fi

RUN=$1
CORPUS=$2
WF=$3

COMBINED_OLD=/home/pablo/projects/ned/dhned/combine/out/combined_out_${RUN}.txt
COMBINED_NEW=/home/pablo/projects/ned/dhned/combine/newout/\
selectedobjs_${RUN}_$(echo ${CORPUS} | tr a-z A-Z)
EVALU=eval_${CORPUS}_${RUN}


if [ $CORPUS = conll ] ; then
    GOLD="/home/pablo/projects/ned/dhned/eval/gold/conll_gold_nel.mapped.norm"
    CORPUS=CoNLL
else
    GOLD="/home/pablo/projects/ned/dhned/eval/gold/iitb_gold_nel.mapped.norm"
    CORPUS=IITB
fi

# -------------------------------------------------------------------
echo "Mapping"

for linker in tagme spotlight wikiminer aida ; do
    python $MAPPER $MAP ${PREFIX}_${linker}_${CORPUS}_${RUN}
done

if [ $WF = new ] ; then
    python $MAPPER $MAP $COMBINED_NEW
fi

# -------------------------------------------------------------------
echo "Normalizing"

python $NORM ${CORPUS} ${RUN}

# -------------------------------------------------------------------
echo "Eval"

for linker in tagme spotlight wikiminer aida ; do
    echo "===== ${linker} ${RUN} ====" >> $EVALU
    $EVALUATOR evaluate -g $GOLD ${PREFIX}_${linker}_${CORPUS}_${RUN}.mapped.norm | \
    grep -P "(entity_match|strong_link_match)" - >> $EVALU 2>> evallogs
done

if [ $WF = new ] ; then
    echo "==== COMBINED ${RUN} ====" >> $EVALU
    $EVALUATOR evaluate -g $GOLD ${COMBINED_NEW}.mapped.norm | \
    grep -P "(entity_match|strong_link_match)" - >> $EVALU
fi

echo -e "\n" >> $EVALU


# Significance ------------------------------------------------------
if [ $CORPUS = CoNLL ] ; then
    lkbest=aida
else
    lkbest=wikiminer
fi

./nel significance --permute -m strong_link_match \
    -f tab \
    -g $GOLD \
    ${PREFIX}_${lkbest}_${CORPUS}_${RUN}.mapped.norm ${COMBINED_NEW}.mapped.norm \
    >> $EVALU 2> /dev/null

cat $EVALU
