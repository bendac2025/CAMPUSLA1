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

# --- CSS TO HIDE STREAMLIT UI ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {
                padding: 0 !important;
                margin: 0 !important;
            }
            /* Remove standard Streamlit padding */
            div[data-testid="stAppViewContainer"] > .main {
                padding: 0;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_base64_of_bin_file(bin_file):
    """Encodes a binary file to base64 for embedding in HTML"""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def find_popup_image(image_name):
    """
    Looks for an image file based on the 'Actual Site' name.
    Checks for .jpg, .jpeg, and .png extensions.
    """
    if not isinstance(image_name, str):
        return None
        
    # Clean the filename (remove extra spaces)
    clean_name = image_name.strip()
    
    # List of extensions to check
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

    # --- DIAGNOSTIC CHECK ---
    # We check for the new columns from your file
    required_cols = ['coordinates', 'link url', 'space', 'actual site']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        return f"""
        <div style='background: darkred; color: white; padding: 20px;'>
            <h3>CSV Error</h3>
            <p>Missing columns: <b>{missing_cols}</b></p>
            <p>Found columns: <b>{list(df.columns)}</b></p>
        </div>
        """

    # 2. Encode Background Image
    if os.path.exists(image_path):
        bg_base64 = get_base64_of_bin_file(image_path)
        img_src = f"data:image/jpeg;base64,{bg_base64}"
    else:
        return "<h3 style='color:white; text-align:center'>Error: Background image1.jpg not found.</h3>"

    # 3. Generate SVG Polygons
    # Dimensions matched to your provided image1.jpg (1024x696)
    svg_width = 1024 
    svg_height = 696

    polygons_html = ""
    
    for index, row in df.iterrows():
        # Extract data using the new column names
        coords = str(row.get('coordinates', ''))
        raw_link = str(row.get('link url', '#'))
        
        # Format Link: Ensure it starts with http/https
        if raw_link and not raw_link.startswith(('http://', 'https://')):
            link = 'https://' + raw_link
        else:
            link = raw_link

        # Info for Tooltip
        title = str(row.get('space', ''))
        
        # Build description from available data
        capacity = row.get('capacity', '')
        site_type = row.get('indoor/outdoor', '')
        desc = f"Capacity: {capacity} | Type: {site_type}"
        
        # Image for Tooltip
        actual_site_name = row.get('actual site', '')
        popup_img_path = find_popup_image(actual_site_name)
        
        if popup_img_path:
            img_b64 = get_base64_of_bin_file(popup_img_path)
            popup_img_src = f"data:image/jpeg;base64,{img_b64}"
        else:
            # Fallback placeholder if image is missing
            popup_img_src = "https://via.placeholder.com/300x200?text=No+Image"

        # Escape quotes for HTML
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
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            pointer-events: none;
            z-index: 9999;
            width: 260px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.6);
        }}
        #tooltip img {{ width: 100%; height: 160px; object-fit: cover; border-radius: 4px; margin-bottom: 10px; border: 1px solid #333; }}
        #tooltip h4 {{ margin: 0 0 5px 0; color: #ffbf00; font-size: 18px; }}
        #tooltip p {{ margin: 0; font-size: 14px; color: #ccc; line-height: 1.4; }}
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
            
            // Mouse position relative to viewport
            var x = evt.clientX;
            var y = evt.clientY;
            
            // Prevent tooltip from going off-screen
            var tooltipWidth = 280;
            var tooltipHeight = 300;
            
            if (x + tooltipWidth > window.innerWidth) {{ x = x - tooltipWidth; }}
            if (y + tooltipHeight > window.innerHeight) {{ y = y - tooltipHeight; }}

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
