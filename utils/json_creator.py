# Creata a JSON file with the data from the binary database for chr1 and another JSON file
# containing a list of the available sonification procedures.

# If you need the numpy arrays in the /data/ folder contact me or Luca Nanni

import numpy as np
import json

# Narrow-peaks
# H3K4me3 = np.load('../data/Binary/chr1/H3K4me3.npy')
# H3K9me3 = np.load('../data/Binary/chr1/H3K9me3.npy')
# H3K27ac = np.load('../data/Binary/chr1/H3K27ac.npy')
# Broad-peaks
# H3K27me3 = np.load('../data/Binary/chr1/H3K27me3.npy')
# H3K36me3 = np.load('../data/Binary/chr1/H3K36me3.npy')
# H3K79me2 = np.load('../data/Binary/chr1/H3K79me2.npy')

# f = open("../js/resources/epigenomes.js", "w")
# f.write("var epigenomes = ")
# f.close()

# # "url_track" is the url to the track to be loaded by the IGV browser
# # "name" is the name of the signal
# # "binary_data" is the binary signal to be used in the "RAW DATA SONIFICATION" procedure  

# json.dump(
#     [
#         {
#             "chr": "chr1",
#             "histones": [
#                 {
#                     "name": "H3K4me3",
#                     "url_track": "js/resources/chr1/chr1_GM12878_H3K4me3_ENCFF295GNH.narrowPeak",
#                     "binary_data": H3K4me3.tolist()
#                 },
#                 {
#                     "name": "H3K9me3",
#                     "url_track": "js/resources/chr1/chr1_GM12878_H3K9me3_ENCFF682WIQ.narrowPeak",
#                     "binary_data": H3K9me3.tolist()
#                 },
#                 {
#                     "name": "H3K27ac",
#                     "url_track": "js/resources/chr1/chr1_GM12878_H3K27ac_ENCFF816AHV.narrowPeak",
#                     "binary_data": H3K27ac.tolist()
#                 }, 
#                 {
#                     "name": "H3K27me3",
#                     "url_track": "js/resources/chr1/chr1_GM12878_H3K27me3_ENCFF001SUI.broadPeak",
#                     "binary_data": H3K27me3.tolist()
#                 },
#                 {
#                     "name": "H3K36me3",
#                     "url_track": "js/resources/chr1/chr1_GM12878_H3K36me3_ENCFF001SUJ.broadPeak",
#                     "binary_data": H3K36me3.tolist()
#                 },
#                 {
#                     "name": "H3K79me2",
#                     "url_track": "js/resources/chr1/chr1_GM12878_H3K79me2_ENCFF001SUN.broadPeak",
#                     "binary_data": H3K79me2.tolist()
#                 }
#             ]
#         }
#     ], open("../js/resources/epigenomes.js", "a")
# )

# f = open("../js/resources/epigenomes.js", "a")
# f.write("; export default epigenomes;")
# f.close()

f = open("../js/resources/index.js", "w")
f.write("var index = ")
f.close()

json.dump(
[
    {
        "chr": "chr1",
        "sonifications": [
            {
                "type": "Raw Data Sonification",
                "formatted_name": "raw-data-sonification",
                "init_params": [
                    { 
                        "name": "Gain", 
                        "value": 0.5, 
                        "min": 0.0, 
                        "max": 1.0, 
                        "step": 0.001 
                    }, 
                    { 
                        "name": "Frequency", 
                        "value": 250.0, 
                        "min": 50.0, 
                        "max": 500.0, 
                        "step": 1.0 
                    }, 
                    { 
                        "name": "Detune", 
                        "value": 0.0, 
                        "min": 0.0, 
                        "max": 0.20, 
                        "step": 0.01 
                    },
                    { 
                        "name": "Stereo Width", 
                        "value": 0.5, 
                        "min": 0.01, 
                        "max": 1.0, 
                        "step": 0.01 
                    },
                    {
                        "name": "Attack",
                        "value": 0.1,
                        "min": 0.01,
                        "max": 0.5,
                        "step": 0.001
                    },
                    {
                        "name": "Decay",
                        "value": 0.1,
                        "min": 0.01,
                        "max": 0.5,
                        "step": 0.001
                    },
                    {
                        "name": "Sustain",
                        "value": 0.1,
                        "min": 0.01,
                        "max": 0.5,
                        "step": 0.001
                    },
                    {
                        "name": "Release",
                        "value": 0.1,
                        "min": 0.01,
                        "max": 0.5,
                        "step": 0.001
                    },
                ]
            },
            {
                "type":"Example Sonification",
                "formatted_name": "example-sonification",
                "processor": "js/audioProcessors/ExampleSonification.js",
                "init_params": [
                    { 
                        "name": "Volume",
                        "value": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1
                    },
                    { 
                        "name": "Pitch",
                        "value": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1
                    },
                    { 
                        "name": "Duration",
                        "value": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1
                    }
                ]
            }
        ]
    }
]
, open("../js/resources/index.js", "a")
)

f = open("../js/resources/index.js", "a")
f.write("; export default index;")
f.close()
