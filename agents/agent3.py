from abc import abstractmethod, ABC
from enum import Enum
import logging
from typing import List, Optional
from cards import valid_deck
import re
from dahuffman import load_shakespeare, HuffmanCodec
from bitstring import Bits
import numpy as np
from math import factorial as fac
from itertools import groupby
import requests

log_level = logging.DEBUG
log_file = 'log/agent3.log'

logger = logging.getLogger('Agent 3')
logger.setLevel(log_level)
logger.addHandler(logging.FileHandler(log_file))


def debug(*args) -> None:
    logger.info(" ".join(args))


# -----------------------------------------------------------------------------
#   Agent Parameters
# -----------------------------------------------------------------------------

MAX_CHUNK_SIZE = 6


class PermutationGenerator:
    # From https://codegolf.stackexchange.com/questions/114883/i-give-you-nth-permutation-you-give-me-n

    def __init__(self):
        self.alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
        self.fact = [0] * 34
        self.fact[0] = 1
        for i in range(1, 32):
            self.fact[i] = (self.fact[i - 1] * i)

    def encode(self, cards, rank):
        ''' Encode the given cards into a permutation of the given rank '''
        base = self.alphabet[:len(cards)]

        permutation = self._perm_unrank(rank, base)
        if permutation is None:
            print(
                f"trying to create permuation for number {rank} with {len(cards)} cards"
            )
            return cards

        return [cards[self.alphabet.index(i)] for i in permutation]

    def decode(self, cards):
        ''' Decode the given permuted cards into a rank '''
        sortedCards = [
            str(sortedCard)
            for sortedCard in sorted([int(card) for card in cards])
        ]

        target = ''.join(
            [self.alphabet[sortedCards.index(card)] for card in cards])
        base = self.alphabet[:len(cards)]

        return self._perm_rank(target, base)

    def perm_count(self, s):
        ''' Count the total number of permutations of sorted sequence `s` '''
        n = fac(len(s))
        for _, g in groupby(s):
            n //= fac(sum(1 for u in g))
        return n

    def n_needed(self, messageLength):
        """Returns the number of cards needed to encode a message of
        messageLength using permutation."""
        for i in range(100):
            if messageLength < self.fact[i]:
                return i

    def _perm_rank(self, target, base):
        ''' Determine the permutation rank of string `target`
            given the rank zero permutation string `base`,
            i.e., the chars in `base` are in lexicographic order.
        '''
        if len(target) < 2:
            return 0
        total = 0
        head, newtarget = target[0], target[1:]
        for i, c in enumerate(base):
            newbase = base[:i] + base[i + 1:]
            if c == head:
                return total + self._perm_rank(newtarget, newbase)
            elif i and c == base[i - 1]:
                continue
            total += self.perm_count(newbase)

    def _perm_unrank(self, rank, base, head=''):
        ''' Determine the permutation with given rank of the 
            rank zero permutation string `base`.
        '''
        if len(base) < 2:
            return head + ''.join(base)

        total = 0
        for i, c in enumerate(base):
            if i < 1 or c != base[i - 1]:
                newbase = base[:i] + base[i + 1:]
                newtotal = total + self.perm_count(newbase)
                if newtotal > rank:
                    return self._perm_unrank(rank - total, newbase, head + c)
                total = newtotal

# -----------------------------------------------------------------------------
#   String -> Domain Detector
# -----------------------------------------------------------------------------

class DomainRule(ABC):
    @abstractmethod
    def verdict(self, msg: str) -> bool:
        pass

class GenericRule:
    def verdict(self, _: str) -> bool:
        return True

class PasswordRule:
    def verdict(self, msg: str) -> bool:
        pattern = re.compile("^@[a-z0-9,.]+$") #TODO: can't handle capitals
        return pattern.match(msg)

class RandomAlphaNumericRule: #not tested
    def verdict(self, msg: str) -> bool:
        pattern = re.compile("^[a-z0-9,.]+$")
        return pattern.match(msg)

class CoordinatesRule:
    def verdict(self, msg: str) -> bool:
        pattern = re.compile("^[0-9]{1,}.[0-9]{4} [NESW], [0-9]{1,}.[0-9]{4} [NESW]$") #TODO: assumes sigfigs of 4
        return pattern.match(msg)

