# import bpy 
# import numpy as np
# from mathutils import Vector
# import os

# def clear_scene():
#     """Remove all objects from the scene"""
#     # Select all objects
#     bpy.ops.object.select_all(action='SELECT')
#     # Delete selected objects
#     bpy.ops.object.delete()
    
#     # Also clear any orphan data blocks
#     for collection in bpy.data.collections:
#         if collection.users == 0:
#             bpy.data.collections.remove(collection)
    
#     # Clear meshes, materials, etc. that have no users
#     for block in bpy.data.meshes:
#         if block.users == 0:
#             bpy.data.meshes.remove(block)
    
#     for block in bpy.data.materials:
#         if block.users == 0:
#             bpy.data.materials.remove(block)
    
#     for block in bpy.data.textures:
#         if block.users == 0:
#             bpy.data.textures.remove(block)
            
#     for block in bpy.data.images:
#         if block.users == 0:
#             bpy.data.images.remove(block)
    
#     print("Scene cleared of all objects")

# def load_pickled_3d_asset(file_path):
#     import gzip
#     import pickle
#     # Open the compressed pickled file
#     with gzip.open(file_path, 'rb') as f:
#         # Load the pickled object
#         loaded_object_data = pickle.load(f)

#     # Create a new mesh object in Blender
#     object_id = os.path.splitext(os.path.basename(file_path))[0]  # Extract object ID from file name
#     mesh = bpy.data.meshes.new(name=f'{object_id}_Mesh')
#     obj = bpy.data.objects.new(object_id, mesh)

#     # Link the object to the scene
#     bpy.context.scene.collection.objects.link(obj)

#     # Set the mesh data for the object
#     obj.data = mesh

#     # Update the mesh with the loaded data
#     # print(loaded_object_data.keys())
#     # print(loaded_object_data['triangles'])
#     # triangles = [vertex_index for face in loaded_object_data['triangles'] for vertex_index in face]
#     triangles = np.array(loaded_object_data['triangles']).reshape(-1,3)
#     vertices = []

#     for v in loaded_object_data['vertices']:
#         vertices.append([v['x'],v['z'],v['y']])

#     mesh.from_pydata(vertices, [], triangles)

#     uvs = []
#     for uv in loaded_object_data['uvs']:
#         uvs.append([uv['x'],uv['y']]) 

#     mesh.update()

#     # Ensure UV coordinates are stored
#     if not mesh.uv_layers:
#         mesh.uv_layers.new(name="UVMap")

#     uv_layer = mesh.uv_layers["UVMap"]
#     for poly in mesh.polygons:
#         for loop_index in poly.loop_indices:
#             vertex_index = mesh.loops[loop_index].vertex_index
#             uv_layer.data[loop_index].uv = uvs[vertex_index]
    

#     material = bpy.data.materials.new(name="AlbedoMaterial")
#     obj.data.materials.append(material)

#     # Assign albedo color to the material
#     material.use_nodes = True
#     nodes = material.node_tree.nodes
#     principled_bsdf = nodes.get("Principled BSDF")

#     texture_node = nodes.new(type='ShaderNodeTexImage')

#     image_path = f"{'/'.join(file_path.split('/')[:-1])}/albedo.jpg"  # Replace with your image file path

#     image = bpy.data.images.load(image_path)

#     # Assign the image to the texture node
#     texture_node.image = image

#     # Connect the texture node to the albedo color
#     material.node_tree.links.new(
#         texture_node.outputs["Color"],
#         principled_bsdf.inputs["Base Color"]
#     )

#     # normal
#     image_path = f"{'/'.join(file_path.split('/')[:-1])}/normal.jpg"
#     img_normal = bpy.data.images.load(image_path)
#     image_texture_node_normal = material.node_tree.nodes.new(type='ShaderNodeTexImage')
#     image_texture_node_normal.image = img_normal    
#     image_texture_node_normal.image.colorspace_settings.name = 'Non-Color'

#     normal_map_node = material.node_tree.nodes.new(type='ShaderNodeNormalMap')

#     material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
#     material.node_tree.links.new(image_texture_node_normal.outputs["Color"], normal_map_node.inputs["Color"])

#     # Assign the material to the object
#     obj.data.materials[0] = material    

#     # Update mesh to apply UV changes
#     mesh.update()

#     return obj

