
import translation_cache_generator
from pathlib import Path


texts = []
texts = Path(".").glob("**/*")

def dir_are_there_files(d, suffix):
	bool(list(Path(d).glob(f"**/{suffix}")))

def should_translate(p):
	return (p.is_dir() and not dir_are_there_files(p, "*.pmx")) or (
		not p.is_dir() and p.suffix == ".pmx"
	)  # and (p.suffix not in [".png", ".jpg", ".jpeg", ".bmp"])

texts = (str(Path(p).name) for p in texts if should_translate(p))


translation_cache_generator.main(texts)