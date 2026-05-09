from tkinter import filedialog as fd
import math
import json
class word_string:
    def __init__(self):
        self.text = None
        self.frequency = 0
    def update_frequency(self,num):
        self.frequency += num
class word_list:
    def __init__(self):
        self.list = []
    def add_string(self,string):
        self.list.append(string)
class green_eggs:
    @staticmethod
    def get_word_list(text):
        lines = text.splitlines()
        words = {}
        for line in lines:
            num_spaces = len(line.split()) - 1
            if "spaces" not in words:
                words["spaces"] = word_string()
                words["spaces"].text = "spaces"
            words["spaces"].update_frequency(num_spaces)
            if "newlines" not in words:
                words["newlines"] = word_string()
                words["newlines"].text = "newlines"
            words["newlines"].update_frequency(1)
            for word in line.split():
                if word not in words:
                    words[word] = word_string()
                    words[word].text = word
                words[word].update_frequency(1)
        wl = word_list()
        for w in sorted(words.values(), key=lambda x: x.frequency, reverse=True):
            wl.add_string(w)
        return wl
    @staticmethod
    def assign_binary(wordlist):
        num_words = len(wordlist.list)
        code_length = math.ceil(math.log2(num_words))
        val = {word.text: bin(i)[2:].zfill(code_length) for i, word in enumerate(wordlist.list)}
        return val, code_length
    @staticmethod
    def encode(text,val):
        encoded = ""
        lines = text.splitlines()
        for line in lines:
            for i, word in enumerate(line.split()):
                encoded += val[word]
                if i < len(line.split()) - 1:
                    encoded += val["spaces"]
            encoded += val["newlines"]
        return encoded
    @staticmethod
    def write_binary(encoded, filename):
        padding = (8 - len(encoded) % 8) % 8
        encoded += '0' * padding
        byte_array = bytearray()
        for i in range(0, len(encoded), 8):
            chunk = encoded[i:i+8]
            byte_array.append(int(chunk, 2))
        with open(filename + ".bin", 'wb') as f:
            f.write(bytes([padding]))
            f.write(byte_array)
    @staticmethod
    def write_codebook(val, code_length, padding, filename):
        codebook = {
            "code_length": code_length,
            "padding": padding,
            "codes": val
        }
        with open(filename + ".json", 'w') as f:
            json.dump(codebook, f)
    @staticmethod
    def master_encode(filename):
        with open(filename, 'r') as file:
            text = file.read()
        output = filename.replace('.txt', '_compressed')
        word_list = green_eggs.get_word_list(text)
        val, length = green_eggs.assign_binary(word_list)
        encoded = green_eggs.encode(text,val)
        padding = (8 - len(encoded) % 8) % 8
        green_eggs.write_binary(encoded, output)
        green_eggs.write_codebook(val,length,padding,output)
    @staticmethod
    def read_binary(filename):
        with open(filename, 'rb') as f:
            padding = f.read(1)[0]
            data = f.read()
        bits = ''.join(bin(byte)[2:].zfill(8) for byte in data)
        return bits[:-padding] if padding else bits
    @staticmethod
    def load_codebook(filename):
        with open(filename + ".json", 'r') as f:
            codebook = json.load(f)
        code_length = codebook["code_length"]
        padding = codebook["padding"]
        reverse_codes = {v: k for k, v in codebook["codes"].items()}
        return reverse_codes, code_length, padding
    @staticmethod
    def decode(bits, reverse_codes, code_length):
        tokens = []
        for i in range(0, len(bits), code_length):
            chunk = bits[i:i + code_length]
            tokens.append(reverse_codes[chunk])
        return tokens
    @staticmethod
    def to_text(tokens):
        output = ""
        for token in tokens:
            if token == "newlines":
                output += "\n"
            elif token == "spaces":
                output += " "
            else:
                output += token
        return output
    @staticmethod
    def master_decode(binname = None):
        if not binname:
            binname = fd.askopenfilename()
        jsonname = binname.replace('.bin','')
        bintext = green_eggs.read_binary(binname)
        reverse_codes, code_length, padding = green_eggs.load_codebook(jsonname)
        tokens = green_eggs.decode(bintext, reverse_codes, code_length)
        text = green_eggs.to_text(tokens)
        with open(binname.replace('_compressed.bin','_uncompressed.txt'),'w') as file:
            file.write(text)