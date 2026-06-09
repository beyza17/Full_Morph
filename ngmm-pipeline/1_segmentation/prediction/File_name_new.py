
import os
import shutil
import argparse
from pathlib import Path

def main(folder_path, output_path, name_list):
    folder_path = Path(folder_path).resolve()
    output_path = Path(output_path).resolve()

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Clean output directory
    if output_path.exists() and output_path.is_dir():
        for file in output_path.iterdir():
            if file.is_file():
                file.unlink()

    for file_name in os.listdir(folder_path):
        old_path = folder_path / file_name

        if file_name.endswith("RCL5_masked.nrrd"):
            parts = file_name.split("_")
            if len(parts) >= 2 and parts[0] in name_list:
                new_name = f"{parts[0]}_{parts[1]}_0000.nrrd"
                new_path = output_path / new_name
                shutil.copy2(old_path, new_path)
                print(f"Filtered, renamed, and copied: {file_name} -> {new_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter and copy specific medical image files based on name.')
    parser.add_argument('--folder_path', type=str, required=True, help='Input directory containing files.')
    parser.add_argument('--output_path', type=str, required=True, help='Output directory for processed files.')
    parser.add_argument('--names', nargs='+', required=True, help='List of base names to include (e.g., NG2561 NG2562)')

    args = parser.parse_args()

    main(args.folder_path, args.output_path, args.names) 