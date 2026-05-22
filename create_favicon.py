from PIL import Image, ImageDraw
import os

# Create a 32x32 image
img = Image.new('RGB', (32, 32), color='#2c3e50')
draw = ImageDraw.Draw(img)

# Draw a simple "I" for Inventory
draw.rectangle([10, 8, 22, 10], fill='#3498db')  # top bar
draw.rectangle([14, 10, 18, 22], fill='#3498db')  # middle bar
draw.rectangle([10, 22, 22, 24], fill='#3498db')  # bottom bar

# Save as ICO
img.save('static/favicon.ico')
print("Favicon created successfully!")