# def view_3d_object(file_path=None, obj=None, clear=True):
#     """
#     View a 3D object in a Blender viewport
#     Args:
#         file_path: Path to the pickled 3D asset
#         obj: Alternatively, pass a pre-loaded Blender object
#         clear: Whether to clear existing scene objects first
#     """
#     if clear:
#         clear_scene()
        
#     if obj is None and file_path is not None:
#         obj = load_pickled_3d_asset(file_path)
#     elif obj is None:
#         raise ValueError("Either file_path or obj must be provided")
    
#     # Set up the viewport for viewing
#     # Deselect all objects
#     for o in bpy.context.selected_objects:
#         o.select_set(False)
    
#     # Select and make our object active
#     obj.select_set(True)
#     bpy.context.view_layer.objects.active = obj
    
#     # Create a camera if it doesn't exist
#     scene = bpy.context.scene
#     if 'Camera' not in bpy.data.objects:
#         camera_data = bpy.data.cameras.new(name='Camera')
#         camera = bpy.data.objects.new('Camera', camera_data)
#         scene.collection.objects.link(camera)
#     else:
#         camera = bpy.data.objects['Camera']
    
#     # Make sure object has bound_box initialized
#     bpy.context.view_layer.update()
    
#     # Position camera based on object's bounding box
#     bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
#     bbox_center = sum((Vector(b) for b in bbox_corners), Vector()) / 8
    
#     # Set camera location 
#     obj_dimensions = obj.dimensions
#     max_dim = max(obj_dimensions.x, obj_dimensions.y, obj_dimensions.z)
#     camera.location = bbox_center + Vector((0, -max_dim * 2.5, max_dim * 0.8))
    
#     # Point camera to the object
#     direction = bbox_center - camera.location
#     rot_quat = direction.to_track_quat('-Z', 'Y')
#     camera.rotation_euler = rot_quat.to_euler()
    
#     # Set camera as active
#     scene.camera = camera
    
#     # Add a light if there isn't one
#     if not any(o.type == 'LIGHT' for o in bpy.data.objects):
#         light_data = bpy.data.lights.new(name="Light", type='SUN')
#         light_data.energy = 5.0
#         light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
#         scene.collection.objects.link(light_obj)
#         light_obj.location = bbox_center + Vector((max_dim, -max_dim, max_dim * 2))
#         light_obj.rotation_euler = (0.8, 0.3, 0.4)
    
#     # Set shading to material preview if UI is available
#     # for area in bpy.context.screen.areas:
#     #     if area.type == 'VIEW_3D':
#     #         for space in area.spaces:
#     #             if space.type == 'VIEW_3D':
#     #                 space.shading.type = 'MATERIAL'
#     #                 # Safe override for context
#     #                 with bpy.context.temp_override(area=area):
#     #                     try:
#     #                         bpy.ops.view3d.view_selected()
#     #                     except:
#     #                         print("Could not execute view_selected in this context")
    
#     print(f"Viewing 3D object: {obj.name}")
#     return obj

# def export_for_threejs(obj, output_dir=None, format='GLB'):
#     """
#     Export the 3D object in a format compatible with Three.js
    
#     Args:
#         obj: The Blender object to export
#         output_dir: Directory to save the exported file (default: same as blend file)
#         format: Export format - 'GLB', 'GLTF', 'OBJ', or 'FBX'
        
#     Returns:
#         Path to the exported file
#     """
#     if output_dir is None:
#         # Use the same directory as the blend file or current directory
#         if bpy.data.filepath:
#             output_dir = os.path.dirname(bpy.data.filepath)
#         else:
#             output_dir = os.getcwd()
    
#     # Ensure output_dir is an absolute path
#     output_dir = os.path.abspath(output_dir)
#     print(f"Export directory: {output_dir}")
    
#     # Create the directory if it doesn't exist
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Deselect all objects
#     bpy.ops.object.select_all(action='DESELECT')
    
#     # Select the object to export
#     obj.select_set(True)
    
#     # Set the object as active
#     bpy.context.view_layer.objects.active = obj
    
#     # Check available exporters
#     available_exporters = dir(bpy.ops.export_scene)
#     print(f"Available exporters: {available_exporters}")
    
#     # Determine file extension and export function based on format
#     format = format.upper()
#     export_path = None
    
#     # Try different export formats based on what's available
#     if format == 'GLB' or format == 'GLTF':
#         if 'gltf' in available_exporters:
#             file_ext = '.glb' if format == 'GLB' else '.gltf'
#             # Remove .pkl from the object name if it exists
#             clean_name = obj.name.replace('.pkl', '')
#             export_path = os.path.join(output_dir, f"{clean_name}{file_ext}")
            
