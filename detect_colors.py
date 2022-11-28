import os, argparse
import pandas as pd
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--image', type=str, help='path to image')
parser.add_argument('--colors', type=str, help='colors csvfile')
args = parser.parse_args()

def resize_image(width, height, threshold):
	"""
	Function takes in an image's original dimensions and returns the 
	new width and height while maintaining its aspect ratio where 
	both are below the threshold. Purpose is to reduce runtime and 
	not distort the original image too much. 

	Parameters
	----------
	width : int
		original width of image
	height : int 
		original height of image
	threshold : int
		max dimension size for both width and height
	"""
	if (width > threshold) or (height > threshold):
		max_dim = max(width, height)
		if height == max_dim:
			new_width = int((width * threshold) / height)
			new_height = threshold
		if width == max_dim:
			new_height = int((height * threshold) / width)
			new_width = threshold
		return new_height, new_width
	else: return height, width

def detect_colors(image_path):
    """
    Function returns colors detected in image
    
    Parameters
    ----------
    image_path : str
        path to imagefile for detection
        
    Return
    ------
    sorted list of tuples (color, total number detections) 
    """
    
    # Read image
    image = Image.open(image_path)
    
    # Convert image into RGB
    image = image.convert('RGB')

    # Get width and height of image
    width, height = image.size
    print(f'Original dimensions: {width} x {height}')
    
    # Resize image to improve runtime
    width, height = resize_image(width, height, threshold=100)
    print(f'New dimensions: {width} x {height}')
    image = image.resize((width, height))
 
    # Iterate through each pixel
    detected_colors = {} # hash-map
    for x in range(0, width):
        for y in range(0, height):
            # r,g,b value of pixel
            r, g, b = image.getpixel((x, y))
            rgb = f'{r}:{g}:{b}'
            if rgb in detected_colors:
                detected_colors[rgb] += 1
            else: 
                detected_colors[rgb] = 1
 
    # Sort colors from most common to least common
    detected_colors = sorted(detected_colors.items(), key=lambda x:x[1], reverse=True)

    return detected_colors

def get_color_codes(detected_colors):
	"""
	Function finds the best matches between detected color codes and source color 
	codes from: https://www.colorhexa.com 

	Parameters
	---------
	detected_colors : list
		list of detected colors in image
	color_codes : list
		list of best matches
	"""

	color_codes = []
	for idx,detected_color in enumerate(detected_colors):
		detected_color = detected_color[0].split(':')
		print(f'Processing {detected_color}...{idx+1}/{len(detected_colors)}')
		
		# Calculate absolute differences
		color_map = []
		for idx,row in colors.iterrows():
			r = abs(int(detected_color[0]) - row['R'])
			g = abs(int(detected_color[1]) - row['G'])
			b = abs(int(detected_color[2]) - row['B'])

			# Query row values
			color = row['color']
			code = row['code'].replace('#', '')
		
			# Map results
			color_map.append({'color':color, 'code':code, 'distance':sum([r,g,b])})

		# Get best match (shortest distance)
		best_match = min(color_map, key=lambda x:x['distance'])

		# Get color code
		color_code = best_match['code']
		if color_code not in color_codes: color_codes.append(color_code)

	return color_codes

def get_association(color_codes):
	"""
	Function returns color name associated with detected color codes

	Parameters
	----------
	color_codes : list
		list of detected color codes in image

	Return
	------
	res : list
		list of color names associated with respective color codes
	"""
	
	res = []
	for color_code in color_codes:
		colorfile = os.path.join('colors', color_code + '.png')
		# Query color name associated with color code
		color_name = colors[colors['code'] == f'#{color_code}']['color'].values[0]
		# Append results...
		res.append({'color name':color_name, 'color code':f'#{color_code}'})
	
	# Generate pandas dataframe
	if len(res) == 0: return []
	elif len(res) == 1: res = pd.DataFrame(res, index=[0])
	else: res = pd.DataFrame(res, index=None)

	return res

if __name__=='__main__':
	
	image = args.image
	colors = args.colors

	# Read in colors csvfile
	colors = pd.read_csv('colors.csv')	

	# Detect all colors in image
	print(f'Detecting colors for {image}...')
	detected_colors = detect_colors(image)

	# I've noticed that not every consecutive pixel is a different color (only slight variations)
	# So I recommend splicing up detected_colors to improve run time
	color_codes = get_color_codes(detected_colors[0::10])
	print(f'Total unique colors found in image: {len(color_codes)}')

	# Return best matches (color name, color code) 
	# Reminder: The topmost color is the dominant color in image.
	res = get_association(color_codes)
	print(res)
