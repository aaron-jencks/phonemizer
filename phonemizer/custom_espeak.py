from logging import Logger
import re
from typing import List, Optional, Union, Dict

from phonemizer.backend.espeak.espeak import EspeakBackend
from phonemizer.backend.espeak.language_switch import LanguageSwitch
from phonemizer.backend.espeak.words_mismatch import WordMismatch


def int_to_token(i: int, vocab: str) -> str:
    if i < 0:
        raise ValueError("Only non-negative integers are allowed.")
    base = len(vocab)
    if i < base:
        return vocab[i]
    result = []
    while i >= base:
        result.append(vocab[i % base])
        i = i // base - 1  # subtract 1 to avoid leading 'a' being reused early
    result.append(vocab[i])
    return ''.join(reversed(result))


class CustomEspeakBackend(EspeakBackend):
    def __init__(self, language: str,
                 punct: Optional[str] = None,
                 preserve_regex: Optional[List[str]] = None,
                 token_vocab: str = ',`~',
                 preserve_punctuation: bool = False,
                 with_stress: bool = False,
                 tie: Union[bool, str] = False,
                 language_switch: LanguageSwitch = 'keep-flags',
                 words_mismatch: WordMismatch = 'ignore',
                 logger: Optional[Logger] = None):
        self.token_index = 0
        self.token_vocab = token_vocab
        self.token_prefix = '<<<{}>'
        self.token_suffix = '</{}>>>'
        self.regex = re.compile('|'.join([f'({pattern})' for pattern in preserve_regex])) if preserve_regex else None
        self.mappings: Dict[str, int] = {}

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

            if txt in self.mappings:
                encoded_token = int_to_token(self.mappings[txt], self.token_vocab)
                token = f'{self.token_prefix.format(encoded_token)} {txt} {self.token_suffix.format(encoded_token)}'
                return token

            encoded_token = int_to_token(self.token_index, self.token_vocab)
            token = f'{self.token_prefix.format(encoded_token)} {txt} {self.token_suffix.format(encoded_token)}'
            self.mappings[txt] = self.token_index
            self.token_index += 1

            return token

        processed_text = self.regex.sub(replace_match, txt)

        return processed_text

    def post_process(self, phoneme: str):
        for token in self.mappings:
            index = self.mappings[token]
            index_str = int_to_token(index, self.token_vocab)
            prefix = self.token_prefix.format(index_str)
            suffix = self.token_suffix.format(index_str)

            if prefix not in phoneme:
                raise Exception(f'phoneme {prefix} not in {phoneme}')
            if suffix not in phoneme:
                raise Exception(f'phoneme {suffix} not in {phoneme}')

            phoneme = re.sub(f'{prefix} .*? {suffix}', lambda x: token, phoneme)

        return phoneme
