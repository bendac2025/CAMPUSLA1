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
        # --- FIX: CLEAN COLUMN NAMES ---
        # This converts all headers to lowercase and removes empty spaces
        # e.g., " Coordinates " becomes "coordinates"
        df.columns = df.columns.str.strip().str.lower()
    except FileNotFoundError:
        return "<h3 style='color:white; text-align:center'>Error: spaces.csv not found.</h3>"
    except Exception as e:
        return f"<h3 style='color:white; text-align:center'>Error reading CSV: {e}</h3>"

    # --- DIAGNOSTIC CHECK ---
    required_cols = ['coordinates', 'link_url', 'name', 'description', 'image_url']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        # If columns are missing, show a helpful error on screen
        error_msg = f"""
        <div style='background: darkred; color: white; padding: 20px;'>
            <h3>CSV Error</h3>
            <p>Your CSV file is missing these required columns: <b>{missing_cols}</b></p>
            <p>Your current columns are: <b>{list(df.columns)}</b></p>
            <p>Please check the first row of your spaces.csv file.</p>
        </div>
        """
        return error_msg

    # 2. Encode Background Image
    if os.path.exists(image_path):
        img_base64 = get_base64_of_bin_file(image_path)
        img_src = f"data:image/jpeg;base64,{img_base64}"
    else:
        return "<h3 style='color:white; text-align:center'>Error: Image file not found.</h3>"

    # 3. Generate SVG Polygons
    # Adjust these numbers if your coordinate tool used a different scale
    svg_width = 1600 
    svg_height = 1066

    polygons_html = ""
    
    for index, row in df.iterrows():
        # Using .get() ensures it doesn't crash if a cell is empty
        coords = str(row.get('coordinates', ''))
        link = str(row.get('link_url', '#'))
        name = str(row.get('name', ''))
        desc = str(row.get('description', ''))
        img_preview = str(row.get('image_url', ''))
        
        # Escape quotes in strings to prevent HTML breakage
        name = name.replace("'", "&#39;")
        desc = desc.replace("'", "&#39;")
        
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
        .map-container {{ position: relative; width: 100%; height: auto; }}
        .map-image {{ width: 100%; display: block; }}
        .map-svg {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        .map-poly {{ fill: transparent; stroke: none; cursor: pointer; transition: all 0.3s ease; }}
        .map-poly:hover {{ fill: rgba(255, 215, 0, 0.4); stroke: rgba(255, 255, 255, 0.8); stroke-width: 2px; }}
        
        #tooltip {{
            display: none;
            position: fixed;
            background: rgba(20, 20, 20, 0.95);
            color: white;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            font-family: sans-serif;
            pointer-events: none;
            z-index: 1000;
            width: 250px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        #tooltip img {{ width: 100%; height: 150px; object-fit: cover; border-radius: 4px; margin-bottom: 8px; }}
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
            
            var x = evt.clientX;
            var y = evt.clientY;
            
            if (x + 270 > window.innerWidth) {{ x = x - 270; }}
            if (y + 300 > window.innerHeight) {{ y = y - 200; }}

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
current_dir = os.getcwd()
img_file = os.path.join(current_dir, "image1.jpg")
csv_file = os.path.join(current_dir, "spaces.csv")

html_content = generate_interactive_map(img_file, csv_file)
st.components.v1.html(html_content, height=900, scrolling=False)
