import argparse
import pathlib

from phonemizer import phonemize, separator, version, logger, punctuation
from phonemizer.backend import BACKENDS

def main():
    ap = argparse.ArgumentParser(description="takes an input string and converts it to phonemes")
    ap.add_argument('input', type=str, help='the string to convert')
    ap.add_argument('-l', '--library',
                    type=pathlib.Path,
                    default=pathlib.Path('../espeak-ng/build/lib/libespeak-ng.so'),
                    help='the location of the libespeak-ng.so')
    args = ap.parse_args()

    BACKENDS['espeak'].set_library(args.library)
    try:
        espeak_library = BACKENDS['espeak'].library()
    except RuntimeError:  # pragma: nocover
        espeak_library = None

    if espeak_library is None:
        print('failed to load espeak library')
        exit(1)

    out = phonemize(args.input.splitlines())
    print(out)

if __name__ == '__main__':
    main()
