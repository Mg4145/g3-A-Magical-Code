from email.headerregistry import Address
from enum import Enum
import random
import string
import math
from collections import defaultdict
import os
import wordninja
import enchant
import hashlib

UNTOK = '*'
EMPTY = ''
DICT_SIZE = 27000
SENTENCE_LEN = 6
ENGLISH_DICTIONARY = enchant.Dict("en_US")

# g1 + g4 + g3
# g7 + g6 (1gram)
# g2
# g5
# g8

class Domain_Info():
    def __init__(self):
        '''Store all inforamtion about all domains'''
        self.domains = dict()
        self.dictionary67 = set() # share dictionary between g6 and g7
        self.dictionary14 = set() # share dictioanry between g1 and g4
        self.add_g1_domain()
        self.add_g2_domain()
        self.add_g3_domain()
        self.add_g4_domain()
        self.add_g5_domain()
        self.add_g6_domain()
        self.add_g7_domain()
        self.add_g8_domain()
    
    def add_g1_domain(self):
        '''Add a new domain to the domain info object'''
        # So far, g1 didnt provide any domain just yet, assume ascii
        domain = " 0123456789"
        domain+= "abcdefghijklmnopqrstuvwxyz"
        domain+= "."
        for c in domain:
            self.dictionary14.add(c)
        self.domains[Domain.G1] = domain
    
    def add_g2_domain(self):
        '''Add a new domain to the domain info object'''
        # AIRPORT: abbreviation, location, number
        # Char: upper case, digit, space
        #self.domains[Domain.AIRPORT] = dict()
        month = [x for x in range(1, 13)]
        day = [x for x in range(1, 29)]
        year = [x for x in range(2023, 2026)]        
        #self.domains[Domain.AIRPORT]['airport_codes'] = []
        #self.domains[Domain.AIRPORT]['time'] = []
        #self.domains[Domain.AIRPORT]['flight_number'] = []
        self.domains[Domain.AIRPORT] = []
        for y in year:
            for m in month:
                if m < 10:
                    m = '0' + str(m)
                for d in day:
                    if d < 10:
                        d = '0' + str(d)
                    time =  str(m) + str(d) + str(y)
                    self.domains[Domain.AIRPORT].append(time)
        # for i1 in (string.ascii_uppercase + string.digits):
        #     for i2 in (string.ascii_uppercase + string.digits):
        #         for i3 in (string.ascii_uppercase + string.digits):
        #             for i4 in (string.ascii_uppercase + string.digits):
        #                 self.domains[Domain.AIRPORT].append(i1+i2+i3+i4)
        with open("./messages/agent2/airportcodes.txt", "r") as f:
            line = f.readline()
            while line:
                line = line.strip()
                self.domains[Domain.AIRPORT].append(line)
                line = f.readline()

    def add_g3_domain(self):
        '''Add a new domain to the domain info object'''
        # PASSWORD: @, number/words combination
        # Char: upper/lower case, number, "@"
        self.domains[Domain.PASSWORD] = []
        with open("./messages/agent3/dicts/large_cleaned_long_words.txt", "r") as f:
            line = f.readline()
            while line:
                line = line.strip()
                self.domains[Domain.PASSWORD].append(line)
                line = f.readline()
            for i in range(1000):
                self.domains[Domain.PASSWORD].append(str(i))
            # while line:
            #     line = line.strip()
            #     prev_i = 0
            #     if line[0].isdigit():
            #         sub_str_digit = True
            #     else:
            #         sub_str_digit = False
            #     msg = []
            #     for i in range(1, len(line)):
            #         if line[i].isdigit() != sub_str_digit:
            #             if not line[prev_i:i].isdigit():
            #                 msg += wordninja.split(line[prev_i:i])
            #             prev_i = i
            #             sub_str_digit = not sub_str_digit
            #     for m in msg:  
            #         self.domains[Domain.PASSWORD].add(m)
            #     line = f.readline()
    
    def add_g4_domain(self):
        '''Add a new domain to the domain info object'''
        # Coordinate: latitude, longitude
        # Char: digit, N, E, S, W, ".", ",", space
        self.domains[Domain.LOCATION] = None
    
    def add_g5_domain(self):
        '''Add a new domain to the domain info object'''
        # Address: Number, Street suffix, streetname
        # Char: words, digit, space, ",", ".", "/"
        self.domains[Domain.ADDRESS] = []
        with open("./messages/agent5/street_name.txt", "r") as f:
            line = f.readline()
            #self.domains[Domain.ADDRESS]["street_name"] = []
            while line:
                line = line.strip()
                self.domains[Domain.ADDRESS].append(line)
                line = f.readline()
        with open("./messages/agent5/street_suffix.txt", "r") as f:
            line = f.readline()
            #self.domains[Domain.ADDRESS]["street_suffix"] = []
            while line:
                line = line.strip()
                self.domains[Domain.ADDRESS].append(line)
                line = f.readline()
        for i in range(10000):
            i = str(i)
            #self.domains[Domain.ADDRESS]["number"].append(i)
            self.domains[Domain.ADDRESS].append(i)
            while len(i) < 4:
                i = '0' + i
                #self.domains[Domain.ADDRESS]["number"].append(i)
                self.domains[Domain.ADDRESS].append(i)
                
    def add_g6_domain(self):
        '''Add a new domain to the domain info object'''
        # N-gram: 1-gram, 2-gram, ..., 9-gram
        # Char: words, digit, space
        # self.domains[Domain.NGRAM] = [dict()]
        # for i in range(1, 10):
        #     self.domains[Domain.NGRAM][i] = set()
        #     with open("./messages/agent6/corpus-ngram-" + str(i) + ".txt", "r") as f:
        #         line = f.readline()
        #         while line:
        #             line = line.strip()
        #             self.domains[Domain.NGRAM][i].add(line)
        #             if i == 1:
        #                 self.dictionary67.add(line)
        #             line = f.readline()
        # with open("./messages/agent6/unedited_corpus.txt", "r") as f:
        #     line = f.readline()
        #     self.domains[Domain.NGRAM]["unedited"] = []
        #     while line:
        #         line = line.strip()
        #         self.domains[Domain.NGRAM]["unedited"].append(line)
        #         line = f.readline()
        
        self.domains[Domain.NGRAM] = []
        with open("./messages/agent6/corpus-ngram-" + str(1) + ".txt", "r") as f:
            line = f.readline()
            while line:
                line = line.strip()
                self.domains[Domain.NGRAM].append(line)
                self.dictionary67.add(line)
                line = f.readline()
        

    def add_g7_domain(self):
        '''Add a new domain to the domain info object'''
        # Duh, this is the domain we are working on
        self.domains[Domain.DICTIONARY] = []
        with open("./messages/agent7/30k.txt", "r") as f:
            line = f.readline()
            while line:
                line = line.strip()
                if ENGLISH_DICTIONARY.check(line):
                    self.domains[Domain.DICTIONARY].append(line)
                    self.dictionary67.add(line)
                line = f.readline()
    
    def add_g8_domain(self):
        '''Add a new domain to the domain info object'''
        # Name/Places: Name, places
        # Char: upper/lower case, space
        self.domains[Domain.NAME_PLACES] = []
        with open("./messages/agent8/names.txt", "r") as f:
            line = f.readline()
            while line:
                line = line.strip()
                self.domains[Domain.NAME_PLACES].append(line)
                line = f.readline()
                
        with open("./messages/agent8/places.txt", "r") as f:
            line = f.readline()
            while line:
                line = line.strip()
                self.domains[Domain.NAME_PLACES].append(line)
                line = f.readline()
    
    def get_domain(self, domain_index):
        '''Get domain object from domain index'''
        return self.domains[domain_index]

