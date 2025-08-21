#!/usr/bin/python3

# A script attempting to act as a universal BIDS directory uploader to an XNAT instance

import xnat
import getpass
import os

# Setup details
url = "https://xnat.mq.edu.au:443"

# Get the following info by prompting user input
project_id = input("Project ID (e.g. ME000): ")
bids_directory = input("Path to your BIDS directory (e.g. D:\\xnat_bids_upload\\BIDS_conversion\\BIDS\\BIDS-2022-14\\ME000): ")
user = input("XNAT Username: ")
password = getpass.getpass(prompt="XNAT Password: ")

# Full BIDS datatypes = ["func", "dwi", "fmap", "anat", "meg", "eeg", "ieeg", "beh"]
# Currently supported datatypes
bids_datatypes = ["anat", "meg", "dwi"]

# Used for checking file types
mri_suffixes = (".nii", ".nii.gz")
meg_suffixes = (".con", ".mrk") #".fif" #


# Check if any subject directories exist
def check_subjects_exist():
    has_subjects = False
    for item in os.listdir(bids_directory):
        if os.path.isdir(os.path.join(bids_directory, item)):
            if item.startswith("sub"):
                has_subjects = True
    if not has_subjects:
        print("No subject folders found - check the bids_directory path is correct")
        raise SystemExit


# Upload project level resources (anything that's not a subject folder)
def upload_project_level_resources():
    # Check if a BIDS resource folder exists - create one if not
    try:
        resource = project.resources["BIDS"]
    except Exception:
        resource = session.classes.ResourceCatalog(parent=project, label="BIDS")
    # If they are files (as opposed to directories) then upload them to the BIDS resource folder
    if os.path.isfile(os.path.join(bids_directory, file)):
        try:
            resource.upload("{}/{}".format(bids_directory, file), file, overwrite=True)
        except Exception:
            print("A - Failed to upload {}".format(file))
    # Check if they are directories (as opposed to files)
    if os.path.isdir(os.path.join(bids_directory, file)):
        # Check the directories are not subjects
        if not file.startswith("sub"):
            # Check if a folder for the directory already exists - create one if not
            try:
                resource = project.resources[file]
            except Exception:
                resource = session.classes.ResourceCatalog(parent=project, label=file)
            # Upload the directory to the resource folder
            try:
                print("uploading project level resource: " + file)
                resource.upload_dir("{}/{}".format(bids_directory, file), overwrite=True, method="per_file")
            except Exception:
                print("B - Failed to upload {}".format(file))


# Create XNAT subjects based on the subject folders found in the bids_directory
def create_subjects():
    # Check if they are directories (as opposed to files)
    if os.path.isdir(os.path.join(bids_directory, file)):
        # Check the directories are subjects
        if file.startswith("sub"):
            # Check if subject exists - create one if not
            current_subject = ""
            for item in project.subjects.values():
                if item.label == file:
                    current_subject = item
            if current_subject == "":
                session.classes.SubjectData(parent=project, label=file)


# Upload subject level resources (anything that's not expected bids datatype folders)
def upload_subject_level_resources():
    # Check if it is a directory
    if os.path.isdir(os.path.join(bids_directory, file, sub_file)):
        # If not a bids expected folder, upload to subject level resources
        if sub_file not in bids_datatypes and "ses" not in sub_file:
            # Check if a folder for the directory already exists - create one if not
            try:
                resource = subject.resources[sub_file]
            except Exception:
                resource = session.classes.ResourceCatalog(parent=subject, label=sub_file)
            # Upload the directory to the resource folder
            try:
                resource.upload_dir("{}/{}/{}".format(bids_directory, file, sub_file), overwrite=True, method="per_file")
            except Exception:
                print("C - Failed to upload {}".format(sub_file))
    # If it is a file then upload to subject BIDS resource folder
    if os.path.isfile(os.path.join(bids_directory, file, sub_file)):
        # Check if a subject BIDS resource folder exists at the subject level - create one if not
        try:
            resource = subject.resources["BIDS"]
        except Exception:
            resource = session.classes.ResourceCatalog(parent=subject, label="BIDS")
        # Try to upload the file to the subject BIDS folder
        try:
            resource.upload("{}/{}/{}".format(bids_directory, file, sub_file), sub_file, overwrite=True)
        except Exception:
            print("D - Failed to upload {}".format(file))


# Create XNAT experiments based on the bids datatype
def create_experiments():
    # Check if experiments exists - create one if not
    current_experiment = ""
    for item in subject.experiments.values():
        if session_folder == "":
            if item.label == "{}-{}".format(file, sub_file):
                current_experiment = "{}-{}".format(file, sub_file)
        else:
            if item.label == "{}-{}-{}".format(file, session_folder[1:], ses_file):
                current_experiment = "{}-{}-{}".format(file, session_folder[1:], ses_file)
    if current_experiment == "":
        if session_folder != "":
            current_experiment = "{}-{}-{}".format(file, session_folder[1:], ses_file)
            if ses_file == "anat" or ses_file == "dwi":
                session.classes.MrSessionData(parent=subject, label=current_experiment)
            if ses_file == "meg":
                session.classes.MegSessionData(parent=subject, label=current_experiment)
        else:
            current_experiment = "{}-{}".format(file, sub_file)
            if sub_file == "anat" or sub_file == "dwi":
                session.classes.MrSessionData(parent=subject, label=current_experiment)
            if sub_file == "meg":
                session.classes.MegSessionData(parent=subject, label=current_experiment)
    return current_experiment


