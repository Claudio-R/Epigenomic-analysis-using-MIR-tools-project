# Python Scripts

This folders contains auxiliary scripts written in python. 
In particular, _json_creator.py_ and _peaks_parser.py_ are used to parse the data into a proper format to be fed to _SonicIGV_.

## json_creator.py
This script is used to create _epigenome.js_ and _index.js_ in the folder _js/resources/_.
The first file contains a json object coolecting the data available, while the second contains a json object collecting the initial configuration of each available sonification module.

## peaks_parser.py
This script has been used to collect the data for each chromosome in a dedicated folder.