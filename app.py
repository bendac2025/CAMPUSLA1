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

# --- CSS TO REMOVE ALL STREAMLIT BRANDING ---
hide_streamlit_style = """
            <style>
            header[data-testid="stHeader"] { display: none !important; }
            [data-testid="stToolbar"] { display: none !important; }
            footer { display: none !important; }
            
            .block-container {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            
            div[data-testid="stAppViewContainer"] > .main {
                padding: 0 !important;
            }
            
            ::-webkit-scrollbar {
                width: 0px;
                background: transparent;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def find_popup_image(image_name):
    if not isinstance(image_name, str):
        return None
    clean_name = image_name.strip()
    extensions = ['.jpg', '.jpeg', '.png']
    for ext in extensions:
        file_path = f"{clean_name}{ext}"
        if os.path.exists(file_path):
            return file_path
    return None

def generate_interactive_map(image_path, csv_path):
    # 1. Load Data
    try:
        df = pd.read_csv(csv_path)
        # Clean columns: lowercase and remove spaces
        df.columns = df.columns.str.strip().str.lower()
    except FileNotFoundError:
        return "<h3 style='color:white; text-align:center'>Error: spaces.csv not found.</h3>"
    except Exception as e:
        return f"<h3 style='color:white; text-align:center'>Error reading CSV: {e}</h3>"

    # --- CHECK COLUMNS ---
    # Updated to look for 'type' and 'size'
    required_cols = ['coordinates', 'link url', 'space', 'actual site', 'type', 'size']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    # We make this a soft check (warning) rather than a hard crash
    if missing_cols:
        return f"""
        <div style='background: darkred; color: white; padding: 20px;'>
            <h3>CSV Column Error</h3>
            <p>The code is looking for these new columns: <b>type, size</b></p>
            <p>Your CSV is missing: <b>{missing_cols}</b></p>
            <p>Please rename 'Capacity' to 'Type' and 'Indoor/Outdoor' to 'Size' in your CSV file.</p>
        </div>
        """

    # 2. Encode Background Image
    if os.path.exists(image_path):
        bg_base64 = get_base64_of_bin_file(image_path)
        img_src = f"data:image/jpeg;base64,{bg_base64}"
    else:
        return "<h3 style='color:white; text-align:center'>Error: Background image1.jpg not found.</h3>"

    # 3. Generate SVG Polygons
    svg_width = 1920 
    svg_height = 1305

    polygons_html = ""
    
    for index, row in df.iterrows():
        coords = str(row.get('coordinates', ''))
        raw_link = str(row.get('link url', '#'))
        
        if raw_link and not raw_link.startswith(('http://', 'https://')):
            link = 'https://' + raw_link
        else:
            link = raw_link

        # --- NEW LOGIC HERE ---
        title = str(row.get('space', ''))
        
        # Get Type and Size
        space_type = row.get('type', 'N/A')
        size_val = row.get('size', 'N/A')
        
        # Build the description string with "sqft" automatically added
        desc = f"Type: {space_type} | Size: {size_val} sqft"
        
        # Image for Tooltip
        actual_site_name = row.get('actual site', '')
        popup_img_path = find_popup_image(actual_site_name)
        
        if popup_img_path:
            img_b64 = get_base64_of_bin_file(popup_img_path)
            popup_img_src = f"data:image/jpeg;base64,{img_b64}"
        else:
            popup_img_src = "https://via.placeholder.com/300x200?text=No+Image"

        title = title.replace("'", "&#39;")
        desc = desc.replace("'", "&#39;")
        
        polygons_html += f"""
        <a href="{link}" target="_blank">
            <polygon class="map-poly" points="{coords}" 
                onmousemove="showTooltip(evt, '{title}', '{desc}', '{popup_img_src}')" 
                onmouseout="hideTooltip()">
            </polygon>
        </a>
        """

    # 4. Construct Final HTML
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; background-color: #000; overflow-x: hidden; }}
        .map-container {{ position: relative; width: 100%; max-width: 100%; height: auto; overflow: hidden; }}
        .map-image {{ width: 100%; height: auto; display: block; }}
        .map-svg {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        .map-poly {{ fill: transparent; stroke: none; cursor: pointer; transition: all 0.2s ease; }}
        .map-poly:hover {{ fill: rgba(255, 215, 0, 0.3); stroke: rgba(255, 255, 255, 0.6); stroke-width: 2px; }}
        
        #tooltip {{
            display: none;
            position: fixed; 
            background: rgba(15, 15, 15, 0.95);
            color: white;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 12px;
            font-family: sans-serif;
            pointer-events: none;
            z-index: 10000;
            width: 240px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.8);
        }}
        #tooltip img {{ width: 100%; height: 140px; object-fit: cover; border-radius: 4px; margin-bottom: 8px; background: #333; }}
        #tooltip h4 {{ margin: 0 0 4px 0; color: #ffbf00; font-size: 16px; font-weight: 600; }}
        #tooltip p {{ margin: 0; font-size: 13px; color: #ddd; }}
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
            ttName.innerHTML = name;
            ttDesc.innerHTML = desc;
            ttImg.src = imgUrl;
            
            var x = evt.clientX;
            var y = evt.clientY;
            
            var tooltipW = 260;
            var tooltipH = 250;
            
            if (x + tooltipW > window.innerWidth) {{ x = x - tooltipW; }}
            if (y + tooltipH > window.innerHeight) {{ y = y - tooltipH; }}

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

# Generate the HTML
html_content = generate_interactive_map(img_file, csv_file)

# Display with scrolling enabled
st.components.v1.html(html_content, height=1200, scrolling=True)
