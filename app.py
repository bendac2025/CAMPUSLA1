import streamlit as st
import pandas as pd
import base64
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Venue Interactive Map",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TO HIDE STREAMLIT UI ELEMENTS ---
# This ensures the focus remains solely on the image as requested
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 0rem;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_base64_of_bin_file(bin_file):
    """Encodes the local image to base64 so it can be embedded in HTML"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def generate_interactive_map(image_path, csv_path):
    # 1. Load Data
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return "<h3 style='color:white; text-align:center'>Error: spaces.csv not found.</h3>"

    # 2. Encode Background Image
    if os.path.exists(image_path):
        img_base64 = get_base64_of_bin_file(image_path)
        img_src = f"data:image/jpeg;base64,{img_base64}"
    else:
        return "<h3 style='color:white; text-align:center'>Error: Image file not found.</h3>"

    # 3. Generate SVG Polygons
    # We use an SVG overlay on top of the image. 
    # The viewBox should match the original image dimensions (or aspect ratio).
    # Assuming the image is roughly 1000x667 based on aspect ratio, but viewBox allows scaling.
    # Note: When mapping coordinates, ensure they match the coordinate system used here.
    # Standard practice: Use the original image width/height for the viewBox.
    
    # Let's assume a standard coordinate base (e.g., 1024 width) for the viewBox.
    # You must map your coordinates relative to the image's original size.
    svg_width = 1600  # Adjust this to match the width of image1.jpg
    svg_height = 1066 # Adjust this to match the height of image1.jpg

    polygons_html = ""
    
    for index, row in df.iterrows():
        coords = row['coordinates']
        link = row['link_url']
        name = row['name']
        desc = row['description']
        img_preview = row['image_url']
        
        # We create a group for each zone containing the link and polygon
        polygons_html += f"""
        <a href="{link}" target="_blank">
            <polygon class="map-poly" points="{coords}" 
                onmousemove="showTooltip(evt, '{name}', '{desc}', '{img_preview}')" 
                onmouseout="hideTooltip()">
            </polygon>
        </a>
        """

    # 4. Construct Final HTML/CSS/JS
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; background-color: #000; }}
        
        /* Container for the image and SVG overlay */
        .map-container {{
            position: relative;
            width: 100%;
            height: auto;
        }}
        
        /* The Background Image */
        .map-image {{
            width: 100%;
            display: block;
        }}
        
        /* The SVG Overlay */
        .map-svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        
        /* Polygon Styling */
        .map-poly {{
            fill: transparent;
            stroke: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        /* Hover Effect: Yellow Highlight */
        .map-poly:hover {{
            fill: rgba(255, 215, 0, 0.4); /* Gold with transparency */
            stroke: rgba(255, 255, 255, 0.8);
            stroke-width: 2px;
        }}

        /* Tooltip Styling */
        #tooltip {{
            display: none;
            position: fixed;
            background: rgba(20, 20, 20, 0.95);
            color: white;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            font-family: sans-serif;
            pointer-events: none; /* Let mouse pass through to polygon */
            z-index: 1000;
            width: 250px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        
        #tooltip img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 4px;
            margin-bottom: 8px;
        }}
        
        #tooltip h4 {{ margin: 0 0 5px 0; color: #ffbf00; }}
        #tooltip p {{ margin: 0; font-size: 0.9em; color: #ddd; }}

    </style>
    </head>
    <body>

    <div class="map-container">
        <img src="{img_src}" class="map-image">
        <svg viewBox="0 0 {svg_width} {svg_height}" class="map-svg" preserveAspectRatio="none">
            {polygons_html}
        </svg>
    </div>

    <div id="tooltip">
        <img id="tt-img" src="" alt="Space Preview">
        <h4 id="tt-name"></h4>
        <p id="tt-desc"></p>
    </div>

    <script>
        var tooltip = document.getElementById("tooltip");
        var ttName = document.getElementById("tt-name");
        var ttDesc = document.getElementById("tt-desc");
        var ttImg = document.getElementById("tt-img");

        function showTooltip(evt, name, desc, imgUrl) {{
            tooltip.style.display = "block";
            ttName.innerText = name;
            ttDesc.innerText = desc;
            ttImg.src = imgUrl;
            
            // Calculate Position
            // We use clientX/Y to position relative to viewport
            var x = evt.clientX;
            var y = evt.clientY;
            
            // Adjust if tooltip goes off screen
            if (x + 270 > window.innerWidth) {{
                x = x - 270;
            }}
            
            if (y + 300 > window.innerHeight) {{
                y = y - 200;
            }}

            tooltip.style.left = (x + 15) + "px";
            tooltip.style.top = (y + 15) + "px";
        }}

        function hideTooltip() {{
            tooltip.style.display = "none";
        }}
    </script>
    </body>
    </html>
    """
    return html_code

# --- APP EXECUTION ---
# 1. Set file paths
current_dir = os.getcwd()
img_file = os.path.join(current_dir, "image1.jpg")
csv_file = os.path.join(current_dir, "spaces.csv")

# 2. Generate HTML
html_content = generate_interactive_map(img_file, csv_file)

# 3. Render in Streamlit
# We use height=1000 to ensure enough scroll space, or use scrolling=True
st.components.v1.html(html_content, height=900, scrolling=False)