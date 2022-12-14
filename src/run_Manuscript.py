#!/usr/bin/env python3

import numpy as np                                                                          # Numerical Operations
import argparse                                                                             # Parse Input Arguments
import glob                                                                                 # File Matching
import json                                                                                 # Handle JSON files
import copy                                                                                 # Copy Objects
import os                                                                                   # Interact with Operating System

if __name__ == '__main__':

    ## Input Arguments
    parser    = argparse.ArgumentParser()
    parser.add_argument('-base', '--base'   , help='Base Directory; bids and raw should be here'                                     , type=str)
    parser.add_argument('-sub' , '--subject', help='The name/label of the subject to be processed (i.e. sub-01)'                     , type=str)
    parser.add_argument('-ses' , '--session', help='The name of a specific session to be processed (i.e. ses-01)'                    , type=str)
    parser.add_argument('-std' , '--study'  , help='The path to the subject-agnostic JSON file used to configure processing settings', type=str)
    parser.add_argument('-json', '--json'   , help='The path to the subject-agnostic JSON file used to configure processing settings', type=str)
    args      = parser.parse_args()

    ## Reassign variables to command line input
    basedir   = args.base                                                                   # Base Directory  
    jsondir   = args.json                                                                   # JSON settings Directory
    subject   = args.subject                                                                # Subject
    session   = args.session                                                                # Session
    study     = args.study                                                                  # Study
    study     = 'ge-big-press-data'                                                         # Study

    ## Check for Absolute Path
    cwd       = os.getcwd()                                                                 # Current Working Directory in case Relative Paths
    if os.path.isabs(basedir) == False:                                                     # Confirm Base Dir is Absolute Path
        basedir  = '{}/{}'.format(cwd, basedir)                                             # Change to Absolute Path
    basedir   = basedir.replace('\\', '/')    

    ## Create Paths to Needed Directories
    src_dir   = '{}/src'.format(basedir)                                                    # Source  Directory
    ospreydir = '{}/osprey'.format(basedir)                                                 # Osprey  Directory
    bids_dir  = '{}/{}/bids'.format(basedir, study)                                         # BIDS    Directory
    sub_dir   = '{}/{}/bids/{}'.format(basedir, study, subject)                             # Subject Directory
    ses_dir   = '{}/{}/bids/{}/{}'.format(basedir, study, subject, session)                 # Session Directory

    print('\n')
    print('--' *20)
    print('Bids Dir: ', bids_dir)
    print('Sub  Dir: ', sub_dir )
    print('Ses  Dir: ', ses_dir )

    if os.path.exists(sub_dir) == False:                                                    # Check Participant Exists
        raise AttributeError('\nError: Subject Directory Not Found ({})'.format(sub_dir))   #

    if os.path.exists(ses_dir) == False:                                                    # Check Session Exists (Otherwise use Subject Directory)
        ses_dir = sub_dir                                                                   # 

    ## Grab T1w file
    anat_dict = {}                                                                         # Anatomical Scans Dictionary
    anat      = glob.glob(os.path.join(ses_dir, 'anat/*T1w.ni*'))                          # Find Anatomical Scans
    
    if len(anat) == 0:                                                                      # No Anatomical Scans Found
        raise ValueError('No T1w image found in {}'.format(ses_dir))                        # 
    else:                                                                                   # Found Anatomical
        anat = anat[:1]                                                                     # If more than 1 --> Take the 1st
        anat_dict['files_nii'] = anat

    ## Load json settings file
    jfile     = '{}/OSPREY_master_settings_example_data.json'.format(src_dir)
    with open(jfile, 'r') as f:
        master_settings = json.loads(f.read())

    print('\nMaster Settings:')
    print(master_settings)
    print(master_settings.keys())
    print(master_settings['UNEDITED'])
    print('\n')

    seqs      = list(master_settings.keys())                                                # Sequences Run
    seq_dict  = {}
    for ii in range(len(seqs)):                                                             # Iterate over Sequences (Unedited, MEGA, HERMES, HERCULES, etc.)
        seq_dict[seqs[ii]]              = copy.deepcopy(master_settings[seqs[ii]])
        seq_dict[seqs[ii]]['files']     = []          
        seq_dict[seqs[ii]]['files_ref'] = []   

        scans = master_settings[seqs[ii]]['prerequisites']['files']
        scans = glob.glob('{}/mrs/{}'.format(ses_dir, scans))
        scans = list(sorted(set(scans)))

        refs  = master_settings[seqs[ii]]['prerequisites']['files_ref']
        refs  = glob.glob('{}/mrs/{}'.format(ses_dir, refs))
        refs  = list(sorted(set(refs)))

        jsons = []
        for jj in range(len(scans)):                                                        # Iterate over Scans
            json_ = scans[jj].replace('.nii.gz', '.json')                                   # Replace nii extension with json 
            jsons.append(json_)

            print(' ')
            print('run-{:02d} {}'.format(jj, scans[jj]))
            print('run-{:02d} {}'.format(jj, refs[ jj]))
            print('run-{:02d} {}'.format(jj, jsons[jj]))
            print(' ')       

            seq_dict[seqs[ii]]['files'].append(    scans[jj])                               # Match Runs Scan
            seq_dict[seqs[ii]]['files_ref'].append(refs[ jj])                               # Match Runs Reference

        del seq_dict[seqs[ii]]['prerequisites']
    
    print(seq_dict['UNEDITED'])

    #Save settings to output directory
    json_out   = '{}/{}_{}_osprey_job.json'.format(ses_dir, subject, session)               # Osprey Job JSON Path
    with open(json_out, 'w') as f:                                                          # Osprey Job Write 
        seq_dict_ = json.dumps(seq_dict, indent = 4)                                        # Convert Dictionary to JSON
        f.write(seq_dict_)                                                                  # Write JSON

        # for temp_combo in file_combos:
        #     print('Temp Combo: ', temp_combo)
        #     # run_processing(settings_dict            = temp_sequence_dict, 
        #     #                mrs_files_dict           = temp_combo, 
        #     #                anat_files_dict          = anat_dict, 
        #     #                derivs_folder_path       = output_dir,
        #     #                participant_label        = temp_participant, 
        #     #                session_partial_path     = temp_session, 
        #     #                sequence                 = temp_sequence, 
        #     #                index                    = index,
        #     #                compiled_executable_path = compiled_executable_path, 
        #     #                mcr_path                 = mcr_path)
        #     index += 1
    
    os.system(compiled_executable_path + ' ' + mcr_path + ' ' + json_output_path)

    print(' ')
    print('--' *20)
