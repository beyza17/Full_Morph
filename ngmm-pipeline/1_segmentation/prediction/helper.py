# import lib
import os
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import nrrd
import shutil
import json
import SimpleITK as sitk
import sys
import os
import nibabel as nib
import numpy as np 
import json
from scipy.ndimage import zoom


#image convert to nifti from nrrd. 
def convert_nrrd_to_nifti(nrrd_file_path, nifti_file_path):
    # Read the NRRD file
    nrrd_data, nrrd_options = nrrd.read(nrrd_file_path)
    
        
    # Save the NIfTI image
    nib.save(nib.Nifti1Image(nrrd_data.astype(np.float32), affine=np.eye(4)), nifti_file_path)

# create directory
def create_folder(_dir):
    if not os.path.exists(_dir):
        os.makedirs(_dir)

# Function to plot all slices of a 3D image
def plot_all_slices(data):
    # Determine the number of slices to display
    slices = data.shape[-1]
    # Calculate the number of subplots needed (square root of number of slices, rounded up)
    subplot_dim = int(np.ceil(np.sqrt(slices)))
    fig, ax = plt.subplots(subplot_dim, subplot_dim, figsize=(15, 15))
    ax = ax.flatten()
    for i in range(slices):
        ax[i].imshow(data[:, :, i], cmap='gray')
        ax[i].axis('off')
    # Hide any unused subplots
    for i in range(slices, len(ax)):
        ax[i].axis('off')
    plt.show()

# Function to plot histogram of voxel intensities
def plot_histogram(data):
    fig, ax = plt.subplots()
    ax.hist(data.ravel(), bins=256, color='c', alpha=0.75)
    ax.set_xlabel('Intensity Value')
    ax.set_ylabel('Frequency')
    ax.set_title('Histogram of Voxel Intensities')
    plt.show()

# Function to generate a binary image based on a threshold
def generate_binary_image(data, threshold):
    binary_data = np.where(data > threshold, 0, 1)
    return binary_data

# Function to adjust voxel spacing and set the origin to 0
def adjust_affine_for_spacing_and_origin(affine):
    # Create a new affine matrix with 1mm spacing if not already set
    new_affine = affine.copy()
    np.fill_diagonal(new_affine[:3, :3], 1)
    # Set the origin to 0
    new_affine[:3, 3] = 0
    return new_affine

# Function to save binary data as a new NIfTI image with 1mm³ voxel spacing and origin set to 0
def save_binary_image_with_adjusted_origin(binary_data, original_nii, output_filename):
    # Adjust affine for 1mm³ voxel spacing and set the origin to 0
    adjusted_affine = adjust_affine_for_spacing_and_origin(original_nii.affine)
    
    # Ensure the header is copied and modified for the new image dimensions
    new_header = original_nii.header.copy()
    new_header.set_zooms((1, 1, 1))  # Set voxel sizes to 1mm³
    
    # Create a NIfTI image from the binary data with adjusted affine
    binary_img = nib.Nifti1Image(binary_data.astype(np.int16), adjusted_affine, new_header)
    
    # Save the binary image to disk with the specified filename
    nib.save(binary_img, output_filename + '.nii.gz')

def make_if_dont_exist(folder_path,overwrite=False):

    if os.path.exists(folder_path):
        
        if not overwrite:
            print(f'{folder_path} exists.')
        else:
            print(f"{folder_path} overwritten")
            shutil.rmtree(folder_path)
            os.makedirs(folder_path)

    else:
      os.makedirs(folder_path)
      print(f"{folder_path} created!")


# .nrrd to nifit.
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
            save_nifti_file_path = os.path.join(os.path.dirname(save_nifti_file_path), newname + '_0000.nii.gz')
            # print(source_nrrd_file_path)
            # print(save_nifti_file_path)
            convert_nrrd_to_nifti(source_nrrd_file_path, save_nifti_file_path)
    print('File convert done. ')

def load_nifti_file(filepath):
    nifti_img = nib.load(filepath)
    return nifti_img, nifti_img.get_fdata(), 

def load_nifti_file_af_datatype(filepath):
    img = nib.load(filepath)
    data = img.get_fdata()
    shape = img.shape
    affine = img.affine
    datatype = img.get_data_dtype()
    return data, shape, affine, datatype

