# %%
import logging
import os
import sys
import re
from pathlib import Path
import shutil
import datetime
import pickle
import json
from threading import Thread
import itertools
import time

# %%

import pykakasi
import translators as ts

# %%

logging.basicConfig(level=logging.WARN)

kanji_add_romaji = True
romanization = "hepburn"
max_backups = 1
backup_dir = "bak/"
cache_dir = "cache/"

update_official_translations = False
asynch_save = False # might be bugged, also no reason to turn on

# non-exclusive
translators_to_use = {
	"google" : True,
	"deepl" : False,
	"bing" : False,
	"google_zh" : False,
	"deepl_zh" : False,
	"bing_zh" : False,
}

# sleep in seconds to wait between requests if it fails
translators_to_wait = {
	"google": 10,
}

# %%

re_hangul = r"\u3131-\uD79D"
re_phonetic = r"[\p{Han}\p{Hiragana}\p{Katakana}A-Za-z0-9]"
re_phonetic = rf"[{re_hangul}\u4E00-\u9FFF\u3040-\u309Fー\u30A0-\u30FFA-Za-z0-9]"
re_phonetic = re.compile(re_phonetic)
re_nonphonetic = r"[^\p{Han}\p{Hiragana}\p{Katakana}A-Za-z0-9]"
re_nonphonetic = rf"[^{re_hangul}\u4E00-\u9FFF\u3040-\u309Fー\u30A0-\u30FFA-Za-z0-9]"
re_nonphonetic = re.compile(re_nonphonetic)

# %%

