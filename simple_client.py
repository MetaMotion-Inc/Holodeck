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
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if "error" in data:
            return {"success": False, "message": data["error"]}
        return {"success": True, "scene_data": data}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Error connecting to API: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"success": False, "message": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    description = sys.argv[1] if len(sys.argv) > 1 else "a cozy living room with a fireplace"
    
    print(f"Generating scene from description: '{description}'")
    result = generate_scene(description)
    
    if result.get("success"):
        print("\nGenerated Scene Data:")
        print(json.dumps(result.get("scene_data"), indent=2))
    else:
        print(f"\nError: {result.get('message')}")
