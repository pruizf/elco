The application consists of clients to call Entity Linking services (EL) in English, and modules to operate on the results. Implements the Entity Linking System Combination described in our [\*SEM 2015 paper](http://aclweb.org/anthology/S/S15/S15-1025.pdf).

The EL services currently supported are:

 - [TagMe](http://tagme.di.unipi.it/)
 - [DBpedia Spotlight](https://github.com/dbpedia-spotlight/dbpedia-spotlight/wiki)
 - ~~[Wikipedia Miner](http://wikipedia-miner.cms.waikato.ac.nz/)~~ (public instance no longer accessible)
 - [AIDA](http://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/yago-naga/aida/): both installed [locally](https://github.com/yago-naga/aida) and in the public [web service](http://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/yago-naga/aida/webservice/)
 - [Babelfy](http://babelfy.org/)

Requirements
------------

 - Python 2.7
 - lxml
 - MySQL-python (aka [MySQLdb](https://pypi.python.org/pypi/MySQL-python/1.2.3))
 - nltk
 - pyspotlight
 - requests

To call TagMe and Babelfy, you need to request a key:  [Tagme](http://tagme.di.unipi.it/tagme_help.html), [Babelfy](http://babelnet.org/register). The application's config module has variables to enter the keys. 

Modules
-------

 - **analysis**: Parses client responses. Computes entity-cooccurrence tables. 
 - **clients**: Clients to call the services
 - **config**: Configuration
 - **main**: Example how to use. Creates runners and calls them for each service
 - **model**: Data types and some methods for them
 - **readers**: To preprocess input before calling a client
 - **runners**: Classes here use a reader, client and writer to create an annotation workflow
 - **utils**: General tools useful for several modules 
 - **writers**: To postprocess the annotations and output them (to a file etc)

Usage
-----
 - activate the services to call in config.py
 - call main.py 
    
        usage: App to work with Entity Linking [-h] [-i MYINPUT] [-o MYOUT]
                                           [-s MYSKIPLIST] [-c CORPUS_NAME]
    
        optional arguments:
          -h, --help            show this help message and exit
          -i MYINPUT, --input MYINPUT
                                Input file, directory or text. A default can be set in
                                config.py (default: /path/to/some/default/input)
          -o MYOUT, --output MYOUT
                                Output file or files. Default names are created 
                                dynamically by code in writers.py module (default: None)
          -r MYOUTRESPS, --resp_output MYOUTRESPS
                                Output directory for client responses. A default is
                                created dynamically by code in writers.py module
                                (default: None)
          -s MYSKIPLIST, --skip_list MYSKIPLIST
                                File with filenames to skip (default:
                                /path/to/some/default/list)
          -c CORPUS_NAME, --corpus CORPUS_NAME
                                Name of the corpus (for output files etc.). A default
                                can be set in config.py (default: SOME_DEFAULT_NAME)

