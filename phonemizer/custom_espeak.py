from logging import Logger
from re import Pattern
import re
from typing import List, Optional, Union

from phonemizer.backend.espeak.espeak import EspeakBackend
from phonemizer.backend.espeak.language_switch import LanguageSwitch
from phonemizer.backend.espeak.words_mismatch import WordMismatch


class CustomEspeakBackend(EspeakBackend):
    def __init__(self, language: str,
                 punct: Optional[str] = None,
                 preserve_regex: Optional[List[str]] = None,
                 preserve_punctuation: bool = False,
                 with_stress: bool = False,
                 tie: Union[bool, str] = False,
                 language_switch: LanguageSwitch = 'keep-flags',
                 words_mismatch: WordMismatch = 'ignore',
                 logger: Optional[Logger] = None):

        patterns = []

        if punct:
            patterns.append(f'[{re.escape(punct)}]')

        if preserve_regex:
            patterns.extend(f'({pattern})' for pattern in preserve_regex)

        regex = '|'.join(patterns) if patterns else None

        super().__init__(
            language,
            punctuation_marks=re.compile(regex) if regex else None,
            preserve_punctuation=preserve_punctuation,
            with_stress=with_stress,
            tie=tie,
            language_switch=language_switch,
            words_mismatch=words_mismatch,
            logger=logger
        )
