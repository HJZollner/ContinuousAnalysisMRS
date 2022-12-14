
__author__  = 'Aaron Gudmundson'
__email__   = 'agudmun2@jhmi.edu'
__date__    = '2022/10/01'

from datetime import date, datetime 													# Date and Time
import pandas as pd 																	# DataFrames
import numpy as np 																		# Numerical Operations
import time as t0 																		# Timer
import subprocess 																		# Run External Commands
import argparse 																		# Input Argument Parser
import logging 																			# File Logging
import glob 																			# File Matching
import copy 																			# Safely Copy Objects
import json 																			# JSON Files
import sys 																				# System Operations
import os 																				# Operating System

def setup_log(log_name, log_file, level=logging.INFO): 									# Create new global log file
	'''
	- 1. Description:
		- Creates logfiles that will be appropriately handled globally
	
	- 2. Inputs:
		- log_name : (String) Name of the log 
		- log_file : (String) Filename of the log
		- level    : (Func  ) Level to log (default to debug and info)

	- 3. Outputs:
		- logger   : (Logger) Global log object
	'''

	formatter = logging.Formatter('(%(asctime)s) %(message)s'       , 					# Logging format (Time and Message)
								  datefmt = '%m/%d/%Y %I:%M:%S %p') 					# Date/Time Specific Formatting
	
	handler = logging.FileHandler(log_file)         									# Log Handler
	handler.setFormatter(formatter)														# Log Formatting

	logger  = logging.getLogger(log_name) 												# Instantiate Logger
	logger.setLevel(level) 																# Set Log Level
	logger.addHandler(handler) 															# Connect Handler

	return logger 																		# Return Logger Object

def create_subjdict(basedir): 															# Subject Dictionary
	''' 
	1. Description:
		- Populate dictionary with subjects (keys) and list of sessions (values) 
	       held in the raw directory. The full subdict can be used to populate 
	       a new Participant Log File to maintain which subjects have been 
	       analyzed and which are new. The combined 
	
		   Note: We could simply do a single glob.glob(*sub*ses*) statement, but 
		     I'm not going to assume there will always be a session used. This 
		     way we can Default to a ses-01 if no sessions are found.
	
	2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.

	3. Outputs:
		- subdict  : (Dict  ) Subjects and Sessions found upon running main.py. 
		- combined : (List  ) List of strings ["sub_ses"] to determine new subjects 
	'''

	subdirs    = list(sorted(set(glob.glob('{}/raw/sub*'.format(basedir)) )))			# Subject Directories
	subdict    = {} 																	# Subject Dictionary with Sessions
	combined   = [] 																	# Combined Subject and Session

	for ii in range(len(subdirs)):
		subdirs[ii] = subdirs[ii].replace('\\', '/') 									# Forward Slashes
		subject     = subdirs[ii].split('/')[-1]
		sessions    = list(sorted(set(glob.glob('{}/ses*'.format(subdirs[ii]) ))))		# Subject Directories

		subdict[subject] = [] 															# Create List of Sessions
		if len(sessions) == 0: 															# No Session Specified
			subdict[subject].append('ses-01')											# Default to ses-01
			combined.append('{}_ses-01'.format(subject, ))

		for jj in range(len(sessions)): 												# Iterate Over Sessions
			sessions[jj]     = sessions[jj].replace('\\', '/') 							# Forward Slashes
			session          = sessions[jj].split('/')[-1]								# Current Session

			subdict[subject].append(session) 											# Populate Sessions 												
			combined.append('{}_{}'.format(subject, session)) 							# Combined Subject and Session 

	return subdict, combined 															# 