class Domain(Enum):
    G1 = 1
    AIRPORT = 2
    PASSWORD = 3
    LOCATION = 4
    ADDRESS = 5
    NGRAM = 6
    DICTIONARY = 7
    NAME_PLACES = 8
    
def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def composed_of_words(msg, dictionary):
    """Recursively check if str is composed of words from dictionary."""
    for i in range(len(msg) + 1):
        if msg[:i].strip() in dictionary:
            if i == len(msg):
                return True
            if not composed_of_words(msg[i:].strip(), dictionary):
                continue
            else:
                return True
    return False
    
class Domain_Classifier():
    def __init__(self) -> None:
        self.domain_info = Domain_Info()

    def is_password(self, msg):
        if msg[0] != "@":
            return False
        alphabet_str = ""
        for i in msg:
            if i.isalpha():
                alphabet_str += i
        pass_dict = self.domain_info.get_domain(Domain.PASSWORD)
        # check if the string is composed of words from pass_dict
        return composed_of_words(alphabet_str, pass_dict)
    
    def is_location(self, msg):
        if len(msg.split(",")) != 2:
            return False
        msg = msg.strip()
        c1, c2 = msg.split(",")
        if (c1[-1] == "N" or c1[-1] == "S" ) and (c2[-1] == "E" or c2[-1] == "W"):
            return True
        return False

    def is_airport(self, msg):
        if len(msg.split(" ")) != 3:
            return False
        msg = msg.strip()
        msg = msg.split(" ")
        airport_code = msg[0]
        if (
            airport_code in self.domain_info.get_domain(Domain.AIRPORT)['airport_codes']
            and msg[2].isdigit()):
            return True
        return False
    
    def is_dictionary(self, msg):
        if len(msg.split()) > 6 or has_numbers(msg):
            return False
        msg = msg.strip()
        for m in msg.split():
            if m not in self.domain_info.get_domain(Domain.DICTIONARY):
                return False
        return True

    def is_ngram(self, msg):
        msg = msg.strip()
        # check for unedited corpus
        if msg in self.domain_info.get_domain(Domain.NGRAM)["unedited"]:
            return True
        # check for ngram
        msg = msg.split()
        for i in range(9, 0, -1):
            if len(msg) % i != 0:
                continue
            i_gram = self.domain_info.get_domain(Domain.NGRAM)[i]
            found_gram = True
            for j in range(0, len(msg), i):
                gram = " ".join(msg[j:j+i])
                if gram not in i_gram:
                    found_gram = False
                    break
            if found_gram:
                return True
        return False

    def is_address(self, msg):
        msg = msg.strip()
        partition = msg.split()
        if not partition[0].isdigit():
            return False
        address_dict = \
            self.domain_info.get_domain(Domain.ADDRESS)["street_name"] \
                + self.domain_info.get_domain(Domain.ADDRESS)["street_suffix"]
        return composed_of_words(" ".join(partition[1:]), address_dict)
    
    def is_name_places(self, msg):
        for x in msg.strip().split(" "):
            if x not in self.domain_info.get_domain(Domain.NAME_PLACES):
                return False
        return True
    
    # def predict(self, msg):
    #     """
    #     Classifies the message into one of the following domains:
    #     - G1 (generic/default) *
    #     - AIRPORT *
    #     - PASSWORD *
    #     - LOCATION *
    #     - ADDRESS *
    #     - NGRAM 
    #     - DICIONARY *
    #     - NAME_PLACES *
    #     """
    #     if self.is_password(msg):
    #         return Domain.PASSWORD
    #     elif self.is_location(msg):
    #         return Domain.LOCATION
    #     elif self.is_airport(msg):
    #         return Domain.AIRPORT 
    #     elif self.is_dictionary(msg):
    #         return Domain.DICTIONARY
    #     elif self.is_address(msg):
    #         return Domain.ADDRESS
    #     elif self.is_name_places(msg):
    #         return Domain.NAME_PLACES
    #     elif self.is_ngram(msg):
    #         return Domain.NGRAM
    #     return Domain.G1 # default ascii
    
    def binary_predict(self, msg):
        if self.is_dictionary(msg):
            return Domain.DICTIONARY
        return Domain.G1

