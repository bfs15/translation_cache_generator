
import translation_cache_generator
from pathlib import Path

texts = []
texts = Path(".").glob("**/*")

translation_cache_generator.main(texts)