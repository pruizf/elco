#!/bin/sh

RUN=$1
CORPUS=$2

if [ -z "$1" ] ; then
  echo -e "\nUsage: $0 [run_nbr] [conll|iitb] [previous_run]?"
  echo -e "If specify previous_run, the mapped results are compared\n"
  exit 1
fi

# evalall maps and evaluates
#./evalall.sh $RUN $CORPUS new 2> /dev/null
./evalonemap.sh $RUN $CORPUS new 2> /dev/null
#./evalnorm.sh $RUN $CORPUS new 2> /dev/null

if [ $CORPUS = "conll" ] ; then
  CORPUSRE=CoNLL
elif [ $CORPUS = "iitb" ] ; then
  CORPUSRE=IITB
elif [ $CORPUS = "aquaint" ] ; then
  CORPUSRE=AQUAINT
elif [ $CORPUS = "msnbc" ] ; then
  CORPUSRE=MSNBC
fi

# verify no overlaps
for svc in tagme spotlight aida wikiminer babelfy combined; do
  python /home/pablo/projects/ned/dhned/scripts/verify_no_overlaps.py $svc $CORPUSRE $RUN
done

if [ ! -z "$3" ] ; then
  PREVIOUS=$3
  ./diffmapped.sh $CORPUS $RUN $PREVIOUS
fi
