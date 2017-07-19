#!/bin/sh

MAPPER=/home/pablo/projects/ned/dhned/scripts/apply_wp_mapping.py

EVALUATOR="/home/pablo/projects/ned/eval/neleval/nel"
PREFIX=/home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length
SUFFIXOLD=mapped
SUFFIX=mapped2

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
EVALU=eval_${CORPUS}_${RUN}_REDO


if [ $CORPUS = conll ] ; then
    GOLD="/home/pablo/projects/ned/dhned/eval/gold/conll_gold_nel.${SUFFIXOLD}"
    MAP="/home/pablo/projects/ned/dhned/eval/gold/maps-conll-and-iitb-23feb"
    CORPUS=CoNLL
elif [ $CORPUS = aquaint ]; then
    GOLD="/home/pablo/projects/ned/dhned/eval/gold/aquaint_gold_nel.${SUFFIXOLD}"
    MAP="/home/pablo/projects/ned/dhned/eval/gold/map-msnbc-2mars"
    CORPUS=AQUAINT
elif [ $CORPUS = msnbc ]; then
    GOLD="/home/pablo/projects/ned/dhned/eval/gold/msnbc_gold_nel.${SUFFIXOLD}"
    MAP="/home/pablo/projects/ned/dhned/eval/gold/map-acquaint-2mars"
    CORPUS=MSNBC
else
    GOLD="/home/pablo/projects/ned/dhned/eval/gold/iitb_gold_nel.${SUFFIXOLD}"
    MAP="/home/pablo/projects/ned/dhned/eval/gold/maps-conll-and-iitb-23feb"
    CORPUS=IITB
fi

echo "Mapping"

for linker in tagme spotlight wikiminer aida ; do
    python $MAPPER $MAP ${PREFIX}_${linker}_${CORPUS}_${RUN}
done

if [ -f ${PREFIX}_babelfy_${CORPUS}_${RUN} ] ; then
    python $MAPPER $MAP ${PREFIX}_babelfy_${CORPUS}_${RUN}
fi

if [ $WF = new ] ; then
    python $MAPPER $MAP $COMBINED_NEW
fi

echo "Eval"

echo "MATCHMODE:" $(grep -Po 'tmatchmode[^#]+#' \
      /home/pablo/projects/ned/dhned/config/config.py)

echo "NEW_RANK_CORR:" $(grep -P'new_rank_corr' \
      /home/pablo/projects/ned/dhned/config/config.py)

for linker in tagme spotlight wikiminer aida babelfy; do
    echo "===== ${linker} ${RUN} ====" >> $EVALU
    $EVALUATOR evaluate -g $GOLD ${PREFIX}_${linker}_${CORPUS}_${RUN}.${SUFFIX} | \
    grep -P "(entity_match|strong_link_match)" - >> $EVALU #2>> evallogs
done

if [ $WF = new ] ; then
    echo "==== COMBINED ${RUN} ====" >> $EVALU
    $EVALUATOR evaluate -g $GOLD ${COMBINED_NEW}.${SUFFIX} | \
    grep -P "(entity_match|strong_link_match)" - >> $EVALU
fi

echo -e "\n" >> $EVALU

#cat $EVALU


# Some config infos -------------------------------------------------
echo "MATCHMODE:" $(grep -Po 'tmatchmode[^#]+#' \
      /home/pablo/projects/ned/dhned/config/config.py) >> $EVALU

echo "NEW_RANK_CORR:" $(grep -P 'new_rank_corr' \
      /home/pablo/projects/ned/dhned/config/config.py)


# Significance ------------------------------------------------------
if [ $CORPUS = CoNLL ] ; then
    lkbest=aida
elif [ $CORPUS  = MSNBC ] ; then
    lkbest=tagme
elif [ $CORPUS  = AQUAINT ] ; then
    lkbest=tagme
elif [ $CORPUS  = IITB ] ; then
    lkbest=wikiminer
fi

echo "SIG: STRONG_LINK_MATCH" >> $EVALU
./nel significance --permute -m strong_link_match \
    -f tab \
    -g $GOLD \
    ${PREFIX}_${lkbest}_${CORPUS}_${RUN}.${SUFFIX} ${COMBINED_NEW}.${SUFFIX} \
    >> $EVALU 2> /dev/null

echo "SIG: ENTITY_MATCH" >> $EVALU
./nel significance --permute -m entity_match \
    -f tab \
    -g $GOLD \
    ${PREFIX}_${lkbest}_${CORPUS}_${RUN}.${SUFFIX} ${COMBINED_NEW}.${SUFFIX} \
    >> $EVALU 2> /dev/null

cat $EVALU

# Copy the config and data
echo "Copying config"

echo "\n\n#### CONFIG STARTS ####\n\n" >> $EVALU
cat /home/pablo/projects/ned/dhned/config/config.py >> $EVALU

datanewdir=/home/pablo/bkp_results/data_${RUN}_${CORPUS}_REDO
mkdir "$datanewdir"

cp /home/pablo/projects/ned/dhned/config/config.py \
   $datanewdir/config_${RUN}.py

echo "Copying data"
cp /home/pablo/projects/ned/dhned/data/*p "$datanewdir/."

cd $dhned
git diff >> $datanewdir/git_diff_${CORPUS}_${RUN}.txt