def create_partfile(basedir, partfile): 												# Create Participant Log File
	'''
	1. Description
	    - Create a Participant Log File (.csv) which will maintains a list of 
	    	Subjects and Sessions that have been previously analyzed. The 
	    	Participant log file is created when new subjects or sessions are 
	    	found during main.py execution. This file can be found at the study 
	    	level where the bids and raw directories.
	
	2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.
		- partfile : (String) Participant File Path (Record of Subjects and Sessions).

	3. Outputs:
		- subdict  : Subjects and Sessions found upon running main.py. 
	'''

	study_log.info('Check     : Check Subjects/Update Study Log') 						# Study Log
	subdict,_ = create_subjdict(basedir) 												# Get Subject Dictionary 							

	df_date   = [] 																		# DataFrame Date/Time Information
	df_base   = [] 																		# DataFrame Base Directory Information
	df_subs   = [] 																		# DataFrame Subject Information
	df_sess   = [] 																		# DataFrame Session Information	

	subkeys   = list(subdict.keys()) 													# Subjects in Subject Dictionary
	for ii in range(len(subkeys)): 			 											# Iterate Over Subjects										
		for jj in range(len( subdict[subkeys[ii]] )): 									# Iterate over Sessions
			
			df_date.append(datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')) 			# Add Date/Time
			df_base.append( basedir) 													# Add Base Directory
			df_subs.append( subkeys[ii]) 												# Add Subject
			df_sess.append( subdict[subkeys[ii]][jj]) 									# Add Session

	df        = pd.DataFrame({'Date'     : df_date, 									# DataFrame Date/Time
							  'Directory': df_base, 									# DataFrame Base Directory
							  'Subject'  : df_subs, 									# DataFrame Subjects
							  'Session'  : df_sess})									# DataFrame Sessions

	df.to_csv(partfile) 																# DataFrame Create CSV
	study_log.info('Check     : Created Subject File') 									# Subject File

	return subdict 	 					 												# Return Newly Added

def update_partfile(basedir, partfile): 												# Update the Participant Log File
	'''
	1. Description
	    - Update the Participant Log File (.csv) which maintains a list of 
	    	Subjects and Sessions that have been previously analyzed. The 
	    	Participant log file is updated when new subjects or sessions are 
	    	found during main.py execution. This file can be found at the study 
	    	level where the bids and raw directories.
	
	2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.
		- partfile : (String) Participant File Path (Record of Subjects and Sessions).

	3. Outputs:
		- combined : List of strings ["sub_ses"] to determine new subjects 
	'''

	study_log.info('Update    : Updated Subject File') 									# Study Log 
	_,combined = create_subjdict(basedir) 												# Get Combined Subject and Session Strings from Subject Dicionary		

	df         = pd.read_csv(partfile) 													# Read in Current CSV Subject file
	df['Comb'] = df.Subject + '_' + df.Session 											# Combined Name
	df_dates   = list(df.Date.values     ) 												# Dates
	df_base    = list(df.Directory.values) 												# Directory
	df_subs    = list(df.Subject.values  ) 												# Subjects
	df_sess    = list(df.Session.values  ) 												# Sessions
	comb       = list(df.Comb.values     ) 												# Get Combined Subject and Sessions as list

	new_subs   = {} 																	# Find New Subjects

	for ii in range(len(combined)): 													# Iterate Over All Subjects
		if combined[ii] not in comb: 													# Current Subject is not in the Subject File

			subject = combined[ii].split('_')[0] 										# Get New Subject
			session = combined[ii].split('_')[1] 										# Get New Session

			df_dates.append(datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')) 			# Add Date/Time
			df_base.append( basedir) 													# Base Directory
			df_subs.append( subject) 													# Add Subject
			df_sess.append( session) 													# Add Session

			if subject not in list(new_subs.keys()): 									# Subject Not Yet included in new_subs
				new_subs[subject] = [ session ] 										# Add Subject and Session
			else: 																		# Subject Already in new_subs
				new_subs[subject].append( session ) 									# Append Session

	df        = pd.DataFrame({'Date'     : df_dates, 									# DataFrame Date/Time
							  'Directory': df_base, 									# DataFrame Base Directory
							  'Subject'  : df_subs, 									# DataFrame Subjects
							  'Session'  : df_sess})									# DataFrame Sessions

	df.to_csv(partfile) 																# DataFrame Create CSV

	study_log.info('Update    : Updated Subject File: Completed') 						# Study Log 
	return new_subs 	 					 											# Return Newly Added

def dicomsort(basedir, sub, ses, misc, success=True, debug=False):  					# Sort Subject Dicoms				
	'''
	- 1. Description:
	    - The function sorts dicoms using the 3rd party software, dicomsort.py. 
	        The dicomsort software can be found at the following link:
	          https://github.com/pieper/dicomsort

	        Note: While the dicomsort package is available as a stand-alone, 
	          we utilize the version included within bidscoiner.
	          See bidscoin function decription for more informtion.

		- Package Website Description:
			"DICOM Sort is a utility that takes a series of DICOM images stored 
			  within an arbitrary directory structure and sorts them into a 
			  directory tree based upon the value of selected DICOM fields."

	- 2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.
		- sub      : (String) Current Subject as string
		- ses      : (String) Current Subject's Session as string
		- misc     : (Dict  ) Miscellaneous Objects that specific functions may need.
		- success  : (Bool  ) Status of function call
		- debug    : (Bool  ) Debugging mode - commands are not execeuted.

	- 3. Outputs:
		- success  : (Bool  ) Status of function call where True = Success and 
							    False = Fail.
	'''

	sub_log.info('%s %s dicomsort :'         , sub, ses) 								# Subject Log - dicomsort function
	sub_log.info('%s %s dicomsort : Starting', sub, ses) 								# Subject Log - dicomsort Starting

	subdir = '{}/raw/{}/{}'.format(basedir, sub, ses) 									# Subject Directory (With Session)
	if os.path.exists(subdir) == False:													# Determine if Session Information was Given
		subdir = '{}/raw/{}'.format(basedir, sub) 										# No Session Information Provided

	script  = 'dicomsort -f {{ScanningSequence}} "{}"'.format(subdir) 					# Script to Call
	sub_log.info('%s %s dicomsort : %s', sub, ses, script) 								# Subject Log - Script to Call
	
	if debug == True: 																	# If Debug - Print to Screen
		sub_log.info('%s %s dicomsort : debugging (Command Not run)', sub, ses) 		# Subject Log - dubugging
		return success

	try: 																				# Error Handling (Note subject fails and keep executing)
		P       = subprocess.Popen(script, shell=False) 								# Run Script
		P.wait() 																		# Wait for Script Completion
	except Exception as e: 																# Error Handling
		success = False 																# Set Success

	sub_log.info('%s %s dicomsort : success = %s', sub, ses, success) 					# Subject Log - Success

	return success

def bidscoin(basedir, sub, ses, misc, success=True, debug=False): 						# Bids-ify Subject Data
	'''
	- 1. Description:
	    - The function converts raw data to bids format using bidscoin.py. 
	        The bidscoin software can be found at the following link:
	          https://github.com/Donders-Institute/bidscoin

	        Note: While the dicomsort package is available as a stand-alone, 
	          we utilize the version included within bidscoiner.
	          See bidscoin function decription for more informtion.

		- Package Website Description:
			"BIDScoin is a user friendly open-source Python application that 
			  converts ("coins") source-level (raw) neuroimaging data-sets to 
			  nifti / json / tsv data-sets that are organized according to the 
			  Brain Imaging Data Structure (BIDS) standard. Rather then depending 
			  on complex programmatic logic for source data-type identification, 
			  BIDScoin uses a mapping approach to discover the different source 
			  data types in your repository and convert them into BIDS data types. 
			  For more information, please see the software link above. Data 
			  conversions are performed within plugins, such as plugins that 
			  employ dcm2niix, spec2nii or nibabel."

	- 2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.
		- sub      : (String) Current Subject as string
		- ses      : (String) Current Subject's Session as string
		- misc     : (Dict  ) Miscellaneous Objects that specific functions may need.
		- success  : (Bool  ) Status of function call
		- debug    : (Bool  ) Debugging mode - commands are not execeuted.

	- 3. Outputs:
		- success  : (Bool  ) Status of function call where True = Success and 
							    False = Fail.
	'''

	bmap    = '{}/bids/code/bidscoin/bidsmap.yaml'.format(basedir)
	script  = 'bidscoiner -f "{}/raw" "{}/bids" -b "{}" -p {}'.format(basedir, basedir, bmap, sub) # Script to Call

	sub_log.info('%s %s bidscoin  :', sub, ses) 										# Subject Log - bidscoin function
	sub_log.info('%s %s bidscoin  : Starting', sub, ses) 								# Subject Log - bidscoin Starting
	sub_log.info('%s %s bidscoin  : bidscoiner -f $raw $bids -b $bmap -p %s', sub, ses, sub) # Subject Log - bidscoin command

	if debug == True: 																	# If Debug - Print to Screen
		sub_log.info('%s %s bidscoin  : debugging (Command Not run)', sub, ses) 		# Subject Log - Base Directory
		return success 																	# Debugging - Exit.

	try:
		P       = subprocess.Popen(script, shell=False)									# Run Script
		P.wait() 																		# Wait for Script Completion
	except Exception as e: 																# Error Handling
		success = False 																# Set Success

	sub_log.info('%s %s bidscoin  : success = %s', sub, ses, success) 					# Subject Log - Base Directory
	return success

def osprey_job(basedir, sub, ses, misc, success=True, debug=False): 					# Create Osprey Job
	'''
	- 1. Description:
	    - The function creates an osprey job file in json format.

	- 2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.
		- sub      : (String) Current Subject as string
		- ses      : (String) Current Subject's Session as string
		- misc     : (Dict  ) Miscellaneous Objects that specific functions may need.
		- success  : (Bool  ) Status of function call
		- debug    : (Bool  ) Debugging mode - commands are not execeuted.

	- 3. Outputs:
		- success  : (Bool  ) Status of function call where True = Success and 
							    False = Fail.
	'''

	sub_log.info('%s %s osprey job:'         , sub, ses) 								# Subject Log - osprey job function
	sub_log.info('%s %s osprey job: Starting', sub, ses) 								# Subject Log - osprey job Starting

	if debug == True: 																	# If Debug - Print to Screen
		sub_log.info('%s %s osprey job: debugging (Command Not run)', sub, ses) 		# Subject Log - debugging
		return success 																	# Debugging - Exit.

	backdir   = basedir.split('/')[:-1] 												# Back out of Study Directory (returns list)
	backdir   = '/'.join(backdir) 														# Recombine strings in list as Path

	src_dir   = '{}/src'.format(backdir)                                				# Source  Directory
	ospreydir = '{}/osprey'.format(backdir)                                             # Osprey  Directory
	bids_dir  = '{}/bids'.format(basedir)                                     			# BIDS    Directory
	sub_dir   = '{}/bids/{}'.format(basedir, sub)                         				# Subject Directory
	out_dir   = '{}/bids/derivatives'.format(basedir) 									# Deriv   Directory (Will add Subject/Session Below)

	if os.path.exists(out_dir) == False: 												# Derivatives not yet created
		os.mkdir(out_dir) 																# Create Derivatives

	out_dir   = '{}/{}'.format(out_dir, sub) 											# Add Subject to Output Path
	if os.path.exists(out_dir) == False: 												# Subject Directory not yet created
		os.mkdir(out_dir)  																# Create Subject Directory in Derivatives
	
	out_dir   = '{}/{}'.format(out_dir, ses)											# Add Session to Output Path
	if os.path.exists(out_dir) == False: 												# Session Directory not yet created
		os.mkdir(out_dir)  																# Create Session Directory in Derivatives/Subject

	ses_dir   = '{}/bids/{}/{}'.format(basedir, sub, ses)            	 				# Session Directory
	if os.path.exists(ses_dir) == False:                                                # Check Session Exists (Otherwise use Subject Directory)
		ses_dir = sub_dir                                                               # No Session - Use Subject Directory

	mrs_dir   = '{}/mrs'.format(ses_dir) 												# MRS Data Directory
	if os.path.exists(mrs_dir) == False: 												# Was MRS generated or a different name?
		mrs_dir = '{}/extra_data'.format(ses_dir)

	emailpath = '{}/EmailConfig.json'.format(src_dir)
	with open(emailpath, 'r') as f:	 													# Create new JSON file
		email = json.loads(f.read())
		email = email['SourceEmail']

	anat_dict = {}                                                                      # Anatomical (T1w) Scans Dictionary
	anat      = glob.glob('{}/anat/*T1w.ni*'.format(ses_dir))                       	# Find Anatomical Scans

	if len(anat) == 0:                                                                  # No Anatomical Scans Found
		sub_log.info('%s %s osprey job: No T1w image found', sub, ses) 					# Subject Log - Note Missing Anatomical 
		sub_log.info('%s %s osprey job: Sucess = False', sub, ses) 						# Subject Log - Set Success to False
		return False 																	# Return Success as False

	anat = anat[:1]                                                                 	# If more than 1 --> Take the 1st
	anat[0] = anat[0].replace('\\', '/') 												# Forward Slashes

	try:
																						## Load json settings file
		jfile  = '{}/OSPREY_master_settings.json'.format(src_dir)						# Default Filename
		with open(jfile, 'r') as f:	 													# Create new JSON file
			master_settings = json.loads(f.read()) 										# Read in Osprey JSON Template as the Settings Master Copy

		# seqs      = list(master_settings.keys())                                        # Sequences Run (Unedited, MEGA, HERMES, HERCULES, etc.)
		seq_dict  = copy.deepcopy(master_settings) 										# Dictionary with Parameters for all Sequences 
		seq_dict['files']     = []           											# Create new Key as files
		seq_dict['files_ref'] = []              										# Create new Key as files_ref

		scans = master_settings['prerequisites']['files'] 								# Scan Pattern to Match
		scans = glob.glob('{}/{}'.format(mrs_dir, scans)) 								# Grab Scan File Names
		scans = list(sorted(set(scans))) 												# Sort Scan Files

		refs  = master_settings['prerequisites']['files_ref'] 							# Ref Pattern to Match
		refs  = glob.glob('{}/{}'.format(mrs_dir, refs)) 								# Grab Ref File Names
		refs  = list(sorted(set(refs))) 												# Sort Ref Files

		jsons = []	 																	# Corresponding json file
		for ii in range(len(scans)):                                                	# Iterate over Scans
			scans[ii] = scans[ii].replace('\\', '/') 									# Maintain Forward Slashes
			refs[ ii] = refs[ ii].replace('\\', '/') 									# Maintain Forward Slashes

			json_ = copy.deepcopy(scans[ii]).replace('.nii.gz', '.json')                # Replace nii extension with json 
			jsons.append(json_) 														# Add json file to list

			sub_log.info('%s %s osprey job: run-%02d %s', sub,ses,ii+1,scans[ii].split('/')[-1]) # Subject Log - Scans
			sub_log.info('%s %s osprey job: run-%02d %s', sub,ses,ii+1,refs[ ii].split('/')[-1]) # Subject Log - Ref
			sub_log.info('%s %s osprey job: run-%02d %s', sub,ses,ii+1,jsons[ii].split('/')[-1]) # Subject Log - json

			seq_dict['files'    ].append(scans[ii])                       				# Match Runs Scan
			seq_dict['files_ref'].append(refs[ ii])                       				# Match Runs Reference

		seq_dict[        'files_nii'] = anat 											# Add in Anatomical
		seq_dict[     'outputFolder'] = [out_dir] 										# Add Output Directory
		seq_dict[     'mailtoConfig'] = emailpath 										# Automatic emailing
		seq_dict[ 'mailtoRecipients'] = [email] 										# Recipients

		del seq_dict['prerequisites'] 													# Remove File Match Key

		json_out   = '{}/{}_{}_osprey_job.json'.format(ses_dir, sub, ses)           	# Osprey Subject-specific Job File
		sub_log.info('%s %s osprey job: %s', sub, ses, json_out) 						# Subject Log - Osprey job json file path

		with open(json_out, 'w') as f:                                                  # Osprey Job Write 
			seq_dict_ = json.dumps(seq_dict, indent = 4)                                # Convert Dictionary to JSON
			f.write(seq_dict_)                                                          # Write JSON
	
	except Exception as e: 																# Error Encountered
		sub_log.info('%s %s Error: %s', sub, ses, e) 									# Subject Log - Success
		success = False		 															# Return False

	sub_log.info('%s %s osprey job: success = %s', sub, ses, success) 					# Subject Log - Success

	return success 																		# True = Success; False = Failed

def osprey_run(basedir, sub, ses, misc, success=True, debug=False): 					# Create Osprey Job
	'''
	- 1. Description:
	    - The function calls osprey to perform preprocessing and linear 
	        combination modeling of MRS data. The osprey software package
	        can be found at the following link: 
	        https://github.com/schorschinho/osprey

	        Note: While the osprey package is available as a stand-alone, 
	          we utilize the compiled matlab version. For this, matlab Runtime
	          must be installed.

		- Package Website Description:
			"Osprey is an all-in-one software suite for state-of-the art 
			  processing and quantitative analysis of in-vivo magnetic 
			  resonance spectroscopy (MRS) data."

	- 2. Inputs:
		- basedir  : (String) Base Directory where raw and bids can be found.
		- sub      : (String) Current Subject as string
		- ses      : (String) Current Subject's Session as string
		- misc     : (Dict  ) Miscellaneous Objects that specific functions may need.
		- success  : (Bool  ) Status of function call
		- debug    : (Bool  ) Debugging mode - commands are not execeuted.

	- 3. Outputs:
		- success  : (Bool  ) Status of function call where True = Success and 
							    False = Fail.
	'''

	sub_log.info('%s %s osprey job:'         , sub, ses) 								# Subject Log - osprey job function
	sub_log.info('%s %s osprey job: Starting', sub, ses) 								# Subject Log - osprey job Starting


	sub_dir   = '{}/bids/{}'.format(basedir, sub)                         				# Subject Directory
	ses_dir   = '{}/bids/{}/{}'.format(basedir, sub, ses)                         		# Subject/Session Directory
	if os.path.exists(ses_dir) == False:                                                # Check Session Exists (Otherwise use Subject Directory)
		ses_dir = sub_dir                                                               # No Session - Use Subject Directory

	jobfile   = '{}/{}_{}_osprey_job.json'.format(ses_dir, sub, ses) 					# Osprey Job File
	script    = 'OspreyCMD "{}"'.format(jobfile) 										# Osprey run script
	sub_log.info('%s %s osprey run: %s', sub, ses, script) 								# Subject Log - debugging

	if debug == True: 																	# If Debug - Print to Screen
		sub_log.info('%s %s osprey run: debugging (Command Not run)', sub, ses) 		# Subject Log - debugging
		return success 																	# Debugging - Exit.

	my_env    = os.environ.copy()
	my_env['PATH'] ='C:\\Program Files\\MATLAB\\MATLAB_Runtime\\v912;'     +my_env['PATH']  # Add Matlab Runtime to Path
	my_env['PATH'] ='C:\\Program Files\\MATLAB\\MATLAB_Runtime\\v912\\bin;' +my_env['PATH'] # Add Matlab Runtime's bin to Path
	my_env['PATH'] ='C:\\Program Files\\MATLAB\\MATLAB_Runtime\\v912\\runtime\\win64;' +my_env['PATH'] # Add Matlab Runtime's bin to Path

	try:
		P       = subprocess.Popen(script, cwd=misc['osp_path'], shell=True, env=my_env)# Run Script
		P.wait() 																		# Wait for Script Completion
	except Exception as e: 																# Error Handling
		success = False 																# Set Success

	sub_log.info('%s %s osprey run: success = %s', sub, ses, success) 					# Subject Log - Base Directory
	return success

if __name__ == '__main__':

	print(' ')    																		# Watchman Log - Space Between Entries
	print('-- '*30) 																	# Watchman Log - Dashed Line Between Entries

	parser     = argparse.ArgumentParser() 												# Input Argument Parser
	parser.add_argument('-b', '--base'  , help='Base   Directory: where /raw and /bids are located'  , type=str) # Base Directory
	parser.add_argument('-o', '--osprey', help='Osprey Directory: where executable osprey is located', type=str) # Osprey Directory
	args       = parser.parse_args() 													# Input Arguments

	now        =  lambda: datetime.now().strftime('%m/%d/%Y %I:%M:%S %p') 				# Watchman Log - Shorthand function to get Date/Time
	print('({})'.format(now()))  														# Watchman Log - Date/Time

	basedir    = args.base 																# Base Directory
	basedir    = basedir.replace('\\', '/') 											# Use Forward Slash on all Operating Systems
	study      = basedir.split('/')[-1] 												# Study Name
	rawdir     = '{}/raw'.format(basedir) 												# Base Directory
	
	misc       = {} 																	# Miscellaneous objects that we might need later....
	misc['osp_path'] = args.osprey 														# Osprey Path

	print('({}) Study Log: {}/{}.log'.format(now(), basedir, study)) 					# Watchman Log - Note Where Subject File Will be Found
	study_log  = setup_log(study, '{}/{}.log'.format(basedir, study)) 					# Study Log File
	study_log.info(' ') 																# Study Log - 
	study_log.info('--'*30) 															# Study Log - Dashed Line to Separate Entries
	study_log.info('Base Dir: %s', basedir) 											# Study Log - Base Directory
	study_log.info('Osp  Dir: %s', args.osprey) 										# Study Log - Osprey Directory
	
	partfile   = '{}/raw/participant_log.csv'.format(basedir)	 						# Maintains List of All Participants (Determines if Analyzed)
	if os.path.exists(partfile) == False: 												# Participant File Does Not Exist
		subs   = create_partfile(basedir, partfile) 									# Create Participant File and get New subjects for Analysis 
	else: 																				# Participant File Exists
		subs   = update_partfile(basedir, partfile) 									# Update Participant File and get New subjects for Analysis

	study_log.info('Waiting for %2d Subject(s) to Upload....', len(list(subs.keys())))  # Study Log - Base Directory
	if len(list(subs.keys())) > 0: 														# Found Subjects
		t0.sleep(10)  		    														# Build in latency to ensure all files finished transferring
		t0.sleep(60*len(list(subs.keys()))) 											# Add Additional Minute per Subject
	study_log.info('Continuing....') 													# Study Log - Base Directory

										 												# This can be moved to a Config File
	commands  = {'dicomsort' : dicomsort , 												# Sort Dicoms
				 'bidscoin'  : bidscoin  , 												# Bids-ify
				 'osprey_job': osprey_job, 												# Create Osprey Job File
				 'osprey_run': osprey_run} 												# Run Osprey
	commands_ = list(commands.keys()) 													# Current Command List

	success   = 1 																		# Check For Errors - Success = True
	nsub_keys = list(subs.keys()) 														# New Subject Dictionary Keys

	for ii in range(len(nsub_keys)): 													# Iterate over Subjects
		sub   = nsub_keys[ii] 															# Current Subject
		subdir= '{}/{}'.format(rawdir, sub) 											# Subject Directory (No Session)

		for jj in range(len( subs[sub] )): 												# Iterate over Sessions
			ses     = subs[sub][jj] 													# Current Session
			comb    = '{}_{}'.format(sub, ses) 											# Subject and Session Combined - Helps Determine New Sessions within Previous Subjects

			print('({}) Subject Log: {}/{}.log'.format(now(), subdir, comb)) 			# Watchman Log - Note Where Subject File Will be Found

			sub_log = setup_log(comb, '{}/{}.log'.format(subdir, comb)) 				# Subject Log - Create File
			sub_log.info(' ') 															# Subject Log - Space Between Entries
			sub_log.info('--'*30) 														# Subject Log - Dashed Line Between Entries
			sub_log.info('%s %s Base Dir  : %s', sub, ses, basedir) 					# Subject Log - Base Directory

			for jj in range(len(commands_)): 											# Iterate Over Commands
				if success == True:				 										# Ensure Successful Completion of Previous
					success = commands[commands_[jj]](basedir, sub, ses, misc)			# Run Current Command

				else:
					sub_log.info('%s %s Skipped ** ', sub, commands_[jj]) 				# Subject Log - Failed Previous Steps (skipping)

			sub_log.info('Exiting....') 												# Subject Log - Exiting
			sub_log.info('--'*30) 														# Subject Log - Dashed Line to Separate Entries

	study_log.info('Exiting....') 														# Study Log - Exiting
	study_log.info('--'*30) 															# Study Log - Dashed Line to Separate Entries

	print('-- '*30) 																	# Watchman Log - Dashed Line Between Entries
	print(' ')    																		# Watchman Log - Space Between Entries
