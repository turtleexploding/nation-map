import requests
import disnake
from disnake.ext import commands
from PIL import Image, ImageDraw
import time
import asyncio
import os
import math
import shutil
import aiohttp
import numpy as np
import json

TOKEN = ''

intents = disnake.Intents.default()
bot = commands.InteractionBot(intents=intents)
intents.message_content = True

class Command(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        
    @commands.slash_command(description="Creates a map of towns in nations")
    async def map_blank(
        self,
        inter: disnake.interactions.ApplicationCommandInteraction,
        nations: str = commands.Param(
            description="Comma-separated list of nation names"
        ),
        scale: int = commands.Param(
            description="",
            default=4
        ),
        colour: str = commands.Param(
            description="",
            default="Black")):

        await inter.response.defer()
        await asyncio.sleep(6)
        
        commandString = f"/map nations: {nations} scale: {scale} colour: {colour}"
        print(f'Received command with arguments: {nations}, {scale}, {colour}')

        if scale > 8:
            await inter.send("Scale cannot be greater than 8")
            return

        def fetch_town_info(town_names):
            base_url = 'https://api.earthmc.net/v3/aurora/towns?query='
            results = []
    
            batch_size = 10
            town_name_batches = [town_names[i:i + batch_size] for i in range(0, len(town_names), batch_size)]
    
            for batch in town_name_batches:
                query = ','.join(batch)
                url = base_url + query
                response = requests.get(url)
        
                if response.status_code == 200:
                    data = response.json()
                    results.extend(data)
                else:
                    print(f"Failed to fetch data for batch: {batch}")
      
            return results

        def extract_coordinates(town_info):
            coordinates = []
            for town in town_info:
                if 'coordinates' in town and 'townBlocks' in town['coordinates']:
                    town_blocks = town['coordinates']['townBlocks']
                    coordinates.extend(town_blocks)
            return coordinates

        url = 'https://api.earthmc.net/v3/aurora'
        
        nation_list = [nation.strip() for nation in nations.split(',')]
        all_coordinates = []

        for nation in nation_list:
            response = requests.get(f'{url}/nations?query={nation}')

            if response.status_code == 200:
                nationLookup = response.json()

                if len(nationLookup) > 0 and 'towns' in nationLookup[0]:
                    nationTowns = nationLookup[0]['towns']
                    formattedNationTowns = [town['name'] for town in nationTowns]

                    town_names = formattedNationTowns
                    town_info = fetch_town_info(town_names)
                    coordinates = extract_coordinates(town_info)
                    all_coordinates.extend(coordinates)

        if not all_coordinates:
            await inter.send("No towns found for the provided nations")
            return

        min_x = min(coord[0] for coord in all_coordinates)
        min_y = min(coord[1] for coord in all_coordinates)
        max_x = max(coord[0] for coord in all_coordinates)
        max_y = max(coord[1] for coord in all_coordinates)

        pixel_size = scale
        scale_factor = scale
        width = (max_x - min_x + 1) * scale_factor
        height = (max_y - min_y + 1) * scale_factor

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        for coord in all_coordinates:
            adjusted_coord = ((coord[0] - min_x) * pixel_size, (coord[1] - min_y) * pixel_size)
            draw.rectangle([adjusted_coord, (adjusted_coord[0] + pixel_size - 1, adjusted_coord[1] + pixel_size - 1)], fill=colour)

        times = int(time.time())

        image_path = f'map-{scale}-{colour}-{times}.png'
        image.save(image_path)

        await inter.edit_original_message(file=disnake.File(image_path))

    @commands.slash_command(description="Chart of available colours")
    async def colours(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        image_path = "https://media.discordapp.net/attachments/1104115964301283431/1248532768720289802/colours.png?ex=6664ab00&is=66635980&hm=4c3b94aaada3d0c046b1264b45c601759f4603e0be025f61a7cc055a7db55a1c&"
        await inter.send(image_path)

    @commands.slash_command(description="makes a map of multiple nations with multiple colours")
    async def map_multicolours(
        inter: disnake.ApplicationCommandInteraction,
        nations: str = commands.Param(description=""),
        colours: str = commands.Param(description=""),
        scale: int = commands.Param(description="", default=4)
    ):
        await inter.response.defer()

        if scale > 8:
            await inter.send("Scale cannot be more than 8")
            return

        async def fetch_town_info(town_names):
            base_url = 'https://api.earthmc.net/v3/aurora/towns?query='
            results = []

            batch_size = 10
            town_name_batches = [town_names[i:i + batch_size] for i in range(0, len(town_names), batch_size)]

            for batch in town_name_batches:
                query = ','.join(batch)
                url = base_url + query
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    results.extend(data)
                else:
                    print(f"Failed to fetch data for batch: {batch}")

            return results

        def extract_coordinates(town_info):
            coordinates = []
            for t in town_info:
                if 'coordinates' in t and 'townBlocks' in t['coordinates']:
                    town_blocks = t['coordinates']['townBlocks']
                    coordinates.extend(town_blocks)
            return coordinates

        async def create_map(nations, colours, scale):
            url = 'https://api.earthmc.net/v3/aurora'
            nation_list = [nation.strip() for nation in nations.split(',')]
            colour_list = [colour.strip() for colour in colours.split(',')]
            all_coordinates = []
            nation_colours = dict(zip(nation_list, colour_list))

            for nation in nation_list:
                response = requests.get(f'{url}/nations?query={nation}')

                if response.status_code == 200:
                    nation_lookup = response.json()

                    if len(nation_lookup) > 0 and 'towns' in nation_lookup[0]:
                        nation_towns = nation_lookup[0]['towns']
                        formatted_nation_towns = [t['name'] for t in nation_towns]

                        town_names = formatted_nation_towns
                        town_info = await fetch_town_info(town_names)
                        coordinates = extract_coordinates(town_info)
                        all_coordinates.append((coordinates, nation_colours[nation]))
                else:
                    print(f"Failed to fetch data for n: {nation}")

            if not all_coordinates:
                print("No towns found for the given n(s)")
                return

            min_x = min(coord[0] for coords, _ in all_coordinates for coord in coords)
            min_y = min(coord[1] for coords, _ in all_coordinates for coord in coords)
            max_x = max(coord[0] for coords, _ in all_coordinates for coord in coords)
            max_y = max(coord[1] for coords, _ in all_coordinates for coord in coords)

            pixel_size = scale
            scale_factor = scale
            width = (max_x - min_x + 1) * scale_factor
            height = (max_y - min_y + 1) * scale_factor

            image = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(image)

            for coords, colour in all_coordinates:
                for coord in coords:
                    adjusted_coord = ((coord[0] - min_x) * pixel_size, (coord[1] - min_y) * pixel_size)
                    draw.rectangle([adjusted_coord, (adjusted_coord[0] + pixel_size - 1, adjusted_coord[1] + pixel_size - 1)], fill=colour)

            times = int(time.time())
            image_path = f'map-{scale}-{times}.png'
            
            await inter.followup.send(file=disnake.File(image_path))

        await create_map(nations, colours, scale)
    
    @commands.slash_command(description='makes a map of a n with squaremap as a background')
    async def map(
        self,
        inter: disnake.ApplicationCommandInteraction,
        nation: str = commands.Param(description = ''),
        colour: str = commands.Param(description = ''),
        zoom: str = commands.Param( description = '')
    ):
        n = nation
        c = colour
        if int(zoom) > 3:
            await inter.send('zoom must be ≤ 3')

        await inter.response.defer()
        await inter.send("<a:UpsidedownTurtle:1266426955503239201>")

        def town_names(base, n, nationName):
            names = []

            response = requests.get(f'{base}{n}{nationName}')

            if response.status_code == 200:
                nationLookup = response.json()

                if len(nationLookup) > 0 and 'towns' in nationLookup[0]:
                    nationTowns = nationLookup[0]['towns']
                    formattedNationTowns = [t['name'] for t in nationTowns]
                    names.extend(formattedNationTowns)

            return names

        def town_info(townNames, base, t):
            info = []

            batchSize = 30
            nameBatches = [townNames[i:i+batchSize] for i in range(0, len(townNames), batchSize)]

            for batch in nameBatches:
                query = ','.join(batch)
                url = base+t+query
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    info.extend(data)

            return info

        def get_coords(townInfo):
            coordinates = []
            for town in townInfo:
                if 'coordinates' in town and 'townBlocks' in town['coordinates']:
                    townBlocks = town['coordinates']['townBlocks']
                    coordinates.extend(townBlocks)
            return coordinates

        def all_coords(base, n, t):
            nation_list = [na.strip() for na in nation.split(',')]
            allcoords = []

            for na in nation_list:
                response = requests.get(f'{base}{n}{na}')

                if response.status_code == 200:
                    nationLookup = response.json()

                    if len(nationLookup) > 0 and 'towns' in nationLookup[0]:
                        nationTowns = nationLookup[0]['towns']
                        formattedNationTowns = [town['name'] for town in nationTowns]

                        townNames = formattedNationTowns
                        townInfo = town_info(townNames, base, t)
                        coordinates = get_coords(townInfo)
                        allcoords.extend(coordinates)

            if not allcoords:
                print("No towns found for the provided nations")
            return allcoords
        
        async def download_tile(session, url, path):
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, 'wb') as file:
                        file.write(await response.read())
            except Exception as e:
                print(f"Error downloading {url}: {e}")

        async def download_tiles(tiles, link, world, now):
            async with aiohttp.ClientSession() as session:
                tasks = []
                for x, z in tiles:
                    url = f'{link}/tiles/{world}/{zoom}/{x}_{z}.png'
                    path = f'{zoom}-{now}/{x}_{z}.png'
                    tasks.append(download_tile(session, url, path))
                await asyncio.gather(*tasks)

        async def create_background(minX, minZ, maxX, maxZ, link, world, now, tminX, tminZ,  tmaxX, tmaxZ, bpp, tiles, scale):

            ts = int(512)

            nx = math.floor(tminX*ts)
            nz = math.floor(tminZ*ts)
            
            os.makedirs(f'{scale}-{now}', exist_ok=True)
                        
            await download_tiles(tiles, link, world, now)
            
            total_width = int((maxX-minX)*16*ts/bpp)
            total_height = int((maxZ-minZ)*16*ts/bpp)
            print(f'minx:{nx} minz:{nz} maxx:{nx+total_width} maxz:{nz+total_height}')
            print(f"Total width: {total_width+ts}, Total height: {total_height+ts}")
            
            output = Image.new(mode="RGBA", size=(total_width+ts, total_height+ts))
            
            for x in range(tminX, tmaxX + 1):
                for z in range(tminZ, tmaxZ + 1):
                    tile_path = f'{zoom}-{now}/{x}_{z}.png'
                    try:
                        tile = Image.open(tile_path)
                        output.paste(tile, ((x-tminX)*ts, (z-tminZ)*ts))
                    except FileNotFoundError:
                        print(f"Warning: Tile {tile_path} not found.")
                        continue
            
            shutil.rmtree(f'{zoom}-{now}')
            
            cLeft = abs(abs(minX)*scale-abs(nx))
            cTop = abs(abs(minZ)*scale-abs(nz))
            cRight = abs(cLeft+abs(maxX-minX)*scale)
            cBottom = abs(cTop+abs(maxZ-minZ)*scale)
            print(f"Crop dimensions: left={cLeft}, top={cTop}, right={cRight}, bottom={cBottom}")
            print(f'dimensions: hor:{abs(cRight-cLeft)} ver:{abs(cBottom-cTop)}')
            print(f'expected dimensions: hor:{abs(maxX-minX)*scale} ver:{abs(maxZ-minZ)*scale}')

            cropped = output.crop((cLeft, cTop, cRight, cBottom))
            
            return cropped

        async def draw_towns(image, coords, minX, minZ, now, nationName, c, scale):
            draw = ImageDraw.Draw(image)

            for coord in coords:
                adjusted = ((coord[0]-minX)*scale, (coord[1]-minZ)*scale)
                draw.rectangle([adjusted, (adjusted[0]+scale-1, adjusted[1]+scale-1)], fill=c)

            path2 = f'{nationName}-{c}-{now}.png'
            image.save(path2)
            
            await inter.edit_original_message(file=disnake.File(path2))

        async def main():
            base = 'https://api.earthmc.net/v3/aurora/'
            t = 'towns?query='
            n = 'nations?query='

            link = 'https://map.earthmc.net/'
            world = 'minecraft_overworld'

            nationName = nation
            c = colour  
            now = int(time.time())
            e = (int(zoom)+int(1))
            print(f'e:{e}')
            scale = 2**e
            print(f'scale:{scale}')

            coords = all_coords(base, n, t)

            if not coords:
                print("No towns found for the provided nations.")
                return

            bpp = 2**(12-int(zoom))
            print(f'bpp:{bpp}')

            minX = min(coord[0] for coord in coords)
            minZ = min(coord[1] for coord in coords)
            maxX = max(coord[0] for coord in coords)
            maxZ = max(coord[1] for coord in coords)
            print(f'minx:{minX} minz:{minZ} maxX:{maxX} maxZ:{maxZ}')


            tminX = math.floor(minX*16/bpp)
            tminZ = math.floor(minZ*16/bpp)
            tmaxX = math.floor(maxX*16/bpp)
            tmaxZ = math.floor(maxZ*16/bpp)
            print(f'tileminx:{tminX} tileminz:{tminZ} tilemaxx:{tmaxX} tilemaxz:{tmaxZ}')
            
            tiles = [(x, z) for x in range(tminX, tmaxX+1) for z in range(tminZ, tmaxZ+1)]

            image = await create_background(minX, minZ, maxX, maxZ, link, world, now, tminX, tminZ,  tmaxX, tmaxZ, bpp, tiles, scale)
            await draw_towns(image, coords, minX, minZ, now, nationName, c, scale)
            await download_tiles(tiles, link, world, now)

        await main()

@bot.event
async def on_ready():
    print('Ready')

bot.add_cog(Command(bot))
bot.run(TOKEN)