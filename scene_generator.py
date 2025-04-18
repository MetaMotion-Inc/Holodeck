import os
import json
from blender_texture import process_world_json
from ai2holodeck.main import generate_single_scene as original_generate_scene

def generate_single_scene(args):
    """
    Wrapper around the original generate_single_scene that returns the scene data
    """
    # Determine the scene file path
    base_folder_name = args.query.replace(" ", "_").replace("'", "")
    scene_dir = args.save_dir
    
    # Find the most recent timestamped folder
    matching_folders = [f for f in os.listdir(scene_dir) if f.startswith(base_folder_name)]
    if not matching_folders:
        # Run the original generation function
        save_dir = original_generate_scene(args)
        print(f"Generation complete for {args.query}. Scene saved and any other data saved to {save_dir}.")
    
        # Find the most recent timestamped folder
        # matching_folders = [f for f in os.listdir(scene_dir) if f.startswith(base_folder_name)]
        # if not matching_folders:
        #     raise FileNotFoundError(f"No folders found starting with {base_folder_name}")
    
    
    # Get the most recent folder (should be the one with the latest timestamp)
    if save_dir:
        scene_dir = save_dir
        # Find the JSON file in the save_dir
        json_files = [f for f in os.listdir(save_dir) if f.endswith('.json')]
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {save_dir}")
        
        # Use the first JSON file found
        scene_file = os.path.join(save_dir, json_files[0])
    # else:
    #     # If save_dir was not returned, use matching folders method
    #     folder_name = sorted(matching_folders)[-1]
    #     scene_dir = os.path.join(args.save_dir, folder_name)
        
    #     # Find JSON file in this directory
    #     json_files = [f for f in os.listdir(scene_dir) if f.endswith('.json')]
    #     if not json_files:
    #         raise FileNotFoundError(f"No JSON files found in {scene_dir}")
        
        # scene_file = os.path.join(scene_dir, json_files[0])
    # folder_name = sorted(matching_folders)[-1]
    # scene_dir = os.path.join(args.save_dir, folder_name)
    # scene_file = os.path.join(scene_dir, base_folder_name + ".json")

        process_world_json(scene_file, output_base_dir='scene_assets')
    
    # Read and return the generated scene data
    if os.path.exists(scene_file):
        with open(scene_file, 'r') as f:
            return json.load(f), save_dir
    else:
        raise FileNotFoundError(f"Scene file not found at {scene_file}")
