**Preview Quads** is a non-destructive, real-time triangulated-to-quad preview tool. It lets you see how a triangulated mesh will look after conversion to quads without modifying the original mesh, and apply the result with a single click once you are satisfied.

In my own workflow, it serves as a pre-conversion step to manually clean up edges that Blender's built-in **Tris to Quads** algorithm handles incorrectly before performing the actual quad conversion.

## Features

- **Non-destructive**: The original triangulated mesh is fully preserved. Toggle the preview on and off at any time, and revert instantly.
  
- **One-click apply**: Write the conversion result back to the source mesh when satisfied. Supports **Ctrl+Z** undo.
  
- **Consistent with the native algorithm**: Uses Blender's built-in **Tris to Quads** algorithm under the hood, producing results identical to the operation in Edit Mode.
  
- **Full parameter control**: Supports face angle threshold, shape angle threshold, and consistency comparison for UVs, color attributes, seams, sharp edges, and materials.
  

## Use Cases

- **Architectural and hard-surface modeling**: Quickly restore clean quad topology from triangulated meshes produced by CAD imports or boolean operations.
  
- **Game asset optimization**: Check the quad conversion result before export, or reverse-convert to a clean, sculptable quad mesh.
  
- **Scan and sculpt post-processing**: Handle high-density triangulated meshes and evaluate the feasibility of quad conversion.
  
- **Teaching and demonstration**: Visually compare the topological differences between triangulated and quad meshes.

## Known Limitations:

- You cannot toggle the preview while in Edit Mode.
  
- Edits made to the preview object cannot be transferred back to the original object.
  
- If you have a better approach to handle these limitations, feel free to submit a change to me on GitHub.