#             print(f"Attempting to export to: {export_path}")
            
#             try:
#                 # Simple GLTF export
#                 bpy.ops.export_scene.gltf(
#                     filepath=export_path,
#                     export_format='GLB' if format == 'GLB' else 'GLTF_SEPARATE',
#                     use_selection=True
#                 )
#             except Exception as e:
#                 print(f"GLTF export failed: {str(e)}")
#                 export_path = None
#         else:
#             print("GLTF exporter not available")
    
#     # Try OBJ export
#     if export_path is None and 'obj' in available_exporters:
#         export_path = os.path.join(output_dir, f"{obj.name}.obj")
#         try:
#             bpy.ops.export_scene.obj(
#                 filepath=export_path,
#                 use_selection=True,
#                 use_materials=True
#             )
#         except Exception as e:
#             print(f"OBJ export failed: {str(e)}")
#             export_path = None
    
#     # Try FBX export
#     if export_path is None and 'fbx' in available_exporters:
#         export_path = os.path.join(output_dir, f"{obj.name}.fbx")
#         try:
#             bpy.ops.export_scene.fbx(
#                 filepath=export_path,
#                 use_selection=True,
#                 path_mode='COPY'
#             )
#         except Exception as e:
#             print(f"FBX export failed: {str(e)}")
#             export_path = None
    
#     # Try 3DS export
#     if export_path is None and '3ds' in available_exporters:
#         export_path = os.path.join(output_dir, f"{obj.name}.3ds")
#         try:
#             bpy.ops.export_scene.autodesk_3ds(
#                 filepath=export_path,
#                 use_selection=True
#             )
#         except Exception as e:
#             print(f"3DS export failed: {str(e)}")
#             export_path = None
    
#     # As a last resort, try saving to a Blender file
#     if export_path is None:
#         print("All exporters failed, saving as .blend file")
#         # Save to a blend file
#         export_path = os.path.join(output_dir, f"{obj.name}.blend")
#         # Save current file (only the selected object)
#         bpy.ops.wm.save_as_mainfile(
#             filepath=export_path,
#             copy=True,
#             compress=True
#         )
    
#     # Verify the file was created
#     if export_path and os.path.exists(export_path):
#         print(f"Successfully exported {obj.name} to {export_path}")
#         return export_path
#     else:
#         print(f"Warning: No export file created")
        
#         # Generate a simple JSON with vertices and faces as a last resort
#         json_path = os.path.join(output_dir, f"{obj.name}.json")
#         try:
#             import json
#             # Get mesh data
#             mesh = obj.data
#             vertices = [[v.co.x, v.co.y, v.co.z] for v in mesh.vertices]
#             faces = [[p.vertices[i] for i in range(len(p.vertices))] for p in mesh.polygons]
            
#             # Create a simple JSON with basic geometry
#             mesh_data = {
#                 'vertices': vertices,
#                 'faces': faces,
#                 'name': obj.name
#             }
            
#             # Add UV coordinates if available
#             if mesh.uv_layers:
#                 uv_layer = mesh.uv_layers.active
#                 uvs = []
#                 for poly in mesh.polygons:
#                     for loop_idx in poly.loop_indices:
#                         uvs.append([uv_layer.data[loop_idx].uv.x, uv_layer.data[loop_idx].uv.y])
#                 mesh_data['uvs'] = uvs
            
#             # Save to JSON
#             with open(json_path, 'w') as f:
#                 json.dump(mesh_data, f)
            
#             print(f"Created fallback JSON geometry at {json_path}")
#             return json_path
            
#         except Exception as e:
#             print(f"JSON fallback also failed: {str(e)}")
#             raise RuntimeError(f"Failed to export {obj.name} in any format")

# def process_and_export_3d_asset(file_path, output_dir=None, format='GLB', render_preview=True):
#     """
#     Load a pickled 3D asset, view it, and export it for Three.js
    
#     Args:
#         file_path: Path to the pickled 3D asset
#         output_dir: Directory to save the exported file
#         format: Export format - 'GLB', 'GLTF', 'OBJ', or 'FBX'
#         render_preview: Whether to render a preview image
        
#     Returns:
#         Path to the exported file
#     """
#     # Clear the scene
#     clear_scene()
    
