import json
import openai
import os

def determine_outdoor_texture(query, texture_classes):
    """Determine appropriate outdoor texture based on scene query."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"""Given a scene description, select the most appropriate ground texture from: {', '.join(texture_classes)}.
                Consider:
                - Urban areas (streets, sidewalks) -> Concrete, Asphalt
                - Parks and gardens -> Grass, Ground
                - Beaches -> Sand
                - Forest/woodland -> Ground, Dirt
                - Patios/courtyards -> Tiles, Stone
                Only output a single word matching one of the available textures."""
            },
            {
                "role": "user",
                "content": f"What would be the most appropriate ground texture for this scene: {query}"
            }
        ],
        temperature=0.3,
        max_tokens=64,
        top_p=1
    )
    return response.choices[0].message.content.strip()

def process_textures(data):
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    texture_names = os.path.join(script_dir, 'assets/texture_classes.txt')

    with open(texture_names, 'r') as txt_file:
        texture_classes = [line.strip() for line in txt_file]
    
    rooms = {}

    # Determine outdoor floor type if it's an outdoor scene
    if data.get('is_outdoor'):
        scene_query = data.get('query', 'An outdoor scene')
        outdoor_texture = determine_outdoor_texture(scene_query, texture_classes)
        
        # Apply the determined textures to all floors and store sky texture in proceduralParameters
        for ifloor, floor in enumerate(data['rooms']):
            data['rooms'][ifloor]['floorMaterial'] = {
                'name': outdoor_texture,
                'ambientcg': outdoor_texture
            }

    # Process walls as before
    print("@"*50)
    print("Processing walls...")
    print("@"*50)
    for iwall, wall in enumerate(data['walls']):
        wall_text_name = wall['material']['name']
        if wall['roomId'] in rooms: 
            data['walls'][iwall]['material']['ambientcg'] = rooms[wall['roomId']]
            continue

        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
            {
              "role": "system", 
              "content": f"I have a texture name as {wall_text_name}. I have the following classes of textures {','.join(texture_classes)}, please select the most likely to be what it should be. Only output a single word."
            },
            {
              "role": "user",
              "content": "Please give me a single texture."
            }
          ],
          temperature=0.7,
          max_tokens=64,
          top_p=1
        )
        texture_response = response.choices[0].message.content
        data['walls'][iwall]['material']['ambientcg'] = texture_response
        rooms[wall['roomId']] = texture_response

    for ifloor, floor in enumerate(data['rooms']):
        floor_text_name = floor['floorMaterial']['name']

        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
            {
              "role": "system",
              "content": f"I have a texture name as {floor_text_name}. I have the following classes of textures {','.join(texture_classes)}, please select the most likely to be what it should be. Only output a single word."
            },
            {
              "role": "user",
              "content": "Please give me a single texture."
            }
          ],
          temperature=0.7,
          max_tokens=64,
          top_p=1
        )
        texture_response = response.choices[0].message.content
        data['rooms'][ifloor]['floorMaterial']['ambientcg'] = texture_response

    print("@"*50)
    print("Processing ceilings...")
    print("@"*50)
    return data

if __name__ == "__main__":
    # Script can still be run standalone if needed
    file_path = 'data/world.json'
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    
    processed_data = process_textures(data)
    
    with open(file_path.replace('.json','_added.json'), 'w') as json_file:
        json.dump(processed_data, json_file)
