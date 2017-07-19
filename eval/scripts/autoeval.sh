#!/bin/sh

# changes corpus name in config and runs app

runid=$(cat /home/pablo/projects/ned/dhned/runid)
echo "Starting at $runid"

startnbr=$[$runid - 1] # increment before use it in loop

for corpus in CONLL IITB MSNBC AQUAINT ; do
  lowc=$(echo $corpus | tr A-Z a-z)
  # modify config and run app
  perl -pi.bak -e "s/chosen_corpus = CorpusNames\..+/chosen_corpus = CorpusNames.$corpus/" \
     /home/pablo/projects/ned/dhned/config/config.py
  python /home/pablo/projects/ned/dhned/combine/newcomb3.py
  # maptest calls mapping and tests significance on mapped results
  ./maptest.sh "$((startnbr=startnbr+1))" $lowc
  echo "Run $startnbr $corpus"
done