#     # Load the object
#     obj = load_pickled_3d_asset(file_path)
    
#     # Set up the scene for viewing
#     view_3d_object(obj=obj, clear=False)
    
#     # Export the object
#     export_path = export_for_threejs(obj, output_dir, format)
    
#     # Render a preview if requested
#     if render_preview:
#         preview_path = os.path.splitext(export_path)[0] + '_preview.png'
#         bpy.context.scene.render.filepath = preview_path
#         bpy.context.scene.render.image_settings.file_format = 'PNG'
#         bpy.ops.render.render(write_still=True)
#         print(f"Rendered preview to {preview_path}")
    
#     return export_path

# def process_world_json(world_data, output_base_path="./exported_assets"):
#     """
#     Process a world JSON file and convert all referenced 3D assets
    
#     Args:
#         json_file_path: Path to the world JSON file
#         output_base_path: Base directory to save the exported assets
        
#     Returns:
#         Dictionary mapping original asset IDs to exported file paths
#     """
#     import json
    
#     # Load the JSON file
#     # print(f"Processing world JSON: {json_file_path}")
#     # with open(json_file_path, 'r') as f:
#     #     world_data = json.load(f)
    
#     # Track processed assets to avoid duplicates
#     print(f"Blender version: {bpy.app.version_string}")
#     processed_assets = {}
    
#     # Process all objects in the world
#     if 'objects' in world_data:
#         for obj in world_data['objects']:
#             if 'assetId' in obj:
#                 asset_id = obj['assetId']
#                 if asset_id and asset_id not in processed_assets:
#                     try:
#                         # Construct the path to the asset's pickle file
#                         asset_dir = os.path.join("/home/gaurav/.objathor-assets/2023_09_23/assets", asset_id)
#                         asset_file = os.path.join(asset_dir, f"{asset_id}.pkl.gz")
                        
#                         if not os.path.exists(asset_file):
#                             print(f"Warning: Asset file not found: {asset_file}")
#                             continue
                            
#                         # Export the asset
#                         output_path = process_and_export_3d_asset(
#                             asset_file,
#                             output_dir=os.path.join(output_base_path, asset_id),
#                             format='GLB',
#                             render_preview=True
#                         )
                        
#                         processed_assets[asset_id] = output_path
#                         print(f"Successfully processed asset: {asset_id}")
                        
#                     except Exception as e:
#                         print(f"Error processing asset {asset_id}: {str(e)}")
#                         processed_assets[asset_id] = None
    
#     # Save a summary of processed assets
#     summary_file = os.path.join(output_base_path, "processed_assets.json")
#     with open(summary_file, 'w') as f:
#         json.dump(processed_assets, f, indent=2)
    
#     print(f"\nProcessing complete!")
#     print(f"Total assets found: {len(processed_assets)}")
#     print(f"Successfully exported: {len([p for p in processed_assets.values() if p])}")
#     print(f"Summary saved to: {summary_file}")
    
#     return processed_assets

# if __name__ == "__main__":
#     # Example usage
#     import sys
    
#     # Process a specific asset if provided
#     if len(sys.argv) > 1:
#         file_path = sys.argv[1]
#         if file_path.endswith('.json'):
#             # Process entire world
#             process_world_json(file_path)
#         else:
#             # Process single asset
#             process_and_export_3d_asset(
#                 file_path,
#                 output_dir="./exported_assets",
#                 format='GLB',
#                 render_preview=True
#             )
#     else:
#         # Default example
#         file_path = "./scene_assets/86ab9a63464d431f982c0fb503783227/86ab9a63464d431f982c0fb503783227.pkl.gz"
#         process_and_export_3d_asset(file_path)


import bpy 
import numpy as np
from mathutils import Vector
import os

def clear_scene():
    """Remove all objects from the scene"""
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    # Delete selected objects
    bpy.ops.object.delete()
    
    # Also clear any orphan data blocks
    for collection in bpy.data.collections:
        if collection.users == 0:
            bpy.data.collections.remove(collection)
    
    # Clear meshes, materials, etc. that have no users
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
            
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)
    
    print("Scene cleared of all objects")

