# TubeToWell-COVID19

## Installation Instructions for Windows
1. Install Anaconda (tested on version 4.8.3) or miniconda for python 3.7, make sure to add to PATH
2. Make anaconda environment:
        Open up anaconda prompt and type: `conda create -n WellLit python=3.7.6`
3. Activate the environment with `conda activate WellLit`
4. Install dependencies:<br/>
        `conda install matplotlib==3.1.3`<br/>
        `conda install -c conda-forge kivy`<br/>
        `pip install kivy-garden`<br/>
        `garden install graph`<br/>
        `garden install matplotlib`<br/>
5. Clone this repo https://github.com/czbiohub/WellLit_to_WellLit.git


## Class Structure


GUI level:

    Well2WellWidget: GUI wrapper for WelltoWell
     * connects buttons to welltowell functions
     * displays two WellPlots to light up plates
    
    WellPlot: GUI wrapper for PlateLighting
     * Updates lighting on changes to Wells in PlateLighting
     
    Popups for LoadDialog, ErrorMessage, PlateChange


Model Classes: 

    WelltoWell: 
       * Loads a csv file into a pandas DataFrame, checking for duplicates or invalid Well labels
       * Parses a validated DataFrame into a TransferProtocol, PlateTransfer, Transfers
       * Updates Transfers on functions connected to user actions, i.e. next, skipped, failedm, assigns unique ids
       * Writes Transfers to transferlog.csv
        
        
        User-facing functions:
            next, skip, failed - marks transfers 
        
        Internal functions:
            checkDuplicatesSource
            checkDuplicatesTarget
            parseDataframe
        
        Objects
             2 x PlateLighting
                 96 x Well
             1 x TransferProtocol
                 N x PlateTransfer
                    M x Transfer


    TransferProtocol:
       * Owns a number of PlateTransfers
       * Orders plates and transfers into a sequence that can be iterated through with next, back
       * Marks plates as completed 
        
    PlateTransfer:
       * Owns a number of Transfers
        
    Transfer:
       * dict-like object with the following fields:
            source_plate, source_well, dest_plate, dest_well, status, timestamp, id, updated
       *     
             status = None
       * When status is assigned by Well2Well user action, timestamp is generated 
        

'''