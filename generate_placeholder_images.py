"""
Generate placeholder SVG images for all automotive components.
"""
from pathlib import Path

COMPONENTS = [
    ("catalytic-converter", "Catalytic Converter"),
    ("oxygen-sensor", "Oxygen Sensor"),
    ("maf-sensor", "MAF Sensor"),
    ("throttle-body", "Throttle Body"),
    ("evap-system", "EVAP System"),
    ("fuel-injector", "Fuel Injector"),
    ("egr-valve", "EGR Valve"),
    ("ignition-coil", "Ignition Coil"),
    ("camshaft-sensor", "Camshaft Sensor"),
    ("crankshaft-sensor", "Crankshaft Sensor"),
]

SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="600" height="400">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#f8f9fa;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#e9ecef;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="600" height="400" fill="url(#bg)"/>

  <!-- Icon/Shape representing component -->
  <rect x="200" y="120" width="200" height="120" rx="10" fill="#6c757d" stroke="#495057" stroke-width="3"/>
  <circle cx="230" cy="160" r="15" fill="#adb5bd"/>
  <circle cx="270" cy="160" r="15" fill="#adb5bd"/>
  <circle cx="230" cy="200" r="15" fill="#adb5bd"/>
  <circle cx="270" cy="200" r="15" fill="#adb5bd"/>
  <circle cx="330" cy="160" r="15" fill="#adb5bd"/>
  <circle cx="370" cy="160" r="15" fill="#adb5bd"/>
  <circle cx="330" cy="200" r="15" fill="#adb5bd"/>
  <circle cx="370" cy="200" r="15" fill="#adb5bd"/>

  <!-- Title -->
  <text x="300" y="280" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="#212529">{title}</text>

  <!-- Subtitle -->
  <text x="300" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#6c757d">Diagram Placeholder</text>
  <text x="300" y="345" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#adb5bd">Vehicle Diagnosis Assistant</text>
</svg>'''

def generate_placeholder(filename: str, title: str, output_dir: Path):
    """Generate a placeholder SVG for a component."""
    svg_content = SVG_TEMPLATE.format(title=title)
    output_path = output_dir / f"{filename}.svg"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"Generated: {output_path.name}")

def main():
    """Generate all placeholder images."""
    output_dir = Path("app/static/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating placeholder SVG images...")
    print()

    for filename, title in COMPONENTS:
        generate_placeholder(filename, title, output_dir)

    print()
    print(f"Generated {len(COMPONENTS)} placeholder images in {output_dir}")

if __name__ == "__main__":
    main()