def load_pickled_3d_asset(file_path):
    import gzip
    import pickle
    # Open the compressed pickled file
    with gzip.open(file_path, 'rb') as f:
        # Load the pickled object
        loaded_object_data = pickle.load(f)

    # Create a new mesh object in Blender
    object_id = os.path.splitext(os.path.basename(file_path))[0]  # Extract object ID from file name
    mesh = bpy.data.meshes.new(name=f'{object_id}_Mesh')
    obj = bpy.data.objects.new(object_id, mesh)

    # Link the object to the scene
    bpy.context.scene.collection.objects.link(obj)

    # Set the mesh data for the object
    obj.data = mesh

    # Update the mesh with the loaded data
    # print(loaded_object_data.keys())
    # print(loaded_object_data['triangles'])
    # triangles = [vertex_index for face in loaded_object_data['triangles'] for vertex_index in face]
    triangles = np.array(loaded_object_data['triangles']).reshape(-1,3)
    vertices = []

    for v in loaded_object_data['vertices']:
        vertices.append([v['x'],v['z'],v['y']])

    mesh.from_pydata(vertices, [], triangles)

    uvs = []
    for uv in loaded_object_data['uvs']:
        uvs.append([uv['x'],uv['y']]) 

    mesh.update()

    # Ensure UV coordinates are stored
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    uv_layer = mesh.uv_layers["UVMap"]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
    

    material = bpy.data.materials.new(name="AlbedoMaterial")
    obj.data.materials.append(material)

    # Assign albedo color to the material
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")

    texture_node = nodes.new(type='ShaderNodeTexImage')

    image_path = f"{'/'.join(file_path.split('/')[:-1])}/albedo.jpg"  # Replace with your image file path

    image = bpy.data.images.load(image_path)

    # Assign the image to the texture node
    texture_node.image = image

    # Connect the texture node to the albedo color
    material.node_tree.links.new(
        texture_node.outputs["Color"],
        principled_bsdf.inputs["Base Color"]
    )

    # normal
    image_path = f"{'/'.join(file_path.split('/')[:-1])}/normal.jpg"
    img_normal = bpy.data.images.load(image_path)
    image_texture_node_normal = material.node_tree.nodes.new(type='ShaderNodeTexImage')
    image_texture_node_normal.image = img_normal    
    image_texture_node_normal.image.colorspace_settings.name = 'Non-Color'

    normal_map_node = material.node_tree.nodes.new(type='ShaderNodeNormalMap')

    material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
    material.node_tree.links.new(image_texture_node_normal.outputs["Color"], normal_map_node.inputs["Color"])

    # Assign the material to the object
    obj.data.materials[0] = material    

    # Update mesh to apply UV changes
    mesh.update()

    return obj

def view_3d_object(file_path=None, obj=None, clear=True):
    """
    View a 3D object in a Blender viewport
    Args:
        file_path: Path to the pickled 3D asset
        obj: Alternatively, pass a pre-loaded Blender object
        clear: Whether to clear existing scene objects first
    """
    if clear:
        clear_scene()
        
    if obj is None and file_path is not None:
        obj = load_pickled_3d_asset(file_path)
    elif obj is None:
        raise ValueError("Either file_path or obj must be provided")
    
    # Set up the viewport for viewing
    # Deselect all objects
    for o in bpy.context.selected_objects:
        o.select_set(False)
    
    # Select and make our object active
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Create a camera if it doesn't exist
    scene = bpy.context.scene
    if 'Camera' not in bpy.data.objects:
        camera_data = bpy.data.cameras.new(name='Camera')
        camera = bpy.data.objects.new('Camera', camera_data)
        scene.collection.objects.link(camera)
    else:
        camera = bpy.data.objects['Camera']
    
    # Make sure object has bound_box initialized
    bpy.context.view_layer.update()
    
    # Position camera based on object's bounding box
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    bbox_center = sum((Vector(b) for b in bbox_corners), Vector()) / 8
    
    # Set camera location 
    obj_dimensions = obj.dimensions
    max_dim = max(obj_dimensions.x, obj_dimensions.y, obj_dimensions.z)
    camera.location = bbox_center + Vector((0, -max_dim * 2.5, max_dim * 0.8))
    
    # Point camera to the object
    direction = bbox_center - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Set camera as active
    scene.camera = camera
    
    # Add a light if there isn't one
    if not any(o.type == 'LIGHT' for o in bpy.data.objects):
        light_data = bpy.data.lights.new(name="Light", type='SUN')
        light_data.energy = 5.0
        light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
        scene.collection.objects.link(light_obj)
        light_obj.location = bbox_center + Vector((max_dim, -max_dim, max_dim * 2))
        light_obj.rotation_euler = (0.8, 0.3, 0.4)
    
    # Set shading to material preview if UI is available
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    # Safe override for context
                    with bpy.context.temp_override(area=area):
                        try:
                            bpy.ops.view3d.view_selected()
                        except:
                            print("Could not execute view_selected in this context")
    
    print(f"Viewing 3D object: {obj.name}")
    return obj

