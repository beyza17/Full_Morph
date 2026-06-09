import os
import nibabel as nib
import numpy as np
import argparse
from pathlib import Path
import shutil
import nrrd
def convert_nrrd_to_nifti(nrrd_file_path, nifti_file_path):
    # Read the NRRD file
    nrrd_data, nrrd_options = nrrd.read(nrrd_file_path)
    # Save the NIfTI image
    nib.save(nib.Nifti1Image(nrrd_data.astype(np.float32), affine=np.eye(4)), nifti_file_path)

def convert_file_format(ORG_DATA_PATH, OUT_DATA_PATH, endswith):
    all_files = os.listdir(ORG_DATA_PATH)
    for file in all_files:
        if file.endswith(endswith):
            source_nrrd_file_path = os.path.join(ORG_DATA_PATH, file)
            save_nifti_file_path = os.path.join(OUT_DATA_PATH, file)
            # Automatically generate the nifti_file_path based on nrrd_file_path
            base_name = os.path.splitext(os.path.basename(save_nifti_file_path))[0]
            # print(base_name)
            newname = os.path.splitext(os.path.basename(base_name))[0]
            # print(newname)
            save_nifti_file_path = os.path.join(os.path.dirname(save_nifti_file_path), newname + '.nii.gz')
            # print(source_nrrd_file_path)
            # print(save_nifti_file_path)
            convert_nrrd_to_nifti(source_nrrd_file_path, save_nifti_file_path)
    print('File convert done. ')
    
def main(folder_path, output_path,clean_path):
    folder_path = Path(folder_path).resolve()
    output_path = Path(output_path).resolve()
    clean_path = Path(clean_path).resolve()
    if output_path.exists():
        for item in output_path.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
    if clean_path.exists():
        for item in clean_path.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    convert_file_format(folder_path, output_path, '.nrrd')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert medical image file formats.')
    parser.add_argument('--folder_path', type=str, required=True, help='The input directory containing files to be converted.')
    parser.add_argument('--output_path', type=str, help='The output directory where converted files will be saved. If not provided, "VolumeReformat" will be added to the input path.')
    parser.add_argument('--clean_path', type=str, help='The output directory where converted files will be saved. If not provided, "VolumeReformat" will be added to the input path.')


    args = parser.parse_args()

    main(args.folder_path, args.output_path,args.clean_path)
