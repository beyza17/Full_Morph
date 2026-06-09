# =============================================================
# seg_nrrd_to_vtk.py
# Converts .seg.nrrd segmentation files → per-region .vtk
# surface meshes organised for ALPACA input.
#
# Must be run inside 3D Slicer's Python environment:
#   1. Open 3D Slicer
#   2. View → Python Interactor
#   3. exec(open("/path/to/seg_nrrd_to_vtk.py").read())
#
# Input structure:
#   pipeline_data/segmentation_predictions/
#   ├── NG4975_RCL5.seg.nrrd
#   ├── NG4976_RCL5.seg.nrrd
#   └── ...
#
# Output structure:
#   pipeline_data/target_models/
#   ├── DG/
#   │   ├── NG4975_DG.vtk
#   │   ├── NG4976_DG.vtk
#   │   └── ...
#   ├── HP/
#   └── ...
# =============================================================

import os
import slicer
import vtk

# =============================================================
# CONFIGURATION — edit these two paths to match your system
# =============================================================

INPUT_FOLDER  = "/path/to/ngmm-pipeline/pipeline_data/segmentation_predictions"
OUTPUT_FOLDER = "/path/to/ngmm-pipeline/pipeline_data/target_models"

# =============================================================
# END OF CONFIGURATION
# =============================================================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

segLogic    = slicer.modules.segmentations.logic()
shNode      = slicer.mrmlScene.GetSubjectHierarchyNode()
sceneItemID = shNode.GetSceneItemID()

seg_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".seg.nrrd")]

if not seg_files:
    print(f"[ERROR] No .seg.nrrd files found in:\n  {INPUT_FOLDER}")
else:
    print(f"Found {len(seg_files)} segmentation file(s) to process.\n")

for filename in sorted(seg_files):
    seg_path  = os.path.join(INPUT_FOLDER, filename)
    base_name = filename.replace(".seg.nrrd", "")   # e.g. NG4975_RCL5
    ng_id     = base_name.split("_")[0]             # e.g. NG4975

    print(f"Processing: {filename}")

    # Load segmentation
    segNode = slicer.util.loadSegmentation(seg_path)

    # Export all segments to model nodes under a temporary folder
    exportFolderId = shNode.CreateFolderItem(sceneItemID, "TempSegmentModels")
    segLogic.ExportAllSegmentsToModels(segNode, exportFolderId)

    # Save each segment model into its region subfolder
    children = vtk.vtkIdList()
    shNode.GetItemChildren(exportFolderId, children)

    for i in range(children.GetNumberOfIds()):
        childId   = children.GetId(i)
        modelNode = shNode.GetItemDataNode(childId)

        if not (modelNode and modelNode.IsA("vtkMRMLModelNode")):
            continue

        # Sanitise region name (e.g. "Dentate Gyrus" → "DentateGyrus")
        region_name = "".join(
            c for c in modelNode.GetName() if c.isalnum() or c in ("_", "-")
        )

        # Create per-region output folder: target_models/DG/
        region_folder = os.path.join(OUTPUT_FOLDER, region_name)
        os.makedirs(region_folder, exist_ok=True)

        # Save as {NG_ID}_{REGION}.vtk  e.g. NG4975_DG.vtk
        save_path = os.path.join(region_folder, f"{ng_id}_{region_name}.vtk")

        if slicer.util.saveNode(modelNode, save_path):
            print(f"  Saved: {save_path}")
        else:
            print(f"  [FAILED]: {save_path}")

    # Cleanup scene before next file
    shNode.RemoveItem(exportFolderId)
    slicer.mrmlScene.RemoveNode(segNode)

print("\n------------------------------")
print("All segmentations processed.")
print(f"VTK files saved to:\n  {OUTPUT_FOLDER}")