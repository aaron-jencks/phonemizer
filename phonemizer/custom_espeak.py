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
        self.token_index = 0
        self.token = "<|begin_custom_regex_preservation_{index}|> {content}"
        self.regex = re.compile('|'.join([f'({pattern})' for pattern in preserve_regex]))
        self.mappings = {}

        super().__init__(
            language,
            punctuation_marks=re.compile(punct),
            preserve_punctuation=preserve_punctuation,
            with_stress=with_stress,
            tie=tie,
            language_switch=language_switch,
            words_mismatch=words_mismatch,
            logger=logger
        )

    def phonemize(self, text: List[str]) -> List[str]:
        if not self.regex:
            return super(CustomEspeakBackend, self).phonemize(text)

        result = []
        for txt in text:
            self.mappings = {}
            self.token_index = 0
            pre_process = self.pre_process(txt, super(CustomEspeakBackend, self).phonemize)
            phonemized = super(CustomEspeakBackend, self).phonemize([pre_process])[0]
            post_txt = self.post_process(phonemized)
            result.append(post_txt)
            
        return result

    def pre_process(self, txt: str, phonemize):
        def replace_match(match):
            txt = match.group(0)
            # token = self.token.format(
            #     index=self.token_index,
            #     content=txt
            # )
            # self.token_index += 1
            token = f'<|.{txt}.|>'

            def mark_case(txt) -> str:
                return '<>' + txt.group(0)

            token = re.sub(r'[A-Z]+', mark_case, token)
            
            if txt in self.mappings:
                return token
                
            phoneme = phonemize([token])[0]
            self.mappings[txt] = phoneme.strip()

            return token

        processed_text = self.regex.sub(replace_match, txt)

        return processed_text

    def post_process(self, phoneme: str):
        for token in self.mappings:
            tphoneme = self.mappings[token]
            if tphoneme not in phoneme:
                raise Exception(f"replacement '{tphoneme}' not found in '{phoneme}'")
            phoneme = phoneme.replace(
                tphoneme, token)

        return phoneme
