#!/bin/sh

CORPUS=$1
RUN1=$2
RUN2=$3

USAGE="\nUsage: $0 [conll|iitb|aquaint|msnbc] run1 run2\n"
if [ -z "$1" ] ; then
  echo $USAGE
  exit 1
fi

if [ "$#" -ne 3 ] ; then
  echo $USAGE
  exit 2
fi

if [ $CORPUS = conll ]; then
  for x in tagme spotlight wikiminer ; do
    echo -e "\n************ ${x} ************\n"
    diff -y /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${x}_CoNLL_${RUN1}.mapped \
            /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${x}_CoNLL_${RUN2}.mapped \
            | grep -P "[<>|]" -
  done
elif [ $CORPUS = msnbc ] ; then
  for x in tagme spotlight wikiminer ; do
    echo -e "\n************ ${x} ************\n"
    diff -y /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${x}_MSNBC_${RUN1}.mapped /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${x}_MSNBC_${RUN2}.mapped | grep -P "[<>|]" -
  done
elif [ $CORPUS = iitb ] ; then
  for y in tagme aida wikiminer ; do
    echo -e "\n************ ${y} ************\n"
    diff -y /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${y}_IITB_${RUN1}.mapped /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${y}_IITB_${RUN2}.mapped | grep -P "[<>|]" -
  done
elif [ $CORPUS = aquaint ] ; then
  for x in tagme spotlight wikiminer ; do
    echo -e "\n************ ${x} ************\n"
    diff -y /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${x}_AQUAINT_${RUN1}.mapped /home/pablo/projects/ned/dhned/combine/newout/indiv_wf_length_${x}_AQUAINT_${RUN2}.mapped | grep -P "[<>|]" -
  done
fi
