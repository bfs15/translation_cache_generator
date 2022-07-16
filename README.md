

# How to use

## Example to translate a text files's lines

```shell
python translation_cache_generator.py text_file_with_entries_to_be_translated_on_each_line.txt
```

## Example to translate a folder tree

```python

import translation_cache_generator
from pathlib import Path

texts = []
texts = Path(".").glob("**/*")

translation_cache_generator.main(texts)
```

# output

Outputs a .json file in the format:

```json
{
  "Texts entry 1 to be translated from input": {
    "trs": {
      "pykakasi": [
		// pykakasi ouput, look the library up, used to detect japanese sections in the text
      ],
      "deepl": [
        "Text translated by deepl version 1",
        "Text translated by deepl version 2... etc.",
      ],
      "google": [
        "Text translated by google (phonetic)",
        "Text translated by google",
      ],
      "bing": [
        "Text translated by bing (phonetic)",
        "Text translated by bing",
      ]
    },
    "did_trs": [
      true,
	  // ... however many sections of text were detected by pykakasi
	  // truth value is if the sections was translated or was already roman/english
    ],
    "did_tr": true  // if any translation was done, from pykakasi
  }
  // ... other entries, i.e.  "Texts entry 2 to be translated from input": {
}
```