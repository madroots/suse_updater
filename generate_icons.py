import os

def create_svg_icon(color: str, filepath: str, symbol: str = ""):
    """
    Generates a modern, minimalist SVG icon for the system tray.
    color: green, yellow, or red
    symbol: optional text/symbol to put in the middle (like an exclamation mark)
    """
    
    # Map colors to nice sleek gradients
    color_map = {
        "green": ("#00C853", "#69F0AE"),  # Material design A700 to A400
        "yellow": ("#FFAB00", "#FFD740"), # Amber A700 to A400
        "red": ("#D50000", "#FF5252"),    # Red A700 to A200
    }
    
    dark, light = color_map.get(color, ("#555555", "#aaaaaa"))
    
    svg_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad_{color}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{light};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{dark};stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.3"/>
    </filter>
  </defs>
  
  <!-- Sleek rounded squircle background representing openSUSE chameleon curve roughly -->
  <path d="M32 4 C12 4 4 12 4 32 C4 52 12 60 32 60 C52 60 60 52 60 32 C60 12 52 4 32 4 Z" 
        fill="url(#grad_{color})" 
        filter="url(#shadow)"/>
        
  <!-- Optional inner symbol -->
  <text x="32" y="42" 
        font-family="sans-serif" 
        font-size="28" 
        font-weight="bold" 
        fill="#ffffff" 
        text-anchor="middle">{symbol}</text>
        
  <!-- Glassmorphism subtle inner highlight -->
  <path d="M32 4 C12 4 4 12 4 32 C4 18 18 8 32 8 C46 8 60 18 60 32 C60 12 52 4 32 4 Z" 
        fill="#ffffff" 
        opacity="0.2"/>
</svg>
"""
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(svg_content)

if __name__ == "__main__":
    assets_dir = "/home/master/gits/suse-updater/assets/icons"
    os.makedirs(assets_dir, exist_ok=True)
    
    create_svg_icon("green", os.path.join(assets_dir, "tray_green.svg"), "✓")
    create_svg_icon("yellow", os.path.join(assets_dir, "tray_yellow.svg"), "↑")
    create_svg_icon("red", os.path.join(assets_dir, "tray_red.svg"), "!")
    
    # Gear icon for settings
    gear_svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <path d="M60.5,36.5v-9l-6.8-1.2c-0.5-2.1-1.3-4.1-2.5-5.9l4.1-5.6l-6.4-6.4l-5.6,4.1c-1.8-1.2-3.8-2-5.9-2.5L36.5,3.5h-9l-1.2,6.8
	c-2.1,0.5-4.1,1.3-5.9,2.5l-5.6-4.1l-6.4,6.4l4.1,5.6c-1.2,1.8-2,3.8-2.5,5.9l-6.8,1.2v9l6.8,1.2c0.5,2.1,1.3,4.1,2.5,5.9l-4.1,5.6
	l6.4,6.4l5.6-4.1c1.8,1.2,3.8,2,5.9,2.5l1.2,6.8h9l1.2-6.8c2.1-0.5,4.1-1.3,5.9-2.5l5.6,4.1l6.4-6.4l-4.1-5.6c1.2-1.8,2-3.8,2.5-5.9
	L60.5,36.5z M32,44c-6.6,0-12-5.4-12-12s5.4-12,12-12s12,5.4,12,12S38.6,44,32,44z" fill="#ccc"/>
</svg>"""
    with open(os.path.join(assets_dir, "settings_gear.svg"), "w") as f:
        f.write(gear_svg)
    
    print("Icons generated successfully in", assets_dir)
