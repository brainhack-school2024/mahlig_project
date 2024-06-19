import os
import nibabel as nib
import numpy as np
from nilearn.image import resample_img

def calcul_snr(path_dataset, path_mask, participants, derivative=False):

    # Initialize the lists
    std_t1 = []
    snr_t1 = []
    std_t2 = []
    snr_t2 = []
    mean_t1 = []
    mean_t2 = []

    for subject in participants:

        if derivative == False:
            t1 = f"{subject}_T1w.nii.gz"
            t2 = f"{subject}_T2w.nii.gz"
        elif derivative == True:
            t1 = f"{subject}_T1w_simulated_low-field.nii.gz"
            t2 = f"{subject}_T2w_simulated_low-field.nii.gz"

        for i in [t1, t2]:

            # Apply the mask of a homogeneous ROI in the brain
            subject_folder = f"s{subject[4:].zfill(4)}"

            if derivative == False:
                # Load the T1w and T2w images
                img = nib.load(os.path.join(path_dataset, subject, 'anat', i))
                # Load the manually defined ROI brain mask
                brain_mask = nib.load(
                    f"{os.path.join(path_mask, subject_folder)}/t2_mask.nii.gz")

            elif derivative == True:  # The mask must be resampled to match the dimensions of the degraded image
                # Load the T1w and T2w images
                img = nib.load(os.path.join(
                    path_dataset, 'derivatives', 'simulated_low-field', subject, 'anat', i))
                # Load the manually defined ROI brain mask
                initial_mask = nib.load(
                    f"{os.path.join(path_mask, subject_folder)}/t2_mask.nii.gz")
                brain_mask = resample_img(
                    initial_mask, target_affine=img.affine, target_shape=img.shape[:3], interpolation='nearest')

            brain_data = img.get_fdata() * brain_mask.get_fdata()

            # Calculate the SNR
            if i == t1:
                mean_brain = np.mean(brain_data[brain_data != 0])
                std_brain = np.std(brain_data[brain_data != 0])

                mean_t1.append(mean_brain)
                std_t1.append(std_brain)
                snr_t1.append(mean_brain / std_brain)

            elif i == t2:
                mean_brain = np.mean(brain_data[brain_data != 0])
                std_brain = np.std(brain_data[brain_data != 0])

                mean_t2.append(mean_brain)
                std_t2.append(std_brain)
                snr_t2.append(mean_brain / std_brain)

    return snr_t1, snr_t2, std_t1, std_t2, mean_t1, mean_t2