def file_exists(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False


def print_nrrd_header_info(file_path):
    # Load the .seg.nrrd file using SimpleITK
    img = sitk.ReadImage(file_path)
    
    # Print all metadata keys and values
    print("Header Information:")
    for key in img.GetMetaDataKeys():
        print(f"{key}: {img.GetMetaData(key)}")
        
def read_and_display_json(file_path):
    # Read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Pretty print the JSON data
    return data

def convert_nifti_to_seg_nrrd(input_filepath, output_filepath, labels):
    # Load the .nii.gz file using nibabel
    nii_img = nib.load(input_filepath)
    img_data = nii_img.get_fdata()

    # Create a SimpleITK image from the numpy array
    sitk_img = sitk.GetImageFromArray(np.transpose(img_data, (2, 1, 0)))
    sitk_img = sitk.Cast(sitk_img, sitk.sitkInt32)

    # Set the spacing (voxel sizes)
    spacing = nii_img.header.get_zooms()[:3]
    sitk_img.SetSpacing([float(sp) for sp in spacing])

    # Set the direction (rotation matrix)
    direction = np.linalg.inv(nii_img.affine[:3, :3]).flatten()
    sitk_img.SetDirection(direction.tolist())

    # Set the origin (translation vector)
    origin = nii_img.affine[:3, 3]
    sitk_img.SetOrigin(origin.tolist())

    # Add custom metadata for segments
    for i, label in enumerate(labels):
        sitk_img.SetMetaData(f"Segment{i}_ID", str(i))
        sitk_img.SetMetaData(f"Segment{i}_Name", label)
        sitk_img.SetMetaData(f"Segment{i}_ColorAutoGenerated", str(0))
        sitk_img.SetMetaData(f"Segment{i}_LabelValue", str(i))
        sitk_img.SetMetaData(f"Segment{i}_Layer", str(0))

    # Save the image as a .seg.nrrd file
    sitk.WriteImage(sitk_img, output_filepath, useCompression=True)
    print(f"Segmented NRRD file saved to: {output_filepath}")

def process_all_volumes(input_dir, output_dir, output_extension, labels):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process each file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".nii.gz"):
            input_filepath = os.path.join(input_dir, filename)
            output_filename = filename.replace(".nii.gz", output_extension)
            output_filepath = os.path.join(output_dir, output_filename)
            
            convert_nifti_to_seg_nrrd(input_filepath, output_filepath, labels)

def parameter_change(source_dir):
    # Step 1: Read the source files and store their metadata in a dictionary
    source_metadata = {}
    for source_filename in os.listdir(source_dir):
        if source_filename.endswith(".nrrd"):
            base_name = os.path.splitext(source_filename)[0].split('_')[0]  # Get base name before underscore or extension
            source_filepath = os.path.join(source_dir, source_filename)
            print("Source .nrrd file path:", source_filepath)

            # Read source NRRD file to get metadata
            source_nrrd_data, source_nrrd_header = nrrd.read(source_filepath)
            source_metadata[base_name] = {
                'data': source_nrrd_data,
                'header': source_nrrd_header,
                'spacing': source_nrrd_header.get('space directions').diagonal().tolist(),
                'origin': source_nrrd_header.get('space origin').tolist(),
                'dimensions': source_nrrd_data.shape,
                'direction': source_nrrd_header.get('space directions').flatten().tolist()
            }

            print(f"Extracted metadata from source NRRD: {base_name}")

    # Path to the directory containing nnUNet results
    prediction_dir = os.path.join(source_dir, "prediction")

    if not os.path.exists(prediction_dir):
        print(f"Error: The directory '{prediction_dir}' does not exist. Operation cancelled.")
        sys.exit(1)  # Exit the script with a non-zero status to indicate an error

    # Step 2: Loop over the output files in the prediction directory
    for output_filename in os.listdir(prediction_dir):
        if output_filename.endswith(".nrrd"):
            base_name = os.path.splitext(output_filename)[0].split('_')[0]  # Get base name before underscore or extension
            if base_name in source_metadata:
                output_filepath = os.path.join(prediction_dir, output_filename)
                print("Output .nrrd file path:", output_filepath)

                # Step 3: Read the result NRRD file (segmentation or volume)
                try:
                    result_nrrd_data, result_nrrd_header = nrrd.read(output_filepath)
                except Exception as e:
                    print(f"Error reading {output_filepath}: {e}")
                    continue

                # Validate data type and convert if necessary
                expected_dtype = source_metadata[base_name]['data'].dtype
                if result_nrrd_data.dtype != expected_dtype:
                    print(f"Data type mismatch for {output_filepath}: expected {expected_dtype}, got {result_nrrd_data.dtype}. Converting data type.")
                    try:
                        result_nrrd_data = result_nrrd_data.astype(expected_dtype)
                    except Exception as e:
                        print(f"Error converting data type for {output_filepath}: {e}")
                        continue

                # Step 4: Update the result NRRD header with the source metadata
                source_header = source_metadata[base_name]['header']
                result_nrrd_header['space directions'] = source_header['space directions']
                result_nrrd_header['space origin'] = source_header['space origin']
                result_nrrd_header['sizes'] = source_header['sizes']

                # Step 5: Save the modified NRRD file
                try:
                    nrrd.write(output_filepath, result_nrrd_data, header=result_nrrd_header)
                    print(f"Modified NRRD file saved to: {output_filepath}")
                except Exception as e:
                    print(f"Error writing {output_filepath}: {e}")
                    continue

                # Verify metadata of the modified file
                try:
                    modified_nrrd_data, modified_nrrd_header = nrrd.read(output_filepath)
                    modified_spacing = modified_nrrd_header.get('space directions').diagonal().tolist()
                    modified_origin = modified_nrrd_header.get('space origin').tolist()
                    modified_dimensions = modified_nrrd_data.shape
                    modified_direction = modified_nrrd_header.get('space directions').flatten().tolist()

                    print(f"Modified spacing: {modified_spacing}")
                    print(f"Modified origin: {modified_origin}")
                    print(f"Modified direction: {modified_direction}")
                    print(f"Modified dimensions: {modified_dimensions}")
                except Exception as e:
                    print(f"Error verifying {output_filepath}: {e}")
                    continue
            else:
                print(f"Warning: No matching source file for output file '{output_filename}'")


