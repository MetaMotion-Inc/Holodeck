import os
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from argparse import Namespace
import ast
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from ai2holodeck.main import generate_multi_scenes, generate_variants
from ai2holodeck.generation.holodeck import Holodeck
from scene_generator import generate_single_scene
from ai2holodeck.constants import OBJATHOR_ASSETS_DIR

from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

import json 
import asyncio

from blender_world import process_world_json


app = FastAPI(title="Holodeck API", description="API for generating 3D scenes with AI")
executor = ThreadPoolExecutor(max_workers=4)

created_scenes = json.load(open("created_scenes.json", "r"))['created_scenes']
print("Created scenes loaded: ", created_scenes)

# Models for request validation
class SceneGenerationRequest(BaseModel):
    query: str = Field(..., description="Query to generate scene from")
    original_scene: Optional[str] = Field(None, description="Path to original scene file")
    save_dir: str = Field("./data/scenes", description="Directory to save scene to")
    generate_image: bool = Field(True, description="Whether to generate an image of the scene")
    generate_video: bool = Field(False, description="Whether to generate a video of the scene")
    add_ceiling: bool = Field(False, description="Whether to add a ceiling to the scene")
    add_time: bool = Field(True, description="Whether to add the time to the scene name")
    use_constraint: bool = Field(True, description="Whether to use constraints")
    use_milp: bool = Field(False, description="Whether to use mixed integer linear programming")
    random_selection: bool = Field(False, description="Whether to use more random object selection")
    used_assets: List[str] = Field([], description="List of assets to exclude from the scene")
    single_room: bool = Field(False, description="Whether to generate a single room scene")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_org: Optional[str] = Field(None, description="OpenAI organization")

class MultiSceneGenerationRequest(BaseModel):
    query_file: str = Field(..., description="Path to file containing queries")
    save_dir: str = Field("./data/scenes", description="Directory to save scenes to")
    generate_image: bool = Field(True, description="Whether to generate an image of the scene")
    generate_video: bool = Field(False, description="Whether to generate a video of the scene")
    add_ceiling: bool = Field(False, description="Whether to add a ceiling to the scene")
    add_time: bool = Field(True, description="Whether to add the time to the scene name")
    use_constraint: bool = Field(True, description="Whether to use constraints")
    use_milp: bool = Field(False, description="Whether to use mixed integer linear programming")
    random_selection: bool = Field(False, description="Whether to use more random object selection")
    used_assets: List[str] = Field([], description="List of assets to exclude from the scene")
    single_room: bool = Field(False, description="Whether to generate a single room scene")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_org: Optional[str] = Field(None, description="OpenAI organization")

class VariantGenerationRequest(BaseModel):
    query: str = Field(..., description="Query to generate variants from")
    original_scene: str = Field(..., description="Path to original scene file")
    save_dir: str = Field("./data/scenes", description="Directory to save variants to")
    number_of_variants: int = Field(5, description="Number of variants to generate")
    used_assets: List[str] = Field([], description="List of assets to exclude from the scene")
    single_room: bool = Field(False, description="Whether to generate a single room scene")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_org: Optional[str] = Field(None, description="OpenAI organization")

class GenerationResponse(BaseModel):
    success: bool
    message: str
    save_dir: Optional[str] = None
    scene_data: Optional[dict] = None  # Add this field to store the scene JSON

# Simplified request model that only requires the text prompt - renamed for clarity
class SimpleSceneRequest(BaseModel):
    scene_description: str = Field(..., description="Text description of the scene to generate")

class SimpleProcessingRequest(BaseModel):
    scene_dir: str = Field(..., description="Directory containing the scene to process")

# Helper function to create args namespace
def create_args_namespace(request_data, model):
    args = Namespace()
    
    for key, value in request_data.dict().items():
        setattr(args, key, value)
    
    # Convert boolean values to strings for the original functions
    for bool_arg in ['generate_image', 'generate_video', 'add_ceiling', 'add_time', 
                    'use_constraint', 'use_milp', 'random_selection', 'single_room']:
        if hasattr(args, bool_arg):
            setattr(args, bool_arg, str(getattr(args, bool_arg)))
    
    args.model = model
    args.generate_image = "True"
    args.generate_video = "False"
    
    return args

# Initialize Holodeck model
def init_holodeck(single_room, openai_api_key=None, openai_org=None):
    if openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if openai_org is None:
        openai_org = os.environ.get("OPENAI_ORG")
    
    return Holodeck(
        openai_api_key=openai_api_key,
        openai_org=openai_org,
        objaverse_asset_dir=OBJATHOR_ASSETS_DIR,
        single_room=single_room,
    )