# Work out the scan type / description based on the bids file name
def get_scan_type():
    split = exp_file.split("_")
    if "ses" not in split[1]:
        scan_type = split[1]
    else:
        scan_type = split[2]
    split_final = scan_type.split(".")
    scan_type = split_final[0]
    return scan_type


# Create XNAT experiments based on the bids datatype
def create_scans():
    # Check if scan exists - create one if not
    current_scan = ""
    scan_count = 0
    for item in experiment.scans.values():
        scan_count += 1
        if item.type == get_scan_type():
            current_scan = exp_file
    if current_scan == "":
        scan_type = get_scan_type()
        if exp_file.endswith(mri_suffixes):
            session.classes.MrScanData(parent=experiment, id=scan_count, type=scan_type)
        if exp_file.endswith(meg_suffixes):
            session.classes.MegScanData(parent=experiment, id=scan_count, type=scan_type)


# Upload scan, scan related, and bids files to their appropriate scan resource folders
def upload_scan_level_resources():
    scan = ""
    for item in experiment.scans.values():
        if get_scan_type() in item.type:
            scan = item
    if scan == "":
        # Check if an experiment BIDS resource folder exists - create one if not
        try:
            resource = experiment.resources["BIDS"]
        except Exception:
            resource = session.classes.ResourceCatalog(parent=experiment, label="BIDS")
    else:
        if exp_file.endswith(mri_suffixes):
            # Check if a NIFTI resource folder exists - create one if not
            try:
                resource = scan.resources["NIFTI"]
            except Exception:
                resource = session.classes.ResourceCatalog(parent=scan, label="NIFTI")
        elif exp_file.endswith(meg_suffixes):
            # Check if a FIF resource folder exists - create one if not
            try:
                resource = scan.resources["MEG"]
            except Exception:
                resource = session.classes.ResourceCatalog(parent=scan, label="MEG")
        else:
            # Check if a BIDS resource folder exists - create one if not
            try:
                resource = scan.resources["BIDS"]
            except Exception:
                resource = session.classes.ResourceCatalog(parent=scan, label="BIDS")
    try:
        print("session_folder: " + session_folder)
        if session_folder == "":
            print("Upload source: " + "{}/{}/{}/{}".format(bids_directory, file, sub_file, exp_file))
            print("Upload target: " + exp_file)
            resource.upload("{}/{}/{}/{}".format(bids_directory, file, sub_file, exp_file), exp_file, overwrite=True)
        else:
            print("Upload source 5: " + "{}/{}/{}/{}/{}".format(bids_directory, file, sub_file, ses_file, exp_file))
            print("Upload target 5: " + exp_file)
            resource.upload("{}/{}/{}/{}/{}".format(bids_directory, file, sub_file, ses_file, exp_file), exp_file, overwrite=True)
    except Exception as e:
        print("E - Failed to upload {}".format(exp_file))
        print(e)


# Attempt to connect to the XNAT instance - exit if unsuccessful
try:
    session = xnat.connect(url, user=user, password=password)
    print("Connected to XNAT instance")
except Exception:
    print("Unable to connect to the XNAT instance - Check you have the correct url, username, and password")
    raise SystemExit
# Attempt to find the chosen project - exit if unsuccessful
try:
    project = session.projects[project_id]
    print("Project {} found!".format(project_id))
except Exception:
    print("Unable to find project {} - Check you have the correct Project ID".format(project_id))
    raise SystemExit

# Check suitable BIDS subject folders exist in the bids_directory provided
check_subjects_exist()

# Loop through the top level in the bids directory
for file in os.listdir(bids_directory):
    # Upload any project level resources
    upload_project_level_resources()
    # Create subjects in XNAT
    create_subjects()
    # Check if it is a directory
    if os.path.isdir(os.path.join(bids_directory, file)):
        # Check the directory is a subject
        if file.startswith("sub"):
            # Setup subject reference
            subject = project.subjects[file]
            # Run through the contents of the subject folder
            for sub_file in os.listdir("{}/{}".format(bids_directory, file)):
                # Upload any subject level resources
                upload_subject_level_resources()
                if "ses" not in sub_file:
                    session_folder = ""
                    # If the folder is a bids supported datatype
                    if sub_file in bids_datatypes:
                        # Create experiments in XNAT
                        experiment = subject.experiments[create_experiments()]
                        # Run through the contents of the experiment folder and create required scans
                        for exp_file in os.listdir("{}/{}/{}".format(bids_directory, file, sub_file)):
                            # Create scans in XNAT
                            create_scans()
                        # Run through the contents of the experiment folder and upload files
                        for exp_file in os.listdir("{}/{}/{}".format(bids_directory, file, sub_file)):
                            # Upload the scan, scan-related, and bids individual files
                            upload_scan_level_resources()
                else:
                    session_folder = "/{}".format(sub_file)
                    # Run through the contents of the session folder
                    for ses_file in os.listdir("{}/{}{}".format(bids_directory, file, session_folder)):
                        # If the folder is a bids supported datatype
                        if ses_file in bids_datatypes:
                            # Create experiments in XNAT
                            experiment = subject.experiments[create_experiments()]
                            # Run through the contents of the experiment folder and create required scans
                            for exp_file in os.listdir("{}/{}{}/{}".format(bids_directory, file, session_folder, ses_file)):
                                # Create scans in XNAT
                                create_scans()
                            # Run through the contents of the experiment folder and upload files
                            print("uploading scan level resources ...")
                            for exp_file in os.listdir("{}/{}{}/{}".format(bids_directory, file, session_folder, ses_file)):
                                # Upload the scan, scan-related, and bids individual files
                                upload_scan_level_resources()

