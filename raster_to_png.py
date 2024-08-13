import rasterio, os
from PIL import Image, ImageOps, ImageEnhance
import os
import glob
import numpy as np
import json

def colour_ramp(colour):
    if colour == "green":
        ramp =[
            (247, 252, 245),
            (116, 196, 118),
            (0, 68, 27)
            ]
    elif colour == "thermal":
        ramp = [
            (6, 123, 194),
            (251, 226, 164),
            (213, 96, 98)
            ]
    elif colour == "blue":
        ramp = [
            (247, 251, 255),
            (107, 174, 214),
            (8, 48, 107)
            ]
    elif colour == "orange":
        ramp = [
            (255, 245, 235),
            (253, 141, 60),
            (127, 39, 4)
            ]
    return ramp

def convert_image(raster_file, image_file, colour_pallette_name, nodata=None):
    colour_pallette = colour_ramp(colour_pallette_name)
    file_name = os.path.basename(raster_file)[0:-4]
    bbox_dict = {file_name: {}}
    
    with rasterio.open(raster_file) as src:
        bounds = src.bounds
        bbox_dict[file_name]["extent"] = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]

        nodata = src.nodata
        data = src.read(1).astype('float32')  # Convert to float to handle NaNs
        
        # Handle nodata values
        data[data == nodata] = np.nan
        data[data == 0] = np.nan

        # Normalize data to 0-255 range for better image quality
        valid_data = data[~np.isnan(data)]
        data_min, data_max = valid_data.min(), valid_data.max()
        segment_range = (data_max - data_min)/4
        bbox_dict[file_name]["minValue"] = round(float(data_min), 2)
        bbox_dict[file_name]["maxValue"] = round(float(data_max), 2)
        bbox_dict[file_name]["colorStops"] = [
            {"value": round(float(data_min), 2), "color": "#fff5eb"},
            {"value": float(round(data_min + segment_range, 2)), "color": "#ffb776"},
            {"value": float(round(data_min + 2*segment_range, 2)), "color": "#fd8d3c"},
            {"value": float(round(data_min + 3*segment_range, 2)), "color": "#c85620"},
            {"value": float(round(data_min + 4*segment_range, 2)), "color": "#7f2704"}
        ]
        bbox_dict[file_name]["units"] = "kg/m^3"
        
        if data_max != data_min:
            normalized_data = ((data - data_min) / (data_max - data_min) * 255)
        else:
            normalized_data = np.zeros_like(data)
        
        normalized_data[np.isnan(normalized_data)] = 0  # Set NaNs to 0
        normalized_data = normalized_data.astype('uint8')

        # Create an image from the normalized data
        img = Image.fromarray(normalized_data, mode='L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)  # Increase the contrast

        # Apply color palette
        palette = ImageOps.colorize(img, black=colour_pallette[0], white=colour_pallette[2], mid=colour_pallette[1])
        palette = palette.convert('RGB')
        palette.save('output.png', 'PNG')
    
    img = Image.open('output.png')
    img = img.convert('RGBA')
    background = colour_pallette[0]  # white color
    data = img.getdata()
    new_data = []

    for item in data:
        if item[:3] == background:
            new_data.append((colour_pallette[0][0], colour_pallette[0][1], colour_pallette[0][2], 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    img.save(image_file, 'PNG')
    os.remove("output.png")

    return bbox_dict


cities = ["Alesund", "Bruges", "Burgas", "Cascais", "Constanta", "Izmir", "Pisek", "Rijeka", "Rimini"]

def find_tif_files(root_dir):
    tif_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".tif"):
                tif_files.append(os.path.join(root, file))
    return tif_files

tif_files = find_tif_files("C:/Users/Acer/PycharmProjects/smart_cities")
bbox_dicts = {}

folder_name = tif_files[0].split("\\")[-2]
previous_dir = os.path.dirname(tif_files[0])

for tif_file in tif_files:
    file_name = os.path.basename(tif_file).rstrip(".tif")

    directory_path = os.path.dirname(tif_file)

    city = tif_file.split("\\")[1]

    folder_name_new = tif_file.split("\\")[-2]

    if folder_name != folder_name_new:
        with open(os.path.join(previous_dir, "metadata.json"), 'w') as json_file:
            json.dump(bbox_dicts, json_file, indent=4)

        folder_name = folder_name_new

        bbox_dicts = {}

    bbox_dict = convert_image(tif_file, os.path.join(directory_path, file_name + ".png"), "orange", 255)
    bbox_dicts.update(bbox_dict)

    previous_dir = directory_path

        


    