# API Endpoints
@app.post("/generate_scene", response_model=GenerationResponse)
async def api_generate_scene(request: SceneGenerationRequest, background_tasks: BackgroundTasks):
    try:
        model = init_holodeck(
            single_room=request.single_room,
            openai_api_key=request.openai_api_key,
            openai_org=request.openai_org
        )
        
        args = create_args_namespace(request, model)
        
        # Make sure the save directory exists
        os.makedirs(args.save_dir, exist_ok=True)
        
        # Process used_assets if it's a file path
        if len(args.used_assets) == 1 and args.used_assets[0].endswith('.txt'):
            with open(args.used_assets[0], "r") as f:
                args.used_assets = [asset.strip() for asset in f.readlines()]
        
        # Run in background to avoid timeout for long-running tasks
        background_tasks.add_task(generate_single_scene, args)
        
        folder_name = args.query.replace(" ", "_").replace("'", "")
        save_path = os.path.join(args.save_dir, folder_name)
        
        return GenerationResponse(
            success=True,
            message=f"Scene generation started for query: {request.query}. Results will be saved to {save_path}",
            save_dir=save_path
        )
    except Exception as e:
        return GenerationResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

@app.post("/generate_multi_scenes", response_model=GenerationResponse)
async def api_generate_multi_scenes(request: MultiSceneGenerationRequest, background_tasks: BackgroundTasks):
    try:
        model = init_holodeck(
            single_room=request.single_room,
            openai_api_key=request.openai_api_key,
            openai_org=request.openai_org
        )
        
        args = create_args_namespace(request, model)
        
        # Make sure the save directory exists
        os.makedirs(args.save_dir, exist_ok=True)
        
        # Process used_assets if it's a file path
        if len(args.used_assets) == 1 and args.used_assets[0].endswith('.txt'):
            with open(args.used_assets[0], "r") as f:
                args.used_assets = [asset.strip() for asset in f.readlines()]
        
        # Run in background to avoid timeout for long-running tasks
        background_tasks.add_task(generate_multi_scenes, args)
        
        return GenerationResponse(
            success=True,
            message=f"Multi-scene generation started using queries from {request.query_file}. Results will be saved to {request.save_dir}",
            save_dir=request.save_dir
        )
    except Exception as e:
        return GenerationResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

@app.post("/generate_variants", response_model=GenerationResponse)
async def api_generate_variants(request: VariantGenerationRequest, background_tasks: BackgroundTasks):
    try:
        model = init_holodeck(
            single_room=request.single_room,
            openai_api_key=request.openai_api_key,
            openai_org=request.openai_org
        )
        
        args = create_args_namespace(request, model)
        args.number_of_variants = str(request.number_of_variants)
        
        # Make sure the save directory exists
        os.makedirs(args.save_dir, exist_ok=True)
        
        # Process used_assets if it's a file path
        if len(args.used_assets) == 1 and args.used_assets[0].endswith('.txt'):
            with open(args.used_assets[0], "r") as f:
                args.used_assets = [asset.strip() for asset in f.readlines()]
        
        # Run in background to avoid timeout for long-running tasks
        background_tasks.add_task(generate_variants, args)
        
        return GenerationResponse(
            success=True,
            message=f"Variant generation started for query: {request.query}. Results will be saved to {request.save_dir}",
            save_dir=request.save_dir
        )
    except Exception as e:
        return GenerationResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

def cpu_bound_task(request):
    try:
        # Create a full request with defaults
        full_request = SceneGenerationRequest(
            query=request.scene_description,
            original_scene=None,
            save_dir="./data/scenes",
            generate_image=False,
            generate_video=False,
            add_ceiling=False,
            add_time=True,
            use_constraint=True,
            use_milp=False,
            random_selection=False,
            used_assets=[],
            single_room=False,
            openai_api_key=None,
            openai_org=None
        )
        
        model = init_holodeck(
            single_room=False,
            openai_api_key=None,
            openai_org=None
        )
        
        args = create_args_namespace(full_request, model)
       
        os.makedirs(args.save_dir, exist_ok=True)
        print("----------------------- Save dir: ", args.save_dir)
        print("----------------------- Query: ", args.query)
        print(f"{args.query in list(created_scenes.keys())}")
        

        # Check if GLB for that scene already exists
        query = args.query
        # args.generate_image = "False"
        # args.generate_video = "False"
        
        if query in list(created_scenes.keys()):    
            print("Scene already exists in the cache.")
            save_path =  created_scenes[query]
            scene_data = {}
            import time
            # time.sleep(2*60)
            

        else:
            # Use our wrapper function that returns the scene data
            print("Generating new scene...")
            scene_data, save_path = generate_single_scene(args)
            created_scenes[query] = save_path
            print("Scene generated and saved to: ", save_path)
            # Save the updated created_scenes dictionary to the JSON file
            with open("created_scenes.json", "w") as f:
                json.dump({"created_scenes": created_scenes}, f, indent=4)
        
        
        return GenerationResponse(
            success=True,
            message=f"Scene generated successfully",
            save_dir=save_path,
            scene_data=scene_data
        )
    
    except Exception as e:
        return GenerationResponse(
            success=False,
            message=f"Error: {str(e)}",
            scene_data=None,
        )

