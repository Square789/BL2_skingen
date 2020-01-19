import argparse
import re

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
		idx_start = 0
		idx = 0
		chklist_ln = len(chks)
		not_first_word = False
		while idx < chklist_ln:
			curlnwidth = 0
			line_empty = True
			while True:
				if idx > chklist_ln - 1: # Out of chunks
					break
				if chks[idx] == "\n": # Newline
					idx += 1
					break
				curlnwidth += len(chks[idx])
				idx += 1 # Append next chunk, add to current line length
				if curlnwidth > (width - 1): # -1 due to the space
					idx -= 1
					if line_empty:
						idx += 1
						break # We are done with this line. Width now ruined.
					else:
						break # Whitespace removed in outer loop layer
				line_empty = False
			out.append((not_first_word * " ") +
				"".join(chks[idx_start:idx]).rstrip())
			#if idx < chklist_ln: # Remove whitespace that may appear at start of newline
			#	if chks[idx].isspace():
			#		idx += 1
			idx_start = idx
			not_first_word = True

		return out
