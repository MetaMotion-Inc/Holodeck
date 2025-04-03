import requests
import json
import sys

def generate_scene(description):
    """
    Call the API to generate a scene using only a scene description
    """
    url = "http://localhost:8000/generate"
    payload = {"scene_description": description}
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Error connecting to API: {str(e)}"}

if __name__ == "__main__":
    # Get description from command line or use default
    description = sys.argv[1] if len(sys.argv) > 1 else "a cozy living room with a fireplace"
    
    print(f"Generating scene from description: '{description}'")
    result = generate_scene(description)
    
    # Pretty print the result
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        print(f"\nCheck {result.get('save_dir')} for your generated scene!")