class AddressRule:
    def verdict(self, msg: str) -> bool:
        road_words = ["Street", "Road", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Roadway", "Trail", "Parkway", "Commons", "Av", "Av.", "Ave", "St.", "St", "Rd", "Rd.", "Mall", "Plaza", "Route", "Highway", "Pike", "Pkwy", "Blvd", "Blvd.", "Turnpike", "Expy", "Ct", "Ct.", "Freeway"] #TODO: are there more?
        for word in road_words:
            if word in msg:
                return True
        return False

class SixWordRule: #not tested much
    def verdict(self, msg: str) -> bool:
        # pattern = re.compile("^([a-z]+ ){5}([a-z]+)$") # Changed to accept any num words that are in it 
        pattern = re.compile("^([a-z]+ )*([a-z]+)$")
        with open("./messages/agent7/30k.txt") as f:
            all_words = [word.strip() for word in f.read().splitlines()]
        return pattern.match(msg) and all([word in all_words for word in msg.split(" ")])

class AirplaneFlightRule:
    def verdict(self, msg: str) -> bool:
        striped_msg = ' '.join([word.strip() for word in msg.split()])
        pattern = re.compile("^([A-Z0-9]{3} )([A-Z.'-]* )+([0-9]+)$")#TODO: can't handle lowercase or numbers in middle
        return pattern.match(striped_msg)

class PlaceNameRule: #not tested much
    def verdict(self, msg: str) -> bool:
        pattern = re.compile("^([A-Z][a-z]+) ([A-Z][a-z]+)$")
        with open("./messages/agent8/names.txt") as f: #TODO: find giant list of names and places
            all_words = [word.strip() for word in f.read().splitlines()]
        with open("./messages/agent8/places.txt") as f:
            all_words += [word.strip() for word in f.read().splitlines()]
        return pattern.match(msg) and all([word in all_words for word in msg.split(" ")])

class WarWordsRule:
    def verdict(self, msg: str) -> bool:
        pattern = re.compile("^([a-z]+ )*([a-z]+)$") #TODO: can't handle numbers
        with open("./messages/agent6/corpus-ngram-1.txt") as f: #TODO not sure the actual format
            all_words = [word.strip() for word in f.read().splitlines()]
        return pattern.match(msg) and all([word in all_words for word in msg.split(" ")])


class Domain(Enum):
    GENERIC  = GenericRule
    PASSWORD = PasswordRule
    ALPHA_NUMERIC = RandomAlphaNumericRule
    COORDS = CoordinatesRule
    ADDRESS = AddressRule
    SIX_WORDS = SixWordRule
    FLIGHTS = AirplaneFlightRule
    PLACES_AND_NAMES = PlaceNameRule
    WAR_WORDS = WarWordsRule

class DomainDetector:
    def __init__(self, domains: list[Domain], default_domain=Domain.GENERIC):
        self.domains = domains
        self.default_domain = default_domain

    def detect(self, msg: str) -> Domain:
        for domain in self.domains:
            rule = domain.value()
            if rule.verdict(msg):
                return domain
        return Domain.GENERIC


# -----------------------------------------------------------------------------
#   String <-> String Message TransFormer (Compression, DeCompression)
# -----------------------------------------------------------------------------

class MessageTransformer(ABC):
    @abstractmethod
    def compress(self, msg: str) -> Bits:
        pass

    @abstractmethod
    def uncompress(self, bits: Bits) -> str:
        pass


class GenericTransformer(MessageTransformer):
    def __init__(self):
        self.huffman = Huffman()

    def compress(self, msg: str) -> Bits:
        bits = self.huffman.encode(msg, padding_len=0)
        debug(f'GenericTransformer: "{msg}" -> {bits.bin}')

        return bits

    def uncompress(self, bits: Bits) -> str:
        msg = self.huffman.decode(bits, padding_len=0)
        debug(f'GenericTransformer: "{bits.bin}" -> {msg}')

        return msg

class WordTransformer(MessageTransformer):
    def __init__(self, delimiter=" ", wordlist=None, huffman_encoding=None):
        self.huffman = Huffman() if huffman_encoding is None else huffman_encoding

        #---------------------------------------------------------------------
        #  Obtain abbreviation for words in a dictionary.
        #---------------------------------------------------------------------
        # Note: self.word2abrev stores the mapping of word to abbreviation
        self.delim = delimiter

        # if can use precomp, comment this out
        if wordlist is None:
            r = requests.get(
                'https://raw.githubusercontent.com/mwcheng21/minified-text/main/minified.txt'
            )
            minified_text = r.text
            self.abrev2word = {}
            self.word2abrev = {}
            for line in minified_text.splitlines():
                [shortened, full] = line.split(' ')
                self.abrev2word[shortened] = full
                self.word2abrev[full] = shortened
        else:
            with open(wordlist, 'r') as f:
                self.abrev2word = {}
                self.word2abrev = {}
                for line in f.readlines():
                    line = line.strip()
                    [shortened, full] = line.split(' ')
                    self.abrev2word[shortened] = full
                    self.word2abrev[full] = shortened

    def compress(self, msg: str) -> Bits:
        msg = self.delim.join([
            self.word2abrev[word] if word in self.word2abrev else word
            for word in msg.split(self.delim)
        ])
        bits = self.huffman.encode(msg, padding_len=0)

        return bits

    def uncompress(self, bits: Bits) -> str:
        decoded_message = self.huffman.decode(bits, padding_len=0)
        original_message = self.delim.join([
            self.abrev2word[word] if word in self.abrev2word else word
            for word in decoded_message.split(self.delim)
        ])

        return original_message

class PasswordsTransformer(MessageTransformer):
    def __init__(self):
        self.huffman = Huffman()

    def compress(self, msg: str) -> Bits:
        bits = self.huffman.encode(msg, padding_len=0)
        debug(f'GenericTransformer: "{msg}" -> {bits.bin}')

        return bits

    def uncompress(self, bits: Bits) -> str:
        msg = self.huffman.decode(bits, padding_len=0)
        debug(f'GenericTransformer: "{bits.bin}" -> {msg}')

        return msg

class CoordsTransformer(MessageTransformer):
    def __init__(self):
        self.huffman = Huffman()

    def compress(self, msg: str) -> Bits:
        bits = self.huffman.encode(msg, padding_len=0)
        debug(f'GenericTransformer: "{msg}" -> {bits.bin}')

        return bits

    def uncompress(self, bits: Bits) -> str:
        msg = self.huffman.decode(bits, padding_len=0)
        debug(f'GenericTransformer: "{bits.bin}" -> {msg}')

        return msg
  
class AddressTransformer(MessageTransformer): #TODO: later bc format not finalized
    def __init__(self):
        self.huffman = Huffman()

    def compress(self, msg: str) -> Bits:
        bits = self.huffman.encode(msg, padding_len=0)
        debug(f'GenericTransformer: "{msg}" -> {bits.bin}')

        return bits

    def uncompress(self, bits: Bits) -> str:
        msg = self.huffman.decode(bits, padding_len=0)
        debug(f'GenericTransformer: "{bits.bin}" -> {msg}')

        return msg
       
class FlightsTransformer(MessageTransformer): #TODO: later bc format not finalized
    def __init__(self):
        self.huffman = Huffman()

    def compress(self, msg: str) -> Bits:
        bits = self.huffman.encode(msg, padding_len=0)
        debug(f'GenericTransformer: "{msg}" -> {bits.bin}')

        return bits

    def uncompress(self, bits: Bits) -> str:
        msg = self.huffman.decode(bits, padding_len=0)
        debug(f'GenericTransformer: "{bits.bin}" -> {msg}')

        return msg

# TODO: adding freq prevents cases of things not in it
class WarWordsTransformer(MessageTransformer):
    def __init__(self):
        self.freq = {' ': 15000, 'e': 2490, 's': 1960, 'a': 1852, 'r': 1672, 'i': 1648, 't': 1488, 'n': 1482, 'o': 1307, 'd': 1168, 'l': 1147, 'c': 1106, 'p': 835, 'm': 727, 'g': 668, 'u': 645, 'h': 542, 'b': 483, 'f': 468, 'v': 367, 'w': 348, 'k': 322, 'y': 312, '0': 140, '1': 96, '2': 77, 'j': 68, 'z': 58, '5': 55, 'x': 52, '3': 50, '4': 45, '7': 34, '9': 34, 'q': 30, '8': 29, '6': 25}
        self.huffman = Huffman(self.freq)
        self.word_file = "./messages/agent3/dicts/shortened_dicts/war_words_mini.txt"
        self.transformer = WordTransformer(wordlist=self.word_file, huffman_encoding=self.huffman)

    def compress(self, msg: str) -> Bits: #TODO: maybe clean messages?
        return self.transformer.compress(msg)

    def uncompress(self, bits: Bits) -> str:
        return self.transformer.uncompress(bits)

class PlacesAndNamesTransformer(MessageTransformer):
    def __init__(self):
        self.freq = {' ': 25000, 'a': 15393, 'e': 11709, 'n': 9319, 'l': 8288, 'r': 7848, 'i': 7821, 's': 6479, 'o': 5599, 't': 5435, 'h': 4205, 'm': 4110, 'd': 3968, 'c': 3925, 'k': 3022, 'y': 2902, 'b': 2377, 'u': 2122, 'g': 1805, 'j': 1767, 'v': 1601, 'w': 1476, 'p': 1375, 'f': 1041, 'z': 518, 'q': 323, 'x': 169}
        self.huffman = Huffman()
        self.word_file = "./messages/agent3/dicts/shortened_dicts/places_and_names_mini.txt"
        self.transformer = WordTransformer(wordlist=self.word_file, huffman_encoding=self.huffman)

    def compress(self, msg: str) -> Bits:
        return self.transformer.compress(msg.lower())

    def uncompress(self, bits: Bits) -> str:
        decoded_msg = self.transformer.uncompress(bits)
        capitalized_msg = [word.capitalize() for word in decoded_msg.split()]
        return " ".join(capitalized_msg)

class SixWordsTransformer(MessageTransformer):#TODO: change this to idxs??
    def __init__(self):
        self.freq = {' ': 60000, 'e': 12351, 'a': 10065, 's': 9847, 'r': 8604, 'i': 8586, 't': 7560, 'n': 7484, 'o': 7095, 'c': 5985, 'l': 5970, 'd': 5057, 'p': 4221, 'm': 4148, 'u': 3405, 'g': 3281, 'h': 3040, 'b': 2787, 'f': 2164, 'y': 1891, 'v': 1602, 'w': 1579, 'k': 1390, 'x': 532, 'j': 486, 'z': 371, 'q': 284}
        self.huffman = Huffman(self.freq)
        self.word_file = "./messages/agent3/dicts/shortened_dicts/six_words_mini.txt"
        self.transformer = WordTransformer(wordlist=self.word_file, huffman_encoding=self.huffman)

    def compress(self, msg: str) -> Bits:
        return self.transformer.compress(msg)

    def uncompress(self, bits: Bits) -> str:
        return self.transformer.uncompress(bits)

class AlphaNumericTransformer(MessageTransformer):
    def __init__(self):
        self.freq = {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1, "f": 1, "g": 1, "h": 1, "i": 1, "j": 1, "k": 1, "l": 1, "m": 1, "n": 1, "o": 1, "p": 1, "q": 1, "r": 1, "s": 1, "t": 1, "u": 1, "v": 1, "w": 1, "x": 1, "y": 1, "z": 1, "0": 1, "1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1, "8": 1, "9": 1, ".": 1, ",": 1, " ": 1}
        self.huffman = Huffman(self.freq)

    def compress(self, msg: str) -> Bits:
        bits = self.huffman.encode(msg, padding_len=0)
        debug(f'GenericTransformer: "{msg}" -> {bits.bin}')

        return bits

    def uncompress(self, bits: Bits) -> str:
        msg = self.huffman.decode(bits, padding_len=0)
        debug(f'GenericTransformer: "{bits.bin}" -> {msg}')

        return msg
       
# -----------------------------------------------------------------------------
#   Bits <-> Deck Converter (BDC)
# -----------------------------------------------------------------------------
Deck = list[int]

class BDC(ABC):
    """Bits <-> Deck Converter."""
    def __init__(self, cards: Deck):
        self._cards = cards # cards that can be used to encode bits

    @property
    def cards(self):
        return self._cards

    @abstractmethod
    def to_deck(self, bits: Bits) -> Optional[tuple[Deck, Deck]]:
        """Returns message deck, including any message metadata."""
        pass

    @abstractmethod
    def to_bits(self, msg: Deck, msg_metadata: Deck) -> Optional[Bits]:
        pass

class ChunkConverter(BDC):
    """Converts between bits and deck of cards by mapping each chunk of bits
    to a card, using linear probing if there are collisions."""

    def __init__(self, cards: Deck, max_chunk_size=MAX_CHUNK_SIZE):
        super().__init__(cards)
        self.permuter = PermutationGenerator()
        self.trash_card_start_idx = 32
        self.max_chunk_size = max_chunk_size

    def _n_needed_metadata(self, messageLength: int):
        """Returns the number of cards needed to encode the metadata."""
        return self.permuter.n_needed(messageLength)

    def _encode_metadata(self, step_size: str, start_padding: str,
                        end_padding: str, lengths: str, cards: Deck
                        ) -> Deck:
        """Encode the message metadata into a deck.""" 
        cards = [str(card) for card in cards]

        metadata = step_size + start_padding + end_padding + lengths

        last_n_cards = cards[-self._n_needed_metadata(2**len(metadata)):]
        permutation = self.permuter.encode(last_n_cards, int(metadata, 2))

        return [int(card) for card in permutation]

    def _decode_metadata(self, msg_metadata: Deck, msg_len: int):
        """Decodes the metadata from the deck.
        
        Returns a tuple of step_size, start_padding, end_padding, lengths.
        """
        cards = [str(card) for card in msg_metadata]
        last_n_cards = cards[-self._n_needed_metadata(2**(msg_len + 3 + 3 + 2)):]

        metadata = self.permuter.decode(last_n_cards)
        metadata = '{0:b}'.format(metadata).zfill(2 + 3 + 3 + msg_len)
        step_size = int(metadata[:2], 2)
        start_padding = int(metadata[2:5], 2)
        end_padding = int(metadata[5:8], 2)
        lengths = metadata[8:8 + msg_len]

        return step_size, start_padding, end_padding, lengths

    def _unhash_msg(self, encoded_msg, step_size):
        """Attempts to unhash the encoded message."""
        step_size = step_size if step_size != 3 else 5
        encoded_msg_hash_table = {}

        message = []
        for i, card in enumerate(encoded_msg):
            address_of_card = card
            while address_of_card - step_size in encoded_msg_hash_table:
                address_of_card -= step_size

            encoded_msg_hash_table[card] = address_of_card
            message.append(address_of_card)
        return message

    def _hash_msg_with_linear_probe(self, chunks, step_size):
        """Attempts a linear probe at the given step size."""
        hash_table = {}
        step_size = step_size if step_size != 3 else 5

        encoded_msg = []
        for chunk in chunks:
            address_of_chunk = chunk
            # TODO: can't know if [26, 27] corresponds to [26, 27] or [26, 26], without
            # metadata
            while address_of_chunk in hash_table or address_of_chunk not in self.cards:
                address_of_chunk += step_size

                # if address_of_chunk is larger than the largest card we can use,
                # we can't use it to encode our message, thus return an empty array
                # to indicate that we can't encode using linear probing
                #
                # TODO: use mod, so that after address_of_chunk is greater than the
                # maximum, wrap around.
                if address_of_chunk > max(self.cards):
                    return []

            hash_table[address_of_chunk] = chunk
            encoded_msg.append(address_of_chunk)

        return encoded_msg

    def _can_hash_msg(self, chunks) -> bool:
        for i in range(1, 4):
            encoded_msg = self._hash_msg_with_linear_probe(chunks, i)
            decoded_hash = self._unhash_msg(encoded_msg, i)
            if decoded_hash == chunks:
                return True and max(encoded_msg) < 32, i
        return False, None

    def _get_parts(self, bit_str):
        """Takes in a bit string, checks if it's possible to encode.
        
        Returns a tuple of is_able_to_encode, parts, start_padding,
                           end_padding, contains_no_duplicates.
        """
        chunk_size = self.max_chunk_size

        # TODO: why are we taking a max here, the second component will always
        # be smaller than chunk_size.
        padding = max(chunk_size,
                      ((chunk_size - len(bit_str) % chunk_size) % chunk_size))
        last_card_padding = 0

        for i in range(padding):
            start_padding = i

            padded_bit_str = '0' * start_padding + bit_str
            parts = []
            while len(padded_bit_str) > 0 and chunk_size <= len(
                    padded_bit_str):
                if padded_bit_str[:chunk_size][0] == '0':
                    parts.append(padded_bit_str[:chunk_size])
                    padded_bit_str = padded_bit_str[chunk_size:]
                else:
                    parts.append(padded_bit_str[:chunk_size - 1])
                    padded_bit_str = padded_bit_str[chunk_size - 1:]

            if len(padded_bit_str) > 0:
                last_card_padding = chunk_size - len(padded_bit_str)
                potential_card = padded_bit_str + '0' * last_card_padding
                if potential_card in parts or potential_card[0] == '1':
                    last_card_padding -= 1
                    potential_card = padded_bit_str + '0' * last_card_padding
                parts.append(potential_card)

            int_deck = [int(part, 2) for part in parts]
            _int_deck_set = set(int_deck)
            if (len(int_deck) == len(_int_deck_set)
                and _int_deck_set.issubset(set(self.cards))):
                # no duplicates and only uses available cards
                return 0, parts, start_padding, last_card_padding

            # must be duplicates, so check if can hash
            canHash, step_size = self._can_hash_msg(int_deck)
            if canHash:
                break
        # TODO: where's the if block for this else block?
        else:
            return -1, None, None, None

        return step_size, parts, start_padding, last_card_padding

    def to_deck(self, bits: Bits) -> Optional[tuple[Deck, Deck]]:
        step_size, parts, start_padding, end_padding = self._get_parts(bits.bin)

        if step_size < 0:
            # could not encode message
            return None

        chunk_size = [len(part) for part in parts]
        msg_cards = [int(part, 2) for part in parts]

        if step_size > 0:
            # has duplicate bit chunks, hash with linear probing
            msg_cards = self._hash_msg_with_linear_probe(msg_cards, step_size=step_size)

        # Message Metadata Format:
        #       + --------- + ------------- + ----------- + --------------------- +
        #       | step size | start padding | end padding | chunk size of n cards |
        #       + --------- + ------------- + ----------- + --------------------- +
        # bits:       2             3              3                 n
        lengths = "".join([
            "0" if size == self.max_chunk_size else "1"
            for size in chunk_size
        ])
        end_padding = '{0:b}'.format(end_padding).zfill(3)
        start_padding = '{0:b}'.format(start_padding).zfill(3)
        step_size = '{0:b}'.format(step_size).zfill(2)

        # given the unused cards, encode the metadata
        unused_cards = [
            card for card in self.cards
            if card not in msg_cards
        ]
        msg_metadata_cards = self._encode_metadata(
            step_size, start_padding, end_padding, lengths, unused_cards)

        return msg_metadata_cards, msg_cards

    def to_bits(self, msg: Deck, msg_metadata: Deck) -> Optional[Bits]:
        # decode metadata
        step_size, start_padding, end_padding, lengths = self._decode_metadata(msg_metadata, len(msg))

        if step_size == 0:
            # no linear probing
            cards = msg
        else:
            # linear probing
            cards = self._unhash_msg(msg, step_size)

        # decode message
        chunk_sizes = [
            self.max_chunk_size if length == '0' else self.max_chunk_size - 1
            for length in lengths
        ]
        bit_str = ''.join([
            '{0:b}'.format(card).zfill(chunk_sizes[i])
            for i, card in enumerate(cards)
        ])

        if end_padding > 0:
            bit_str = bit_str[start_padding:-end_padding] 
        else:
            bit_str = bit_str[start_padding:]

        return Bits(bin=bit_str)

class PermutationConverter(BDC):
    """Converts between bits and deck of cards by mapping each permutation of
    cards to a unique integer in its binary representation."""

    def to_deck(self, bits: Bits) -> Optional[tuple[Deck, Deck]]:
        # TODO: actually encode the message
        return [], [20]

    def to_bits(self, msg: Deck, msg_metadata: Deck) -> Optional[Bits]:
        # TODO: actually decode the message
        bits = Bits(uint=msg[0], length=5)
        debug(f"recovered message deck: {msg} -> {bits.bin}")

        return bits

def to_partial_deck(domain: Domain, msg_bits: Bits, free_cards: Deck) -> Optional[tuple[Deck, Deck, Deck]]:
    """Dynamically select the best BDC to encode bits to deck."""
    meta_codec = MetaCodec()

    for bdc in [ChunkConverter, PermutationConverter]:
        metadata_deck = meta_codec.encode(domain, bdc)

        # compute cards availabe for encoding the message, to avoid
        # collision between metadata cards and message cards
        free_msg_cards = [card for card in free_cards if card not in metadata_deck]
        msg_deck = bdc(free_msg_cards).to_deck(msg_bits)

        if msg_deck is not None:
            return metadata_deck, *msg_deck

    return None

# -----------------------------------------------------------------------------
#   Bits <-> String Codec
# -----------------------------------------------------------------------------

class MetaCodec:
    """Codec for (domain, BDC) <-> deck"""
    def __init__(self):
        self.domains = [
                Domain.PASSWORD, Domain.COORDS, # format specific
                Domain.ADDRESS, Domain.FLIGHTS, # format specific with dictionary
                Domain.WAR_WORDS, Domain.PLACES_AND_NAMES, Domain.SIX_WORDS, # dictionary domains
                Domain.ALPHA_NUMERIC, # format generic
                Domain.GENERIC #generic all
            ]
        self.BDCs = [ChunkConverter, PermutationConverter]
        self.domain_mappings = {
            Domain.PASSWORD: 0,
            Domain.COORDS: 1,
            Domain.ADDRESS: 2,
            Domain.FLIGHTS: 3,
            Domain.WAR_WORDS: 4,
            Domain.PLACES_AND_NAMES: 5,
            Domain.SIX_WORDS: 6,
            Domain.ALPHA_NUMERIC: 7,
            Domain.GENERIC: 7,# TODO: map to default, what should default be?
        }


    def encode(self, domain: Domain, bdc: BDC) -> Deck:
        # use the index to represent domain and BDC
        domain_idx = self.domain_mappings[domain]
        bdc_idx = self.BDCs.index(bdc)

        # metadata bit representation:
        # domain (3 bits) + BDC (1 bit) => metadata (4 bits)
        domain_bits = Bits(uint=domain_idx, length=3)
        bdc_bit = Bits(uint=bdc_idx, length=1)
        metadata = Bits(bin=f'0b{domain_bits.bin}{bdc_bit.bin}')

        # Bit -> Card
        deck = [metadata.uint]

        # logging
        debug('MetaCodec encode: %s (domain), %s (BDC) -> %s (deck)' % (domain.name, bdc, str(deck)))
        debug("%-7s %-5s %5s %-5s %10s" % ("DOMAIN", "BITS", "BDC", "BITS", "METADATA"))
        debug( "%-7d %-5s %5d %-5s %10s" %
            (domain_idx, domain_bits.bin, bdc_idx, bdc_bit.bin, metadata.bin))

        return deck

    def decode(self, deck: Deck) -> tuple[Domain, BDC]:
        metadata = Bits(uint=deck[0], length=4)
        bdc_bit, domain_bits = metadata.bin[-1], metadata.bin[:-1]

        bdc_idx = int(bdc_bit, 2)
        domain_idx = int(domain_bits, 2)

        bdc = self.BDCs[bdc_idx]
        domain = self.domains[domain_idx]

        debug('MetaCodec decode:  %s (deck) -> %s (domain), %s (BDC)' % (str(deck), domain.name, bdc))
        debug("%-7s %-5s %5s %-5s %10s" % ("DOMAIN", "BITS", "BDC", "BITS", "METADATA"))
        debug( "%-7d %-5s %5d %-5s %10s" %
            (domain_idx, domain_bits, bdc_idx, bdc_bit, metadata.bin))

        return domain, bdc


class Huffman:

    def __init__(self, dictionary: Optional[List[str]] = None) -> None:
        if dictionary is not None:
            self.codec = HuffmanCodec.from_frequencies(dictionary)
        else:
            self.codec = load_shakespeare()

    def _add_padding(self, msg: Bits, padding_len: int) -> Bits:

        padding_bits = '{0:b}'.format(0).zfill(
            padding_len) if padding_len > 0 else ''
        padded_msg_bin = '0b{}{}'.format(padding_bits, msg.bin)

        padded_msg = Bits(bin=padded_msg_bin)

        debug('[ Huffman._add_padding ]',
              f'len(msg): {len(msg)}, msg: {msg.bin}',
              f'padding size: {padding_len}', f'padded msg: {padded_msg.bin}')

        return padded_msg

    def _remove_padding(self, msg: Bits, padding_len: int) -> Bits:
        original_encoding = Bits(bin=f'0b{msg.bin[padding_len:]}')

        debug('[ Huffman._remove_padding ]',
              f'original encoding: {original_encoding.bin}')

        return original_encoding

    def encode(self, msg: str, padding_len: int = 5) -> Bits:
        bytes = self.codec.encode(msg)
        bits = Bits(bytes=bytes)
        debug('[ Huffman.encode ]', f'msg: {msg} -> bits: {bits.bin}')
        padded_bits = self._add_padding(bits, padding_len)

        return padded_bits

    def decode(self, bits: Bits, padding_len: int = 5) -> str:
        bits = self._remove_padding(bits, padding_len)
        decoded = self.codec.decode(bits.tobytes())
        debug('[ Huffman.decode ]', f'bits: {bits.bin} -> msg: {decoded}')

        return decoded


class Agent:

    def __init__(self) -> None:
        self.stop_card = 51
        self.trash_card_start_idx = 32
        self.trash_cards = list(range(self.trash_card_start_idx, 51))
        self.rng = np.random.default_rng(seed=42)

        # IMPORTANT: ordering here matters since we check them linearlly
        # a subset of a less efficient one should be found sooner (ie alpha numeric last since WAR_WORDS is a more efficient subset)
        self.domain_detector = DomainDetector(
            [
                Domain.PASSWORD, Domain.COORDS, # format specific
                Domain.ADDRESS, Domain.FLIGHTS, # format specific with dictionary
                Domain.SIX_WORDS, Domain.WAR_WORDS, Domain.PLACES_AND_NAMES, # dictionary domains
                Domain.ALPHA_NUMERIC # format generic
            ]
        )

        self.domain2transformer = {
            Domain.GENERIC: WordTransformer(),
            Domain.PASSWORD: PasswordsTransformer(),
            Domain.COORDS: CoordsTransformer(),
            Domain.ADDRESS: AddressTransformer(),
            Domain.FLIGHTS: FlightsTransformer(),
            Domain.WAR_WORDS: WarWordsTransformer(),
            Domain.PLACES_AND_NAMES: PlacesAndNamesTransformer(),
            Domain.SIX_WORDS: SixWordsTransformer(),
            Domain.ALPHA_NUMERIC: AlphaNumericTransformer()
        }
 
    # TODO: there might be many _tangle_cards and _untangle_cards methods
    # such as using checksum vs using trashcards, so this should be extracted
    # as a component that could be swapped and reused.
    def _tangle_cards(self, metadata: Deck, message_metadata: Deck, message: Deck) -> Deck:
        used_cards = self.trash_cards + [self.stop_card] + metadata + message + message_metadata
        unused_message_cards = [
            card for card in range(0, 52)
            if card not in used_cards
        ]

        deck = (self.trash_cards
              + unused_message_cards
              + message_metadata
              + [self.stop_card]
              + message
              + metadata)

        return deck if valid_deck(deck) else list(range(52))

    def _untangle_cards(self, cards: Deck) -> tuple[Deck, Deck, Deck]:
        def remove_trash_cards(deck) -> List[int]:
            for i in self.trash_cards:
                deck.remove(i)
            return deck

        deck = remove_trash_cards(cards)
        stop_card = deck.index(self.stop_card)
        message_metadata, message, metadata = deck[:stop_card], deck[stop_card+1:-1], deck[-1:]

        return metadata, message_metadata, message

    def encode(self, msg: str) -> List[int]:
        # Encoding Steps
        # 1. detect the domain of the message, if none matches, fall back to
        #    using Domain.GENERIC
        # 2. based on the domain, choose a domain-specific *MessageTransformer*
        #    to compress the message string into a shorter one
        # 3. dynamically select a *Bits <-> Deck Converter* based on the
        #    shortened message, returns two decks:
        #      a) metadata deck: containing domain and BDC type
        #      b) message deck: contains the encoded message
        # 4. tangles the decks, trash cards, unused cards, stop cards into a
        #    final deck returned to the simulator

        domain = self.domain_detector.detect(msg)

        debug(f"message domain: {domain.name}")

        bits = self.domain2transformer[domain].compress(msg)

        # TODO: at this point, we already now the number of bits to encode to deck.
        # So it seems like *here* we can decide what *scheme* to use make our encoded
        # message resilient to shuffles (e.g. trash cards, checksums)
        #
        # We could create an entity to represent this scheme, and it will have the
        # following features:
        #   - select cards it need, so that we can pass to BDC to tell it not to use
        #     these cards
        #   - a tanlge() method: creates the final deck given the 3 deck returned by
        #     to_partial_deck()
        #   - an untangle() method: untangles a given deck into 3 decks
        #
        # To achieve this, we'll also have to encode this enformation in the metadata
        # deck (currently 4 bits of information, there's room for one more bit for this)
        # to be able to know untangle() from which *scheme* to use during decoding.
        # 
        # Actually, we can't. Because, we need to untangle the deck first to get the
        # metadata that we need to know which untangle to use. So it seems like we need
        # to decide a single scheme to use apriori.
        #
        # This approach has two benefits
        #   1. schemes to protect against shuffles could be used with *any* BDC
        #   2. (NO) a scheme could be *dynamically* selected at runtime, per message
        #   3. decouples the implementation of *BDC* and such against-shuffle safety
        #      *scheme* [1]
        #
        # [1]: currently, they are coupled. For example, ChunkConverter has the
        #      trash_card_start_idx hardcoded to be able to figure out what cards
        #      to use and not use, so that it's consistent with the tangle and untangle
        #      methods in the Agent class.

        # TODO: to_partial_deck (bdc) needs to communicate with _tangle_cards
        # on the cards it used. Maybe move _tangle and _untangle into bdc?
        # or modify the interface to also return cards used.
        free_cards = [card for card in range(self.trash_card_start_idx)]
        metadata_cards, message_metadata_cards, message_cards = to_partial_deck(domain, bits, free_cards)
        final_deck = self._tangle_cards(metadata_cards, message_metadata_cards, message_cards)

        return final_deck

    def decode(self, deck) -> str:
        # Decoding Steps:
        # 1. recover the deck that contains the message and metadata
        #    The metadata containing the bdc and domain is fixed size and are always at the end of the deck of message + metadata
        #    We can Use a single card to represent the metdata which is 4 bits
        #        3 bits for MessageTransformer + 1 bits for bdc
        # 2. read the metadata to recover bdc and domain
        # 3. use bdc to convert message deck -> message bits
        # 4. use domain to convert message bits -> original message string
        
        metadata, message_metadata, message = self._untangle_cards(deck)
        if len(message) == 0:
            return "NULL"

        domain, bdc = MetaCodec().decode(metadata)

        # deck -> message bits
        free_msg_cards = [card for card in range(32) if card not in metadata]
        message_bits = bdc(free_msg_cards).to_bits(message, message_metadata)
        orig_msg = self.domain2transformer[domain].uncompress(message_bits)

        return orig_msg

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

        assert type(
            encoded) == Bits, 'error: encoded message is not of type Bits!'
        assert orig == decoded, 'error: decoded message is not the same as the original'

    print('PASSED: Huffman codec using dictionary')

def test_metacodec():
    codec = MetaCodec()

    for domain, bdc in [
        (Domain.GENERIC, ChunkConverter),
        (Domain.PASSWORD, PermutationConverter)
    ]:
        deck = codec.encode(domain, bdc)
        codec.decode(deck)


if __name__ == "__main__":
    test_metacodec()
    test_huffman_codec()