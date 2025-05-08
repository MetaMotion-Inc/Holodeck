import json
import openai
import os

def process_textures(data):
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    texture_names = os.path.join(script_dir, 'assets/texture_classes.txt')

    with open(texture_names, 'r') as txt_file:
        texture_classe = [line.strip() for line in txt_file]
    
    rooms = {}
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
              "content": f"I have a texture name as {wall_text_name}. I have the following classes of textures {','.join(texture_classe)}, please select the most likely to be what it should be. Only output a single word."
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
              "content": f"I have a texture name as {floor_text_name}. I have the following classes of textures {','.join(texture_classe)}, please select the most likely to be what it should be. Only output a single word."
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
