import os
import json
import shutil
import pandas as pd
import csv
import argparse

# Define the paths to the input and output folders
parser = argparse.ArgumentParser()
parser.add_argument('--path_input', type=str,
                    help='Path to the input folder')
parser.add_argument('--path_output', type=str,
                    help='Path to the output folder')
args = parser.parse_args()

if args.path_input is None:
    raise ValueError(
        "Please provide the path to the input folder using the --path_input argument.")
if args.path_output is None:
    raise ValueError(
        "Please provide the path to the output folder using the --path_output argument.")

# Creating the folders in the output path
os.makedirs(args.path_output, exist_ok=True)
os.makedirs(os.path.join(args.path_output, 'derivatives'), exist_ok=True)
os.makedirs(os.path.join(args.path_output, 'derivatives', 'masks'), exist_ok=True)
os.makedirs(os.path.join(args.path_output, 'derivatives', 'simulated_low-field'), exist_ok=True)

# Create the subject folders for all the participants
for subject in os.listdir(args.path_input):
    
    if not os.path.isdir(os.path.join(args.path_input, subject)):
        continue
    
    # Create the anat folder of the participant
    subject_folder = os.path.join(args.path_output, subject.replace('s','sub-'))
    os.makedirs(subject_folder, exist_ok=True)
    os.makedirs(os.path.join(subject_folder, 'anat'), exist_ok=True)

    # Rename the files and copy them individually to the anat folder of the participant
    for image in ['t1.nii.gz', 't2.nii.gz']:
        shutil.copyfile(os.path.join(args.path_input, subject, image), os.path.join(subject_folder, 'anat', 
                subject.replace('s','sub-') + '_' + image.replace('.nii.gz','').upper() + 'w.nii.gz'))
        
    # Create the participants.tsv file
    meta_df = pd.read_csv(os.path.join(args.path_input, 'meta.csv'), delimiter=';')
    meta_df = meta_df[['image_id', 'age', 'diagnosis']]
    meta_df = meta_df.rename(columns={'image_id': 'participant_id'})
    meta_df['participant_id'] = meta_df['participant_id'].str.replace('s', 'sub-')
    meta_df.to_csv(os.path.join(args.path_output, 'participants.tsv'), sep='\t', index=False, quoting=csv.QUOTE_NONE)

# Select the participants with a normal diagnosis and age 0
participants = []
with open(os.path.join(args.path_input, 'meta.csv'), 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for line in reader:
        if 's' in line[0]:
            if line[5] == 'normal' and line[2] == '0':
                if line[0] not in ['s0645', 's0672', 's0841']: # These subjects have artefacts in their images.
                    participants.append(line[0])

# Create the masks folder in the derivatives for the selected participants
for subject in participants:

    os.makedirs(os.path.join(args.path_output, 'derivatives', 'masks', subject.replace('s','sub-')), exist_ok=True)
    os.makedirs(os.path.join(args.path_output, 'derivatives', 'simulated_low-field', subject.replace('s','sub-')), exist_ok=True)

    # Copy the masks to the masks folder of the participant
    shutil.copyfile(os.path.join(args.path_input, subject, 't2_mask.nii.gz'), os.path.join(args.path_output, 'derivatives', 'masks', subject.replace('s','sub-'),
            subject.replace('s','sub-') + '_T1w_T2w_mask.nii.gz'))
    
# Create the dataset_description.json file for the masks
with open(os.path.join(args.path_output, 'derivatives', 'masks', 'dataset_description.json'), 'w') as f:
    json.dump({"Name": "Mask used for the computation of the SNR of both T1w and T2w images",
                "BIDSVersion": "1.9.0",
                "License": "CC-by 4.0",
                "Description": "A mask delineating a homogeneous 9-pixel square region of white matter in the brain, defined on the T2w image.",
                "Type": "Binary",
                "Purpose": "SNR computation",
                "Method": "Manual delineation in FSLeyes",
            }, f, indent=4)

# Create the dataset_description.json file for the simulated low-field images
with open(os.path.join(args.path_output, 'derivatives', 'simulated_low-field', 'dataset_description.json'), 'w') as f:
    json.dump({"Name": "Simulated low-field MRI images",
                "BIDSVersion": "1.9.0",
                "License": "CC-by 4.0",
                "Description": "Only the participants with a normal diagnosis and age 0 are included in this folder. "
                "A downsampling and Gaussian noise addition have been applied to the T1w and T2w images.",
            }, f, indent=4)

# Create the dataset_description.json file for the whole dataset
with open(os.path.join(args.path_output, 'dataset_description.json'), 'w') as f:
    json.dump({"Name": "Basel Dataset",
                "BIDSVersion": "1.9.0",
                "DatasetDOI": "10.5281/zenodo.6556135",
                "License": "CC-by 4.0",
                "Authors": ["Akinci D'Antonoli, Tugba", "Todea, Ramona-Alexandra", "Datta, Alexandre",
                            "Stieltjes, Bram", "Leu, Nora", "Prüfer, Friederike", "Wasserthal, Jakob"],
                },
                f, indent=4)

# Create the participants.json file
with open(os.path.join(args.path_output, 'participants.json'), 'w') as f:
    json.dump({"Name": "Participants",
                "BIDSVersion": "1.9.0",
                "License": "CC-by 4.0",
                "participant_id": {
                    "Description": "Unique Participant ID",
                    "LongName": "Participant ID",
                    "age": {
                        "Description": "Participant age",
                        "LongName": "Participant age",
                        "Units": "months"},
                    "diagnosis": {
                    "Description": "The diagnosis of pathology of the participant",
                    "LongName": "Pathology name",
                   },
                }}, f, indent=4)

# Create a README.md file 
with open(os.path.join(args.path_output, 'README.md'), 'w') as f:
    f.write("## Dataset\n\n")
    f.write("This dataset contains 833 brain MRI images (T1w and T2w) from infancy and early childhood. The age of the subjects is between "
            "0 months and 36 months. It contains a wide range of pathologies as well as healthy subjects. It is a quite diverse dataset acquired "
            "in the clinical routine over several years (images acquired with same Phillips Achieva 3T MRI scanner, but with different protocols).\n\n")
    f.write("The T1w images are resampled to the shape of the T2w images. Then both are skull stripped.\n\n")

    f.write("## Usage\n\n")
    f.write("All details about this dataset can be found in the following paper. If you use this dataset please cite this paper.\n\n")
    f.write("T. Akinci D’Antonoli et al., « Development and Evaluation of Deep Learning Models for Automated Estimation of Myelin Maturation Using"
            "Pediatric Brain MRI Scans», Radiol Artif Intell, vol. 5, nᵒ 5, p. e220292, juill. 2023, doi: 10.1148/ryai.220292.\n\n")

    f.write("This dataset was converted to BIDS format as part of the Brainhack GBM6953EE course at Polytechnique Montréal.")