def remove_all_files_and_folders(path):
    # Check if the path exists
    if not os.path.exists(path):
        print("The specified path does not exist.")
        return

    # Loop through each item in the directory
    for item_name in os.listdir(path):
        item_path = os.path.join(path, item_name)  # Full path to the item

        try:
            # Check if the item is a file or a folder
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # Remove the file or link
                print(f"Removed file: {item_path}")
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove the directory and all its contents
                print(f"Removed directory: {item_path}")
        except Exception as e:
            print(f"Failed to remove {item_path}. Reason: {e}")
            
#######################################################################################################3
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

def label_downsample(img_data, label_data):
        
    # Get the shapes of the image and label data
    img_shape = img_data.shape
    label_shape = label_data.shape

    # Calculate the resize factor for each dimension
    resize_factors = [img_shape[i] / label_shape[i] for i in range(3)]

    # Resize the label data using scipy's zoom function
    resized_label_data = zoom(label_data, resize_factors, order=0)  
    return resized_label_data

def load_nifti_file(filepath):
    nifti_img = nib.load(filepath)
    return nifti_img.get_fdata(), nifti_img.shape

def save_nifti_file(data, filepath):
    nifti_img = nib.Nifti1Image(data.astype(np.float32), affine=np.eye(4))
    nib.save(nifti_img, filepath)

def rename_file_name(DATASET_PATH,remove_str, replace_str=""):
    # Iterate over the files in the directory
    for filename in os.listdir(DATASET_PATH):
        # Check if the file is a NIfTI image
        if filename.endswith(".nii.gz"):
            print(filename)
            # Extract the required part of the filename
            new_filename = filename.replace(remove_str,replace_str)
            # Construct the new path for the renamed file
            old_path = os.path.join(DATASET_PATH, filename)
            new_path = os.path.join(DATASET_PATH, new_filename)
            # Rename the file
            os.rename(old_path, new_path)
            
def file_compare(TRAINING_DATASET_PATH,input_path,resize=False):
    # over view original Images 
    all_files = os.listdir(input_path)
    for file in all_files:
        if file.endswith(".nii.gz"):
            _label_path = os.path.join(input_path, file)

            file_id = file.split("_")
            file_name = f"{file_id[0]}_RCL5_0000.nii.gz"

            _file_path = os.path.join(TRAINING_DATASET_PATH, file_name)
            
            org_img, org_shape = load_nifti_file(_file_path)
            label_img, label_shape = load_nifti_file(_label_path)
            print(file_name)
            print("img: ",org_shape)
            print("label: ",label_shape)
            
            if org_shape != label_shape: 
                
                if resize:
                    resize_label = label_downsample(org_img, label_img)
                    # Save resized label
                    resized_label_filepath = os.path.join(input_path, file_name)  # Save with the same filename
                    save_nifti_file(resize_label, resized_label_filepath)

                    print("resize shape: ",resize_label.shape)
            else: 
                print("checked")
                
            print("")
    print('File read done. ')

def modify_intensity(input_filepath, output_filepath, intensity_map):
    # Load the NIfTI image
    nifti_img = nib.load(input_filepath)
    img_data = nifti_img.get_fdata()

    # Modify intensity values based on the provided intensity map
    modified_img_data = np.copy(img_data)
    for original_intensity, new_intensity in intensity_map.items():
        modified_img_data[img_data == original_intensity] = new_intensity

    # Save the modified image to a new NIfTI file
    modified_nifti_img = nib.Nifti1Image(modified_img_data, nifti_img.affine)
    nib.save(modified_nifti_img, output_filepath)
    return modified_img_data
    

def list_of_int(img_data):
    # Flatten the image data array to a 1D array
    flat_img_data = img_data.flatten()

    # Get the unique intensity values
    unique_values = set(flat_img_data)
    init_list = [int(x) for x in unique_values]

    return init_list


def read_nifti(path):
    img = nib.load(path)

    return img.get_fdata(),img.shape