from logging import Logger
from re import Pattern
import re
from typing import List, Optional, Tuple, Union

from phonemizer.backend.espeak.espeak import EspeakBackend
from phonemizer.backend.espeak.language_switch import LanguageSwitch
from phonemizer.backend.espeak.words_mismatch import WordMismatch


class CustomEspeakBackend(EspeakBackend):
    def __init__(self, language: str,
                 punct: Optional[str] = None,
                 preserve_regex: Optional[List[str]] = [],
                 preserve_punctuation: bool = False,
                 with_stress: bool = False,
                 tie: Union[bool, str] = False,
                 language_switch: LanguageSwitch = 'keep-flags',
                 words_mismatch: WordMismatch = 'ignore',
                 logger: Optional[Logger] = None):
        self.token = "<|begin_real_number_{index}|> {content}"
        self.regex = '|'.join([f'({pattern})' for pattern in preserve_regex])

        super().__init__(
            language,
            punctuation_marks=punct,
            preserve_punctuation=preserve_punctuation,
            with_stress=with_stress,
            tie=tie,
            language_switch=language_switch,
            words_mismatch=words_mismatch,
            logger=logger
        )

    def phonemize(self, text: List[str]) -> List[str]:
        if not self.regex:
            return super().phonemize(text)

        pre_process = [self.pre_process(
            txt, super().phonemize) for txt in text]
        phonemized = super().phonemize([txt for txt, _ in pre_process])
        post_txt = [self.post_process(phoneme, process[1])
                    for process, phoneme in zip(pre_process, phonemized)]

        return post_txt

    def pre_process(self, txt: str, phonemize):
        counter = [0]
        replacements = []

        def replace_match(match):
            txt = match.group(0)
            token = self.token.format(
                index=counter[0],
                content=txt
            )
            counter[0] += 1
            content = f"{token} {txt}"
            phoneme = phonemize([content])[0]
            replacements.append((phoneme.strip(), txt))

            return content

        processed_text = re.sub(self.regex, replace_match, txt)

        return processed_text, replacements

    def post_process(self, phoneme: str, replacements: List[Tuple[str, str]]):
        for replacement in replacements:
            if replacement[0] in phoneme:
                phoneme = phoneme.replace(
                    replacement[0], replacement[1], 1)
            else:
                print(
                    f"Replacement '{replacement[0]}' not found in '{phoneme}'")

        return phoneme