CHECKSUM_CARDS = 6

class EncoderDecoder:
    def __init__(self, n):
        self.encoding_len = n
        if n < 7: #If less than 7 bits its for checksum
            self.perm_zero = [46,47,48,49,50,51]
        else:
            self.perm_zero = list(range(46-n, 46)) #[20,21,...45]
        self.max_messge_length = 12 #TODO TEST AND CHANGE THIS VALUE
        factorials = [0] * n
        for i in range(n):
            factorials[i] = math.factorial(n-i-1)
        self.factorials = factorials

        words_dict = {EMPTY: 0}
        words_index = [EMPTY]
        with open(os.path.dirname(__file__) + '/../messages/agent7/30k.txt') as f:
            for i in range(1, DICT_SIZE-1):     # reserve 1 for empty and 1 for unknown
                word = f.readline().rstrip('\t\n')
                words_dict[word] = i
                words_index.append(word)
        words_dict[UNTOK] = DICT_SIZE-1
        words_index.append(UNTOK)
        self.words_dict = words_dict
        self.words_index = words_index

    def perm_number(self, permutation):
        n = len(permutation)
        # s = sorted(permutation)
        number = 0
        for i in range(n):
            k = 0
            for j in range(i + 1, n):
                if permutation[j] < permutation[i]:
                    k += 1
            number += k * self.factorials[i]
        return number

    def nth_perm(self, n):
        perm = []
        items = self.perm_zero[:]

        for f in self.factorials:
            lehmer = n // f
            x = items.pop(lehmer)
            perm.append(x)
            n %= f
        return perm

    def str_to_perm(self, message):
        tokens = message.split()
        init = [EMPTY for i in range(SENTENCE_LEN)]
        for i in range(len(tokens)):
            init[i] = tokens[i]
        tokens = init[::-1]
        num = 0
        for i in range(SENTENCE_LEN):
            num += self.words_dict.get(tokens[i], DICT_SIZE-1) * DICT_SIZE**i
        return self.nth_perm(num)

    def str_to_num(self, message):
        tokens = message.split()
        init = [EMPTY for i in range(SENTENCE_LEN)]
        for i in range(len(tokens)):
            init[i] = tokens[i]
        tokens = init[::-1]
        num = 0
        for i in range(SENTENCE_LEN):
            num += self.words_dict.get(tokens[i], DICT_SIZE-1) * DICT_SIZE**i
        return num

    def perm_to_str(self, perm):
        num = self.perm_number(perm)
        words = []
        for i in range(SENTENCE_LEN):
            index = num % DICT_SIZE
            words.append(self.words_index[index])
            num = num // DICT_SIZE
        return ' '.join(words[::-1]).strip()

    def set_checksum(self, num, base=10):
        num_bin = bin(num)[2:]
        chunk_len = 5
        checksum = 0
        mod_prime = 113
        while len(num_bin) > 0:
            bin_chunk = num_bin[:chunk_len]
            num_bin = num_bin[chunk_len:]

            num_chunk = int(bin_chunk, 2)
            checksum = ((checksum + num_chunk) * base) % mod_prime
        return checksum


