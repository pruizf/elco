#!/bin/bash

# Significance between two runs

USAGE="$0 run service corpus measure\nService all in caps"

RUN=$1
SERVICE=$2
CORPUS=$3
MEASURE=$4


GOLDPREF=/home/pablo/projects/ned/dhned/eval/gold
SYSPREF=/home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length
COMBINEDPREF=/home/pablo/projects/ned/dhned/combine/newout/selectedobjs

if [ -z "$1" ] ; then
    echo -e $USAGE ; exit 2
fi

echo -e "SIG ${MEASURE}\n"

# capitalization not consistent in filenames
CORPUSLO=$(echo ${CORPUS} | tr A-Z a-z) # goldenset
CORPUSRE=$(echo ${CORPUS} | tr a-z A-Z) # combined results

./nel significance --permute -m $MEASURE -f tab \
    -g ${GOLDPREF}/${CORPUSLO}_gold_nel.mapped \
    ${SYSPREF}_${SERVICE}_${CORPUS}_${RUN}.mapped4 \
    ${COMBINEDPREF}_${RUN}_${CORPUSRE}.mapped4