def export_for_threejs(obj, output_dir=None, format='GLB'):
    """
    Export the 3D object in a format compatible with Three.js
    
    Args:
        obj: The Blender object to export
        output_dir: Directory to save the exported file (default: same as blend file)
        format: Export format - 'GLB', 'GLTF', 'OBJ', or 'FBX'
        
    Returns:
        Path to the exported file
    """
    if output_dir is None:
        # Use the same directory as the blend file or current directory
        if bpy.data.filepath:
            output_dir = os.path.dirname(bpy.data.filepath)
        else:
            output_dir = os.getcwd()
    
    # Ensure output_dir is an absolute path
    output_dir = os.path.abspath(output_dir)
    print(f"Export directory: {output_dir}")
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select the object to export
    obj.select_set(True)
    
    # Set the object as active
    bpy.context.view_layer.objects.active = obj
    
    # Check available exporters
    available_exporters = dir(bpy.ops.export_scene)
    print(f"Available exporters: {available_exporters}")
    
    # Determine file extension and export function based on format
    format = format.upper()
    export_path = None
    
    # Try different export formats based on what's available
    if format == 'GLB' or format == 'GLTF':
        if 'gltf' in available_exporters:
            file_ext = '.glb' if format == 'GLB' else '.gltf'
            # Remove .pkl from the object name if it exists
            clean_name = obj.name.replace('.pkl', '')
            export_path = os.path.join(output_dir, f"{clean_name}{file_ext}")
            
            print(f"Attempting to export to: {export_path}")
            
            try:
                # Simple GLTF export
                bpy.ops.export_scene.gltf(
                    filepath=export_path,
                    export_format='GLB' if format == 'GLB' else 'GLTF_SEPARATE',
                    use_selection=True
                )
            except Exception as e:
                print(f"GLTF export failed: {str(e)}")
                export_path = None
        else:
            print("GLTF exporter not available")
    
    # Try OBJ export
    if export_path is None and 'obj' in available_exporters:
        export_path = os.path.join(output_dir, f"{obj.name}.obj")
        try:
            bpy.ops.export_scene.obj(
                filepath=export_path,
                use_selection=True,
                use_materials=True
            )
        except Exception as e:
            print(f"OBJ export failed: {str(e)}")
            export_path = None
    
    # Try FBX export
    if export_path is None and 'fbx' in available_exporters:
        export_path = os.path.join(output_dir, f"{obj.name}.fbx")
        try:
            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=True,
                path_mode='COPY'
            )
        except Exception as e:
            print(f"FBX export failed: {str(e)}")
            export_path = None
    
    # Try 3DS export
    if export_path is None and '3ds' in available_exporters:
        export_path = os.path.join(output_dir, f"{obj.name}.3ds")
        try:
            bpy.ops.export_scene.autodesk_3ds(
                filepath=export_path,
                use_selection=True
            )
        except Exception as e:
            print(f"3DS export failed: {str(e)}")
            export_path = None
    
    # As a last resort, try saving to a Blender file
    if export_path is None:
        print("All exporters failed, saving as .blend file")
        # Save to a blend file
        export_path = os.path.join(output_dir, f"{obj.name}.blend")
        # Save current file (only the selected object)
        bpy.ops.wm.save_as_mainfile(
            filepath=export_path,
            copy=True,
            compress=True
        )
    
    # Verify the file was created
    if export_path and os.path.exists(export_path):
        print(f"Successfully exported {obj.name} to {export_path}")
        return export_path
    else:
        print(f"Warning: No export file created")
        
        # Generate a simple JSON with vertices and faces as a last resort
        json_path = os.path.join(output_dir, f"{obj.name}.json")
        try:
            import json
            # Get mesh data
            mesh = obj.data
            vertices = [[v.co.x, v.co.y, v.co.z] for v in mesh.vertices]
            faces = [[p.vertices[i] for i in range(len(p.vertices))] for p in mesh.polygons]
            
            # Create a simple JSON with basic geometry
            mesh_data = {
                'vertices': vertices,
                'faces': faces,
                'name': obj.name
            }
            
            # Add UV coordinates if available
            if mesh.uv_layers:
                uv_layer = mesh.uv_layers.active
                uvs = []
                for poly in mesh.polygons:
                    for loop_idx in poly.loop_indices:
                        uvs.append([uv_layer.data[loop_idx].uv.x, uv_layer.data[loop_idx].uv.y])
                mesh_data['uvs'] = uvs
            
            # Save to JSON
            with open(json_path, 'w') as f:
                json.dump(mesh_data, f)
            
            print(f"Created fallback JSON geometry at {json_path}")
            return json_path
            
        except Exception as e:
            print(f"JSON fallback also failed: {str(e)}")
            raise RuntimeError(f"Failed to export {obj.name} in any format")