class Agent:
    def __init__(self, encoding_len=26):
        self.encoding_len = encoding_len

        self.ed = EncoderDecoder(self.encoding_len)
        self.perm_ck = EncoderDecoder(6)

    def encode(self, message):
        print('Encoding "', message, '"')
        message = ' '.join(message.split()[:6])
        x  = self.ed.str_to_num(message)
        checksum = self.ed.set_checksum(x)
        checksum_cards = self.perm_ck.nth_perm(checksum)
        a = list(range(46 - self.encoding_len))
        b = self.ed.str_to_perm(message)
        c =checksum_cards
        encoded_deck = a+b+c
        print('Encoded deck:\n', encoded_deck, '\n---------')
        return encoded_deck

    def decode(self, deck):
        msg_perm = []
        checksum = []
        for card in deck:
            if 20 <= card <= 45:
                msg_perm.append(card)
            if card > 45:
                checksum.append(card)

        #print('\nMessage Cards:', msg_perm)
        #print('Checksum Cards:', checksum)
        msg_num = self.ed.perm_number(msg_perm)

        decoded_checksum = self.perm_ck.perm_number(checksum)
        message_checksum = self.perm_ck.set_checksum(msg_num)        



def test_classifier():
    # - ASCII
    # - AIRPORT
    # - PASSWORD
    # - LOCATION
    # - ADDRESS
    # - NGRAM
    # - DICIONARY
    # - NAME_PLACES
    classifier = Domain_Classifier()
    # g7_dict = Domain_Classifier().domain_info.get_domain(Domain.DICTIONARY)
    # g6_dict = Domain_Classifier().domain_info.get_domain(Domain.NGRAM)[1]
    # overall = g6_dict.union(set(g7_dict))
    # print(len(g7_dict), len(g6_dict), len(overall))
    # msg = "@pneumatoscope9mesorrhinium5worklessness489"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "1.1714 S, 36.8356 E"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "SWF LX3M 12032025"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "the of a apple orange kills"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "5 East Main Meadow "
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "escalation encourage least kyiv ukrainian environment defeat"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "As of Monday October 31 Putin had not signed the decree required to officially end mobilization"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "2uez4cw6tc4"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    # msg = "Adwoa Abdullatif Zeona Zephyr"
    # print(f"{msg:>100} -> {classifier.predict(msg)}")
    
    for i in range(1, 9):
        with open(f"./test_classifier/g{i}_example.txt") as f:
            msg = f.readline().strip()
            while msg:
                prediction = classifier.binary_predict(msg)
                print(prediction, i)
                msg = f.readline().strip()
    return

test_classifier()