def main(texts=None):
	# %%
	if not texts:
		if len(sys.argv) != 2:
			print("Usage: python translation_cache_generator.py [text_file_with_entries_on_each_line]")
			return

		textsFilepath = sys.argv[1]
		f = open(textsFilepath, "r")
		texts = f

	# %%

	cache_translations = {}

	if kanji_add_romaji:
		filepath = cache_dir + "cache_translations.json"
		try:
			with open(filepath, "rb") as f:
				cache_translations = json.load(f)
		except FileNotFoundError:
			logging.warning(
				f"Cache file {filepath} not found!!"
			)


	# %%

	official_character_translations = {}
	for tr_dict in itertools.chain(
		Path(".").glob("translation_dict*.json"),
		Path(".").glob("*/translation_dict*.json")
	):
		with open(str(tr_dict), "r") as f:
			official_character_translations.update(json.load(f))
	logging.info(
		f"official_character_translations # Found {len(official_character_translations.keys())} entries in the dictionaries]"
	)
	loops_max = 1
	loops = 0
	trs_save_t = None
	save_frequency = 1000

	kks = pykakasi.kakasi()
	try:
		while True:
			for text in texts:
				trs = {}
				logging.info(text)
				if text in cache_translations:
					trs = cache_translations[text]["trs"]

				if "pykakasi" not in trs:
					result = kks.convert(text)
					trs["pykakasi"] = result

				did_trs = [r["orig"] != r[romanization] for r in trs["pykakasi"]]
				if not any(did_trs):
					for l in ["", "-zh"]:
						for _ in [
							"deepl",
							"google",
							"bing",
						]:
							if _ + l in trs:
								del trs[_ + l]

				if f"pykakasi-{romanization}" not in trs:
					s = ""
					prev_did_tr = ""
					for r in trs["pykakasi"]:
						did_tr = r["orig"] != r[romanization]
						if (prev_did_tr and not did_tr) or (did_tr and not prev_did_tr):
							s.strip()
							s += " "
						s += r[romanization]
						prev_did_tr = did_tr
					trs[f"pykakasi-{romanization}"] = s

				if any(did_trs):

					def _deepl(from_language="ja"):
						l = f"-{from_language}"
						if from_language == "ja":
							l = ""
						if "deepl" + l not in trs or (str(trs["deepl" + l]) == str(-1)):
							try:
								trs["deepl" + l] = translate_deepl(text, from_language)
							except Exception as e:
								trs["deepl" + l] = -1
								logging.warn(str(e))

					def _google(from_language="ja"):
						l = f"-{from_language}"
						if from_language == "ja":
							l = ""
						if "google" + l not in trs or (
							str(trs["google" + l]) == str(-1)
						):
							try:
								trs["google" + l] = translate_google(
									text, from_language
								)
							except Exception as e:
								trs["google" + l] = -1
								logging.warn(str(e))

					def _bing(from_language="ja"):
						l = f"-{from_language}"
						if from_language == "ja":
							l = ""
						if "bing" + l not in trs or (str(trs["bing" + l]) == str(-1)):
							try:
								trs["bing" + l] = translate_bing(text, from_language)
							except Exception as e:
								trs["bing" + l] = -1
								logging.warn(str(e))

					t_google = None
					t_google_zh = None
					t_deepl = None
					t_deepl_zh = None
					t_bing = None
					t_bing_zh = None

					
					if translators_to_use["google"]:
						t_google = Thread(target=_google)
						t_google.start()
					if translators_to_use["deepl"]:
						t_deepl = Thread(target=_deepl)
						t_deepl.start()
					if translators_to_use["bing"]:
						t_bing = Thread(target=_bing)
						t_bing.start()
					if translators_to_use["google_zh"]:
						t_google_zh = Thread(target=_google, kwargs={"from_language": "zh"})
						t_google_zh.start()
					if translators_to_use["deepl_zh"]:
						t_deepl_zh = Thread(target=_deepl, kwargs={'from_language':"zh"})
						t_deepl_zh.start()
					if translators_to_use["bing_zh"]:
						t_bing_zh = Thread(target=_bing, kwargs={'from_language':"zh"})
						t_bing_zh.start()

					
					
					if translators_to_use["google"] and t_google:
						t_google.join()
					if translators_to_use["deepl"] and t_deepl:
						t_deepl.join()
					if translators_to_use["bing"] and t_bing:
						t_bing.join()
					if translators_to_use["google_zh"] and t_google_zh:
						t_google_zh.join()
					if translators_to_use["deepl_zh"] and t_deepl_zh:
						t_deepl_zh.join()
					if translators_to_use["bing_zh"] and t_bing_zh:
						t_bing_zh.join()

					for tw, sleep_time in translators_to_wait.items():
						if trs[tw] == -1:
							time.sleep(sleep_time)

				def get_official_tr(text):
					text = re_nonphonetic.sub("", text)
					ss = ["·", " ", "-", "_"]
					gotten = []
					for (
						name_official,
						translations,
					) in official_character_translations.items():
						full_names = [
							name_in_lang
							for lang, name_in_lang in translations.items()
							if lang
							in [
								"Chinese",
								"Chinese (simple)",
								"Chinese (Traditional)",
								# "Chinese (simple) (roman)",
								# "Chinese (Traditional) (roman)",
								"Japanese",
								"Korean",
							]
						]
						for full_name in full_names:
							full_name = re_nonphonetic.sub("", full_name)
							if full_name and full_name in text:
								gotten.append(name_official)
						for full_name in full_names:
							for s in ss:
								name_splits = full_name.split(s)
								if len(name_splits) < 2:
									continue
								for name_split in name_splits:
									if name_split and name_split in text:
										gotten.append(name_official)
					return gotten

				if update_official_translations:
					if "official" in trs:
						del trs["official"]
				if "official" not in trs:
					o_tr = get_official_tr(text)
					if o_tr:
						trs["official"] = o_tr
					else:
						trs["official"] = None


				logging.info(trs)
				if trs_save_t:
					trs_save_t.join()
					trs_save_t = None
				cache_translations[text] = {
					"trs": trs,
					"did_trs": did_trs,
					"did_tr": any(did_trs),
				}

				if save_frequency and loops % save_frequency == 0:
					filepath = cache_dir + "cache_translations.json"
					if trs_save_t:
						trs_save_t.join()
						trs_save_t = None
					trs_save_t = save_file_a(filepath, cache_translations, asynch=asynch_save)

				did_trs = [r["orig"] != r[romanization] for r in trs["pykakasi"]]
				logging.info(str("".join([r["orig"] for r in trs["pykakasi"]])))
				logging.info(str("".join([r[romanization] for r in trs["pykakasi"]])))
			loops += 1
			print(f"=========== Completed loop {loops} ===========")
			print("")
			print("")

			if loops_max and loops >= loops_max:
				print("Ended loops")
				break

			filepath = cache_dir + "cache_translations.json"
			if trs_save_t:
				trs_save_t.join()
				trs_save_t = None
			trs_save_t = save_file_a(filepath, cache_translations, asynch=asynch_save)
	except Exception as e:
		logging.exception("")
	filepath = cache_dir + "cache_translations.json"
	if trs_save_t:
		trs_save_t.join()
		trs_save_t = None
	trs_save_t = save_file_a(filepath, cache_translations, asynch=asynch_save)


	# %%

	google_tr_count = len(
		[
			i
			for i in cache_translations.items()
			if ("google" in i[1]["trs"]) and i[1]["trs"]["google"] != -1
		]
	)
	print(f"{google_tr_count} elements with google tr")

	official_tr_count = len(
		[
			i
			for i in cache_translations.items()
			if ("official" in i[1]["trs"]) and i[1]["trs"]["google"] != -1
		]
	)
	print(f"{official_tr_count} elements with official tr")

	return cache_translations

