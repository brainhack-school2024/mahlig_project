import os
import numpy as np
import nibabel as nib
from nilearn.image import resample_img
from calcul_snr import calcul_snr
import csv
import json
import argparse

# Define the path to the dataset and the masks
parser = argparse.ArgumentParser()
parser.add_argument('--path_dataset', type=str,
                    help='Path to the BIDS dataset')
parser.add_argument('--path_mask', type=str,
                    help='Path to the mask folder')
args = parser.parse_args()

if args.path_dataset is None:
    raise ValueError(
        "Please provide the path to the BIDS dataset using the --path_dataset argument.")
if args.path_mask is None:
    raise ValueError(
        "Please provide the path to the mask folder using the --path_mask argument.")

# Create a list of the participants with a normal diagnosis and age 0
participants = []
with open(os.path.join(args.path_dataset, 'participants.tsv'), 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for line in reader:
        if 'sub-' in line[0]:
            if line[2] == 'normal' and line[1] == '0':
                # These subjects have artefacts in their images.
                if line[0] not in ['sub-0645', 'sub-0672', 'sub-0841']:
                    participants.append(line[0])

for subject in participants:
    t1 = f"{subject}_T1w.nii.gz"
    t2 = f"{subject}_T2w.nii.gz"

    for i in [t1, t2]:

        # Remove the extension from the filename
        filename, ext = os.path.splitext(i)
        if ext == '.gz':
            filename, ext = os.path.splitext(filename)

        # Load the image
        img = nib.load(os.path.join(args.path_dataset, subject, 'anat', i))

        # Downsample the image
        new_voxel_size = (1.6, 1.6, 5) # Low-field MRI resolution
        resampled_img = resample_img(img, target_affine=np.diag(
            new_voxel_size), interpolation='nearest')

        # Get the data from the previous image
        data = resampled_img.get_fdata()

        # Generate Gaussian noise and add to the data
        mean = 0
        if i == t1:
            std_dev = 79.50 - \
                calcul_snr(args.path_dataset, args.path_mask, [subject])[
                    2][0]
        elif i == t2:
            std_dev = 86.54 - \
                calcul_snr(args.path_dataset, args. path_mask, [subject])[
                    3][0]
        noise = np.random.normal(mean, std_dev, data.shape)
        noisy_data = data + noise

        # Create and save a new NIfTI image with the noisy data
        noisy_img = nib.Nifti1Image(
            noisy_data, resampled_img.affine, resampled_img.header)
        os.makedirs(os.path.join(args.path_dataset, 'derivatives',
                    'simulated_low-field', subject, 'anat'), exist_ok=True)
        noisy_img.to_filename(os.path.join(args.path_dataset, 'derivatives', 'simulated_low-field',
                                           subject, 'anat', f"{filename}_simulated_low-field.nii.gz"))

        # Create the JSON sidecar files
        with open(os.path.join(args.path_dataset, 'derivatives', 'simulated_low-field',
                               subject, 'anat', f"{filename}_simulated_low-field.json"), 'w') as f:
            json.dump({"Name": "Simulated low-field MRI images",
                       "Processing": [
                           {
                               "Step": "Downsampling",
                               "Resolution": "1.6 mm x 1.6 mm x 5 mm",
                               "Tool": "Nilearn version 0.10.4",
                               "Interpolation": "Nearest neighbour"
                           },
                           {
                               "Step": "Noise Addition",
                               "NoiseType": "Gaussian",
                               "NoiseParameters": {
                                   "Mean": 0,
                                   "StandardDeviation": round(std_dev, 2)
                               }
                           }
                       ]
                       }, f, indent=4)