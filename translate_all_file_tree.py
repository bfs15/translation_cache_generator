
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

	translation_cache_generator.main(texts)

if __name__ == "__main__":
	main()