# Update the simplified endpoint to only accept scene_description
@app.post("/generate", response_model=GenerationResponse)
async def generate_from_prompt(request: SimpleSceneRequest, background_tasks: BackgroundTasks):

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, cpu_bound_task, request)
    return result

    
@app.post("/process_file", response_model=GenerationResponse)
async def process_file(request: SimpleProcessingRequest, background_tasks: BackgroundTasks):
     # Post process the textures
    scene_dir = request.scene_dir
    save_dir = scene_dir #os.path.sep.join(scene_dir.split("/")[:-1])

    print("Scene dir: ", scene_dir)
    print("Save dir: ", save_dir)
    
    # Find the JSON file in the save_dir
    # CHeck if glb file exists
    glb_files = [f for f in os.listdir(scene_dir) if f.endswith('.glb')]
    if not glb_files:

        json_files = [f for f in os.listdir(scene_dir) if f.endswith('.json')]
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {scene_dir}")
        
        else:
            # Use the first JSON file found
            scene_file = os.path.join(scene_dir, json_files[0])

            opt = {
                "output": os.path.join(save_dir, "processed"),
                "json": scene_file,
                "content": "/home/gaurav/MetaMotion/Deployment/Holodeck/assets/",  # Adjust path as needed
                "objaverse_path": "/home/gaurav/.objathor-assets/"  # Adjust path as needed
            }
            
            class DictAsObject:
                def __init__(self, d):
                    self.__dict__.update(d)

            opt = DictAsObject(opt)
            
            print(opt.json)
            os.makedirs(opt.output, exist_ok=True)
            
            output_path = process_world_json(opt)

            return GenerationResponse(
                success=True,
                message=f"Scene processed successfully",
                save_dir=save_dir,
                scene_data=None
            )
    else:
        # Use the first GLB file found
        return GenerationResponse(
            success=True,
            message=f"Scene processed successfully",
            save_dir=save_dir,
            scene_data=None
        )


# Additional endpoint to serve the downloaded file
@app.get("/{hash_id}")
async def get_file(hash_id: str):
    file_path = f"scene_assets/{hash_id}/{hash_id}.glb"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="model/gltf-binary",
        filename=f"{hash_id}.glb"
        )

@app.get("/scene/{scene_file}")
def process_scene(scene_file: str):
    """
    Process the scene file and return glb.
    """
    file_path = f"data/scenes/{scene_file}"
    print("File path: ", file_path)

    # Find the GLB file in the directory
    glb_files = []
    if os.path.exists(file_path):
        glb_files = [f for f in os.listdir(file_path) if f.endswith('.glb')]
    
    if not glb_files:
        raise HTTPException(status_code=404, detail="No GLB file found")
    
    # Use the first GLB file found
    glb_filepath = os.path.join(file_path, glb_files[0])
    if not os.path.exists(glb_filepath):
        raise HTTPException(status_code=404, detail="GLB file not found")
    
    return FileResponse(
        glb_filepath,
        media_type="model/gltf-binary",
        filename=f"{glb_files[0]}"
        )
    

@app.get("/thumbnail/{save_dir}")
async def get_thumbnail(save_dir: str):
    # Find the first PNG file in the save directory
    for dirs in os.listdir("data/scenes"):
        if dirs.startswith(save_dir):
            save_dir = dirs
            break
        
    save_dir = os.path.join("data", "scenes", save_dir)

    if os.path.exists(save_dir):
        png_files = [f for f in os.listdir(save_dir) if f.endswith('.png')]
        print("PNG files found: ", png_files)
        if png_files:
            thumbnail_path = os.path.join(save_dir, png_files[0])
        else:
            raise HTTPException(status_code=404, detail="No PNG files found in directory")
    else:
        raise HTTPException(status_code=404, detail="Directory not found")
    if not os.path.exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        thumbnail_path,
        media_type="image/png",
        filename=png_files[0]
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