def process_and_export_3d_asset(file_path, output_dir=None, format='GLB', render_preview=True):
    """
    Load a pickled 3D asset, view it, and export it for Three.js
    
    Args:
        file_path: Path to the pickled 3D asset
        output_dir: Directory to save the exported file
        format: Export format - 'GLB', 'GLTF', 'OBJ', or 'FBX'
        render_preview: Whether to render a preview image
        
    Returns:
        Path to the exported file
    """
    # Clear the scene
    clear_scene()
    
    # Load the object
    obj = load_pickled_3d_asset(file_path)
    
    # Set up the scene for viewing
    # view_3d_object(obj=obj, clear=False)
    
    # Export the object
    export_path = export_for_threejs(obj, output_dir, format)
    
    # Render a preview if requested
    if render_preview:
        preview_path = os.path.splitext(export_path)[0] + '_preview.png'
        bpy.context.scene.render.filepath = preview_path
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.ops.render.render(write_still=True)
        print(f"Rendered preview to {preview_path}")
    
    return export_path

def process_world_json(json_file_path, output_base_dir="./exported_assets"):
    """
    Process a world JSON file and convert all referenced 3D assets
    
    Args:
        json_file_path: Path to the world JSON file
        output_base_dir: Base directory to save the exported assets
        
    Returns:
        Dictionary mapping original asset IDs to exported file paths
    """
    import json
    
    # Load the JSON file
    print(f"Processing world JSON: {json_file_path}")
    with open(json_file_path, 'r') as f:
        world_data = json.load(f)
    
    # Track processed assets to avoid duplicates
    processed_assets = {}
    
    # Process all objects in the world
    if 'objects' in world_data:
        for obj in world_data['objects']:
            if 'assetId' in obj:
                asset_id = obj['assetId']
                if asset_id and asset_id not in processed_assets:
                    try:
                        # Construct the path to the asset's pickle file
                        asset_dir = os.path.join("/home/gaurav/.objathor-assets/2023_09_23/assets", asset_id)
                        asset_file = os.path.join(asset_dir, f"{asset_id}.pkl.gz")
                        
                        if not os.path.exists(asset_file):
                            print(f"Warning: Asset file not found: {asset_file}")
                            continue
                            
                        # Export the asset
                        output_path = process_and_export_3d_asset(
                            asset_file,
                            output_dir=os.path.join(output_base_dir, asset_id),
                            format='GLB',
                            render_preview=True
                        )
                        
                        processed_assets[asset_id] = output_path
                        print(f"Successfully processed asset: {asset_id}")
                        
                    except Exception as e:
                        print(f"Error processing asset {asset_id}: {str(e)}")
                        processed_assets[asset_id] = None
    
    # Save a summary of processed assets
    summary_file = os.path.join(output_base_dir, "processed_assets.json")
    with open(summary_file, 'w') as f:
        json.dump(processed_assets, f, indent=2)
    
    print(f"\nProcessing complete!")
    print(f"Total assets found: {len(processed_assets)}")
    print(f"Successfully exported: {len([p for p in processed_assets.values() if p])}")
    print(f"Summary saved to: {summary_file}")
    
    return processed_assets

if __name__ == "__main__":
    # Example usage
    import sys
    
    # Process a specific asset if provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith('.json'):
            # Process entire world
            process_world_json(file_path)
        else:
            # Process single asset
            process_and_export_3d_asset(
                file_path,
                output_dir="./exported_assets",
                format='GLB',
                render_preview=True
            )
    else:
        # Default example
        file_path = "./scene_assets/86ab9a63464d431f982c0fb503783227/86ab9a63464d431f982c0fb503783227.pkl.gz"
        process_and_export_3d_asset(file_path)