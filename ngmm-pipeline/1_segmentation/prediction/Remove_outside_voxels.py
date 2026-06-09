import os
import nibabel as nib
import numpy as np
import argparse
from pathlib import Path
import shutil
import SimpleITK as sitk

def main(volume_dir, seg_dir,output_path):
    volume_dir = Path(volume_dir).resolve()
    seg_dir = Path(seg_dir).resolve()
    output_path = Path(output_path).resolve()



    # Loop through all volume files
    for filename in os.listdir(volume_dir):
        if not filename.endswith(".nrrd"):
            continue

        # Extract ID before first underscore
        file_id = filename.split("_")[0]

        volume_path = os.path.join(volume_dir, filename)
        seg_filename = f"{file_id}_RCL5.seg.nrrd"
        seg_path = os.path.join(seg_dir, seg_filename)

        # Check if the corresponding segmentation file exists
        if not os.path.exists(seg_path):
            print(f"Segmentation not found for {file_id}, skipping.")
            continue

        print(f"Processing: {filename} with segmentation {seg_filename}")

        # Load volume
        volume = sitk.ReadImage(volume_path)
        volume_array = sitk.GetArrayFromImage(volume)

        # Load segmentation
        seg = sitk.ReadImage(seg_path)
        seg_array = sitk.GetArrayFromImage(seg)

        # Mask segmentation where volume is invalid
        valid_mask = volume_array > 0
        seg_array[~valid_mask] = 0

        # Convert back to SimpleITK image and retain metadata
        corrected_seg = sitk.GetImageFromArray(seg_array)
        corrected_seg.CopyInformation(seg)

        for key in seg.GetMetaDataKeys():
            corrected_seg.SetMetaData(key, seg.GetMetaData(key))

        # Save corrected segmentation
        output_path = os.path.join(seg_dir, f"{file_id}_RCL5.seg.nrrd")
        sitk.WriteImage(corrected_seg, output_path,useCompression=True)
        print(f"Saved corrected segmentation at: {output_path}")
        
  



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert medical image file formats.')
    parser.add_argument('--volume_dir', type=str, required=True, help='The input directory containing files to be converted.')
    parser.add_argument('--seg_dir', type=str, help='The output directory where converted files will be saved. If not provided, "VolumeReformat" will be added to the input path.')
    parser.add_argument('--output_path', type=str, required=True, help='The input directory containing files to be converted.')

    args = parser.parse_args()

    main(args.volume_dir, args.seg_dir,args.output_path)
