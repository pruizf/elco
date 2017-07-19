# repro table 1 and 2

MAPPEDREFDIR=/home/pablo/projects/ned/pb/srw/data_local/reference/mapped
MAPPEDSYSDIR=/home/pablo/projects/ned/pb/srw/data_local/system_results/mapped

for measure in sam ent ; do 
  if [ $measure = sam ] ; then 
    lookfor='strong_link_match'
  else lookfor='entity_match' 
  fi
  for corpus in aidaconllb iitb msnbc aquaint ; do 
    echo -e "\n** ${corpus} [${measure}] **"
    for annotator in tagme spotlight wikiminer aida babelfy combined ; do
        echo "== ${annotator} =="
        ./nel evaluate -g ${MAPPEDREFDIR}/${corpus}-gold.mapped \
         ${MAPPEDSYSDIR}/${corpus}-${annotator}-${measure}.mapped 2> /dev/null \
         | grep $lookfor
    done
  done
done

