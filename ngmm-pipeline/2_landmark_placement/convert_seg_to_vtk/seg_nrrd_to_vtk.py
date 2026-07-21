import os
import slicer
import vtk


INPUT_FOLDER = "/path/to/ngmm-pipeline/pipeline_data/segmentation_predictions"
OUTPUT_FOLDER = "/path/to/ngmm-pipeline/2_landmark_placement/target_models"


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    segLogic = slicer.modules.segmentations.logic()
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    sceneItemID = shNode.GetSceneItemID()

    seg_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".seg.nrrd")]

    if not seg_files:
        raise RuntimeError(
            f"No .seg.nrrd files found in:\n{INPUT_FOLDER}"
        )

    print(f"Found {len(seg_files)} segmentation file(s).\n")

    for filename in sorted(seg_files):

        seg_path = os.path.join(INPUT_FOLDER, filename)
        base_name = filename.replace(".seg.nrrd", "")
        ng_id = base_name.split("_")[0]

        print(f"Processing {filename}")

        segNode = slicer.util.loadSegmentation(seg_path)

        exportFolderId = shNode.CreateFolderItem(sceneItemID, "TempSegmentModels")
        segLogic.ExportAllSegmentsToModels(segNode, exportFolderId)

        children = vtk.vtkIdList()
        shNode.GetItemChildren(exportFolderId, children)

        for i in range(children.GetNumberOfIds()):

            childId = children.GetId(i)
            modelNode = shNode.GetItemDataNode(childId)

            if not (modelNode and modelNode.IsA("vtkMRMLModelNode")):
                continue

            region_name = "".join(
                c for c in modelNode.GetName()
                if c.isalnum() or c in ("_", "-")
            )

            region_folder = os.path.join(OUTPUT_FOLDER, region_name)
            os.makedirs(region_folder, exist_ok=True)

            save_path = os.path.join(
                region_folder,
                f"{ng_id}_{region_name}.vtk"
            )

            if slicer.util.saveNode(modelNode, save_path):
                print(f"  Saved: {save_path}")
            else:
                print(f"  FAILED: {save_path}")

        shNode.RemoveItem(exportFolderId)
        slicer.mrmlScene.RemoveNode(segNode)

    print("\nFinished successfully.")


if __name__ == "__main__":
    try:
        main()
        slicer.app.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR] Pipeline crashed:\n{e}")
        slicer.app.exit(1)