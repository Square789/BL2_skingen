import logging
import re

LEVELS = ("NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
RE_SEEK_NR = re.compile(r"Level (\d*)")

class SkingenLogFormatter(logging.Formatter):
	"""Log record formatter that identifies the standard inbetween numbers
	("Level 42", "Level 14") and replaces them with the level they stand for
	("ERROR", "DEBUG").
	"""
	def format(self, record: logging.LogRecord):
		if not record.levelname in LEVELS:
			re_res = RE_SEEK_NR.search(record.levelname)
			if not re_res:
				pass
			else:
				re_res = int(re_res[1])
				record.levelname = LEVELS[int(re_res / 10)] 

		return super().format(record)
