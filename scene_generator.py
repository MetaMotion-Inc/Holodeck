import os
import json
from ai2holodeck.main import generate_single_scene as original_generate_scene

def generate_single_scene(args):
    """
    Wrapper around the original generate_single_scene that returns the scene data
    """
    # Run the original generation function
    original_generate_scene(args)
    
    # Determine the scene file path
    base_folder_name = args.query.replace(" ", "_").replace("'", "")
    scene_dir = args.save_dir
    
    # Find the most recent timestamped folder
    matching_folders = [f for f in os.listdir(scene_dir) if f.startswith(base_folder_name)]
    if not matching_folders:
        raise FileNotFoundError(f"No folders found starting with {base_folder_name}")
    
    # Get the most recent folder (should be the one with the latest timestamp)
    folder_name = sorted(matching_folders)[-1]
    scene_dir = os.path.join(args.save_dir, folder_name)
    scene_file = os.path.join(scene_dir, base_folder_name + ".json")
    
    # Read and return the generated scene data
    if os.path.exists(scene_file):
        with open(scene_file, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Scene file not found at {scene_file}")
