import os
import argparse
import SimpleITK as sitk
import nrrd
from pathlib import Path
from helper import (
    print_nrrd_header_info,
    read_and_display_json,
    convert_nifti_to_seg_nrrd,
    process_all_volumes
)


def extract_segment_colors_by_name(example_path):
    # Read header from example .seg.nrrd
    _, header = nrrd.read(example_path)
    name_to_color = {}

    # Build mapping: Segment name -> Segment color
    for key, value in header.items():
        key = key.decode() if isinstance(key, bytes) else key
        value = value.decode() if isinstance(value, bytes) else value

        if key.endswith("_Name"):
            segment_id = key.split("_")[0]
            color_key = f"{segment_id}_Color"
            color_value = header.get(color_key.encode() if isinstance(key, bytes) else color_key)
            color_value = color_value.decode() if isinstance(color_value, bytes) else color_value
            name_to_color[value] = color_value

    return name_to_color


def apply_colors_by_name(input_path, example_path):
    # Load input image
    sitk_img = sitk.ReadImage(input_path)

    # Extract color mapping from example
    name_to_color = extract_segment_colors_by_name(example_path)

    # For each metadata entry, if it's a Name, assign the corresponding Color (if exists)
    keys_to_add = []
    for key in sitk_img.GetMetaDataKeys():
        if key.endswith("_Name"):
            name = sitk_img.GetMetaData(key)
            segment_id = key.split("_")[0]
            color = name_to_color.get(name)
            if color:
                color_key = f"{segment_id}_Color"
                keys_to_add.append((color_key, color))

    # Set new Color values based on matching Name
    for k, v in keys_to_add:
        sitk_img.SetMetaData(k, v)

    # Overwrite the same file
    sitk.WriteImage(sitk_img, input_path, useCompression=True)
    print(f"Updated NRRD with copied colors saved to: {input_path}")



def main(label_json_path, input_dir, output_dir, original_folder, example_seg_path):
    label_json_path = Path(label_json_path).resolve()
    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve()
    original_folder = Path(original_folder).resolve()
    example_seg_path = Path(example_seg_path).resolve()
    # --- Load Label Mapping from JSON ---
    data = read_and_display_json(label_json_path)
    labels = data.get('labels', {})

    # --- Process NIfTI Volumes ---
    output_extension = ".seg.nrrd"
    process_all_volumes(input_dir, output_dir, output_extension, labels)

    # --- Correct Metadata in Output Files ---
    input_folder = output_dir  # Already defined

    for filename in os.listdir(input_folder):
        if not filename.endswith(output_extension):
            continue

        input_path = os.path.join(input_folder, filename)
        base_id = filename.split("_")[0]
        expected_filename = f"{base_id}_RCL5_0000.nrrd"
        original_nrrd_path = os.path.join(original_folder, expected_filename)
        if not os.path.exists(original_nrrd_path):
            print(f"Original file not found for {filename}, skipping metadata correction.")
            continue

        # Read images
        original_img = sitk.ReadImage(original_nrrd_path)
        input_img = sitk.ReadImage(input_path)

        # Transfer metadata
        input_img.CopyInformation(original_img)

        # Save with corrected spacing/origin/direction
        sitk.WriteImage(input_img, input_path,useCompression=True)
        print(f"Updated file saved to: {input_path}")

        # Apply segment colors from example
        apply_colors_by_name(input_path, example_seg_path)
      


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert medical image file formats and fix metadata.')
    parser.add_argument('--label_json_path', type=str, required=True, help='Path to dataset.json containing label definitions.')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing input NIfTI label volumes.')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save converted NRRD files.')
    parser.add_argument('--original_folder', type=str, required=True, help='Directory containing original NRRD files for metadata correction.')
    parser.add_argument('--example_seg_path', type=str, required=True, help='Path to an example .seg.nrrd file to copy segment colors from.')

    args = parser.parse_args()
    main(args.label_json_path, args.input_dir, args.output_dir, args.original_folder, args.example_seg_path)
