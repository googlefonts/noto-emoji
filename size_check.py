"""Sanity check image sizes and svg viewboxes."""
from PIL import Image
from pathlib import Path
from lxml import etree
import sys


def _check_image(base_dir, image_dir):
	assert image_dir.is_dir()
	expected_size = (int(image_dir.name), int(image_dir.name))

	num_bad = 0
	num_good = 0
	for image_file in image_dir.iterdir():
		with Image.open(image_file) as image:
			actual_size = image.size
		if expected_size != actual_size:
			print(f"bad_dim {image_file.relative_to(base_dir)} actual {actual_size} expected {expected_size}")
			num_bad += 1
		else:
			num_good += 1
	return num_bad, num_good

def _check_svg(base_dir, svg_dir):
	expected_viewbox = (0.0, 0.0, 128.0, 128.0)
	num_bad = 0
	num_good = 0
	for svg_file in svg_dir.iterdir():
		if not svg_file.name.startswith("emoji_u"):
			continue
		assert svg_file.is_file()
		with open(svg_file) as f:
			actual_viewbox = etree.parse(f).getroot().attrib["viewBox"]
		actual_viewbox = tuple(float(s) for s in actual_viewbox.split(" "))
		if expected_viewbox != actual_viewbox:
			print(f"bad_dim {svg_file.relative_to(base_dir)} actual {actual_viewbox} expected {expected_viewbox}")
			num_bad += 1
		else:
			num_good += 1
	return num_bad, num_good

def main():
	base_dir = Path(__file__).parent
	image_dir = base_dir / "png"
	svg_dir = base_dir / "svg"

	assert image_dir.is_dir()
	assert svg_dir.is_dir()

	for size_dir in image_dir.iterdir():
		num_bad, num_good = _check_image(base_dir, size_dir)
		print(f"{num_bad}/{num_bad+num_good} issues with {size_dir}")
	num_bad, num_good = _check_svg(base_dir, svg_dir)
	print(f"{num_bad}/{num_bad+num_good} issues with {svg_dir}")
	sys.exit(num_bad)

if __name__ == "__main__":
   main()