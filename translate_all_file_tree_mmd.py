
import sys
from pathlib import Path

import translation_cache_generator

def main():
	if len(sys.argv) != 2:
		print("Usage: python translation_cache_generator.py [path_to_directory_yourd_like_the_tree_translated]")
		return
		
	directoryPath = sys.argv[1]
	texts = []
	texts = Path(directoryPath).glob("**/*")

	def dir_are_there_files(d, suffix):
		bool(list(Path(d).glob(f"**/{suffix}")))

	def should_translate(p):
		return (p.is_dir() and not dir_are_there_files(p, "*.pmx")) or (
			not p.is_dir() and p.suffix == ".pmx"
		)  # and (p.suffix not in [".png", ".jpg", ".jpeg", ".bmp"])

	texts = (str(Path(p).name) for p in texts if should_translate(p))

	translation_cache_generator.main(texts)

if __name__ == "__main__":
	main()