import logging
from typing import List, Optional

from dahuffman import load_shakespeare, HuffmanCodec
from bitstring import Bits
import numpy as np


log_level = logging.DEBUG
log_file = 'log/agent3.log'

logger = logging.getLogger('Agent 3')
logger.setLevel(log_level)
logger.addHandler(logging.FileHandler(log_file))


def debug(*args) -> None:
    logger.info(' '.join(args))


class Huffman:

    def __init__(
            self,
            dictionary: Optional[List[str]] = None
    ) -> None:
        if dictionary is not None:
            self.codec = HuffmanCodec.from_data(''.join(dictionary))
        else:
            self.codec = load_shakespeare()

    def encode(
            self,
            msg: str
    ) -> Bits:
        bytes = self.codec.encode(msg)
        bits = Bits(bytes=bytes)

        debug('[ Huffman.encode ]', f'msg: {msg} -> bits: {bits.bin}')
        return bits

    def decode(
            self,
            bits: Bits
    ) -> str:
        decoded = self.codec.decode(bits.tobytes())

        debug('[ Huffman.decode ]', f'bits: {bits.bin} -> msg: {decoded}')
        return decoded


class Agent:
    def __init__(
            self
    ) -> None:
        self.stop_card = 51
        self.trash_cards = list(range(32, 51))
        self.rng = np.random.default_rng(seed=42)
        self.huff = Huffman()  # Create huffman object

    def encode(
            self,
            msg: str
    ) -> List[int]:
        encode_msg = []

        # Convert Huffman to binary
        bin = self.huff.encode(msg).bin

        # Split binary into chunks -> Convert to string to do this
        parts = [str(bin)[i:i+5] for i in range(0, len(str(bin)), 5)]

        # For each binary string convert to binary then int using int()
        # and append to encode_msg
        for i in parts:
            # print(int(Bits(bin=i).bin, 2))
            encode_msg.append(int(Bits(bin=i).bin, 2))

        useless_cards = [card for card in range(0, 32)
                         if card not in encode_msg]
        deck = self.trash_cards + useless_cards + [self.stop_card] + encode_msg

        return deck

    def decode(
            self,
            deck
    ):
        deck = self.remove_trash_cards(deck)
        deck = self.get_encoded_message(deck)
        return "NULL"

    def remove_trash_cards(
            self,
            deck
    ) -> List[int]:
        for i in self.trash_cards:
            deck.remove(i)
        return deck

    def get_encoded_message(
            self,
            deck
    ) -> List[int]:
        deck.index(self.stop_card)
        return deck[deck.index(self.stop_card)+1:]


# -----------------------------------------------------------------------------
#   Unit Tests
# -----------------------------------------------------------------------------

def test_huffman_codec():
    # Note: shakespeare codec doesn't seem to be able to handle punctuations
    cases = ['group 3', 'magic code']

    huffman = Huffman()
    for tc in cases:
        orig = tc
        encoded = huffman.encode(orig)
        decoded = huffman.decode(encoded)

        assert type(
            encoded) == Bits, 'error: encoded message is not of type Bits!'
        assert orig == decoded, 'error: decoded message is not the same as the original'

    print('PASSED: Huffman codec using pre-traind shakespeare text')

    cases = ['group 3', 'magic code', 'hi!']
    huffman = Huffman(dictionary=cases)
    for tc in cases:
        orig = tc
        encoded = huffman.encode(orig)
        decoded = huffman.decode(encoded)

        assert type(encoded) == Bits, 'error: encoded message is not of type Bits!'
        assert orig == decoded, 'error: decoded message is not the same as the original'

    print('PASSED: Huffman codec using dictionary')
