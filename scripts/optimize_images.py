"""
Download and optimize images for WhatsApp delivery.

Target: Under 200KB, max 1000px wide, JPEG quality 75-80.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_supabase_client
import subprocess
import os
from PIL import Image
import io


def optimize_image(input_path: str, output_path: str, max_width: int = 1000, quality: int = 75):
    """
    Optimize image: resize and compress.

    Args:
        input_path: Path to input image
        output_path: Path to save optimized image
        max_width: Maximum width in pixels
        quality: JPEG quality (1-100)

    Returns:
        tuple: (original_size_kb, optimized_size_kb, reduction_percent)
    """
    original_size = os.path.getsize(input_path)

    # Open and process image
    with Image.open(input_path) as img:
        # Convert to RGB if necessary (handles RGBA, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if wider than max_width
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save with compression
        img.save(output_path, 'JPEG', quality=quality, optimize=True)

    optimized_size = os.path.getsize(output_path)
    reduction = ((original_size - optimized_size) / original_size) * 100

    return (
        original_size / 1024,
        optimized_size / 1024,
        reduction
    )


def main():
    client = get_supabase_client()
    result = client.table('system_diagrams').select('system, image_url').execute()

    print('=' * 80)
    print('IMAGE OPTIMIZATION')
    print('=' * 80)
    print()

    # Create temp directory for downloaded images
    temp_dir = Path('temp_images')
    temp_dir.mkdir(exist_ok=True)

    optimized_dir = Path('optimized_images')
    optimized_dir.mkdir(exist_ok=True)

    results = []

    for item in result.data:
        system = item['system']
        url = item['image_url']

        # Only process remote Wikimedia images
        if not url.startswith('https://upload.wikimedia.org'):
            continue

        print(f'Processing: {system}')
        print(f'  URL: {url}')

        # Download original
        filename = url.split('/')[-1]
        temp_path = temp_dir / filename
        optimized_path = optimized_dir / f'{system.replace(" ", "_")}_optimized.jpg'

        try:
            # Download with curl
            subprocess.run(
                ['curl', '-s', '-A', 'Mozilla/5.0', '-o', str(temp_path), url],
                check=True, timeout=60
            )

            if not temp_path.exists() or temp_path.stat().st_size < 1000:
                print('  ERROR: Download failed or file too small')
                continue

            # Optimize
            orig_kb, opt_kb, reduction = optimize_image(
                str(temp_path),
                str(optimized_path),
                max_width=1000,
                quality=78
            )

            print(f'  Original: {orig_kb:.1f} KB')
            print(f'  Optimized: {opt_kb:.1f} KB')
            print(f'  Reduction: {reduction:.1f}%')
            print(f'  Saved to: {optimized_path}')
            print()

            results.append({
                'system': system,
                'original_kb': orig_kb,
                'optimized_kb': opt_kb,
                'reduction': reduction,
                'optimized_path': optimized_path
            })

        except Exception as e:
            print(f'  ERROR: {e}')
            print()

    print('=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print()
    print(f'{'Component':<30} {'Original':<12} {'Optimized':<12} {'Reduction'}")
    print('-' * 80)

    for r in sorted(results, key=lambda x: x['original_kb'], reverse=True):
        print(f\"{r['system']:<30} {r['original_kb']:>8.1f} KB  {r['optimized_kb']:>8.1f} KB  -{r['reduction']:>5.1f}%\")

    print('=' * 80)
    print()
    print('Next steps:')
    print('1. Review optimized images in optimized_images/ folder')
    print('2. Upload to Supabase Storage')
    print('3. Update database URLs')


if __name__ == '__main__':
    main()
