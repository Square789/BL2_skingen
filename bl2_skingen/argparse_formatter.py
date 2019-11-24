import argparse
import re

WHITESPACE = ("\t", "\n", "\x0b", "\x0c", " ")

WORDSEP_RE = re.compile(r'''
	( # a newline char
		\n
	| # any whitespace
		{ws}+
	| # em-dash between words
		(?<={wp}) -{{2,}} (?=\w)
	| # word, possibly hyphenated
		{nws}+? (?:
		# hyphenated word
			-(?: (?<={lt}{{2}}-) | (?<={lt}-{lt}-))
			(?= {lt} -? {lt})
		| # end of word
			(?={ws}|\Z)
		| # em-dash
			(?<={wp}) (?=-{{2,}}\w)
		)
	)'''.format(
		wp = r'[\w!"\'&.,?]', lt = r'[^\d\W]',
		ws = '[\t\n\x0b\x0c\r ]',
		nws = '[^\t\n\x0b\x0c\r ]'),
	re.VERBOSE) # Borrowed from textwrap.TextWrapper.wordsep_re

class SkingenArgparseFormatter(argparse.HelpFormatter):
	"""Argparse formatter to override the lacking ability of the default
	formatter to display linebreaks. If '\\n' is encountered, a linebreak
	will be forced, whitespace at the start of a line will be preserved.
	Every line that is not the first one will receive a single space as
	first character.
	"""
	def _split_lines(self, text, width):
		chks = [c for c in WORDSEP_RE.split(text) if c]

		out = []
		chklist_i_start = 0
		chklist_i = 0
		chklist_ln = len(chks)
		not_first_word = False
		while chklist_i < chklist_ln:
			curlnwidth = 0
			line_empty = True
			while True:
				#Look at next word
				#Append next word
				#Does it cause width overflow?
				#if yes
				# step back one word
				# is the line empty now?
				# if yes
				#  step fwd one word again, return
				# if no
				#  is last word whitespace?
				#  if yes
				#   chop off, return

				if chklist_i > chklist_ln - 1:
					break
				if chks[chklist_i] == "\n":
					chklist_i += 1
					break
				curlnwidth += len(chks[chklist_i])
				chklist_i += 1
				if curlnwidth > (width - 1): # -1 due to the space
					chklist_i -= 1
					if line_empty:
						chklist_i += 1
						break # We are done with this line. Width now ruined.
					else:
						break # Whitespace removed in outer loop layer
				line_empty = False
			out.append((not_first_word * " ") +
				"".join(chks[chklist_i_start:chklist_i]).rstrip())
			chklist_i_start = chklist_i
			not_first_word = True

		return out