# %%

def translate_google(text, from_language="ja"):
	t = ts.google(text, is_detail_result=True, from_language=from_language)
	return [t[0][0], t[1][0][-1][-1][0][0]]


def translate_bing(text, from_language="ja"):
	t = ts.bing(text, is_detail_result=True, from_language=from_language)
	return [t[1]["inputTransliteration"], t[0]["translations"][0]["text"]]


def translate_deepl(text, from_language="ja"):
	t = ts.deepl(text, is_detail_result=True, from_language=from_language)
	return [
		_["postprocessed_sentence"] for _ in t["result"]["translations"][0]["beams"]
	]


# %%


def removeOldFiles(list_of_files, max_files):
	old_files = list(
		sorted(
			list_of_files,
			key=lambda x: os.stat(x).st_ctime,
			reverse=True,
		)
	)[max_files:]
	for f in old_files:
		os.remove(f)
	return old_files


save_funs = {
	"pickle": (pickle.dump, "wb"),
	"json": (lambda data, f: json.dump(data, f, indent=2, ensure_ascii=False), "w"),
}


def save_file(filepath, data, save_fun, backup_dir=backup_dir, max_backups=max_backups):
	if isinstance(save_fun, str):
		save_fun = save_funs[save_fun]
	backup_dir = Path(filepath).parent / backup_dir
	filepath_bak = (
		str(backup_dir / str(Path(filepath).name))
		+ "-"
		+ datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	)
	try:
		try:
			Path(filepath_bak).parent.mkdir(exist_ok=True)
			shutil.copyfile(filepath, filepath_bak)
			try:
				removeOldFiles(
					Path(backup_dir).glob(f"{Path(filepath).name}*"), max_backups
				)
			except Exception as e:
				logging.exception(e)
		except FileNotFoundError:
			pass
		if "b" in save_fun[1]:
			with open(filepath, save_fun[1]) as f:
				save_fun[0](data, f)
		else:
			with open(filepath, save_fun[1], encoding="utf8") as f:
				save_fun[0](data, f)
		print("Saved!", filepath)
	except Exception as e:
		shutil.copyfile(filepath_bak, filepath_bak + ".err")
		logging.warning("Exception on saving file ", filepath)
		logging.exception(e)


def save_file_a(filepath, data, save_fun=None, asynch=False):
	if save_fun == None:
		save_fun = Path(filepath).suffix[1:]

	def _():
		save_file(filepath, data, save_fun=save_fun)

	a = Thread(target=_)
	a.start()
	if not asynch:
		a.join()
		return None
	return a


# %%

if __name__ == '__main__':
	main()