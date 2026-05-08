from collections import Counter
import heapq
import LZW
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq
class Huffman:
    @staticmethod
    def encode(text):
        if not text:
            return "", {}
        charcount = Counter(text)
        heap = [Node(char, freq) for char, freq in charcount.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            parent = Node(None, left.freq + right.freq)
            parent.left = left
            parent.right = right
            heapq.heappush(heap, parent)
        root = heap[0]
        codes = {}
        def assign_codes(node, current_code):
            if node is None:
                return
            if node.char is not None:
                codes[node.char] = current_code or "0"
                return
            assign_codes(node.left, current_code + "0")
            assign_codes(node.right, current_code + "1")
        assign_codes(root, "")
        encoded = "".join(codes[char] for char in text)
        return encoded, codes

    @staticmethod
    def decode(encoded, codes):
        if not encoded:
            return ""
        if not codes:
            raise ValueError("Invalid Huffman data: codes are required")
        reverse_codes = {code: char for char, code in codes.items()}
        decoded = []
        current_code = ""
        for bit in encoded:
            if bit not in "01":
                raise ValueError("Invalid Huffman data: encoded text must contain only 0 and 1")
            current_code += bit
            if current_code in reverse_codes:
                decoded.append(reverse_codes[current_code])
                current_code = ""
        if current_code:
            raise ValueError("Invalid Huffman data: encoded bits ended mid-code")
        return "".join(decoded)

    @staticmethod
    def bits_to_bytes(bits):
        if any(bit not in "01" for bit in bits):
            raise ValueError("Invalid Huffman data: bits must contain only 0 and 1")
        bit_length = len(bits)
        padding = (-bit_length) % 8
        padded_bits = bits + ("0" * padding)
        encoded_bytes = bytearray()
        encoded_bytes.extend(bit_length.to_bytes(4, byteorder="big"))
        for i in range(0, len(padded_bits), 8):
            encoded_bytes.append(int(padded_bits[i:i + 8], 2))
        return bytes(encoded_bytes)

    @staticmethod
    def bytes_to_bits(data):
        if len(data) < 4:
            raise ValueError("Invalid Huffman data: missing bit length header")
        bit_length = int.from_bytes(data[:4], byteorder="big")
        available_bits = (len(data) - 4) * 8
        if bit_length > available_bits:
            raise ValueError("Invalid Huffman data: bit length exceeds available data")
        bits = "".join(f"{byte:08b}" for byte in data[4:])
        return bits[:bit_length]

    @staticmethod
    def encode_lzw(codes):
        if not codes:
            return "", {}
        charcount = Counter(codes)
        heap = [Node(char, freq) for char, freq in charcount.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            parent = Node(None, left.freq + right.freq)
            parent.left = left
            parent.right = right
            heapq.heappush(heap, parent)
        root = heap[0]
        huffman_codes = {}
        def assign_codes(node, current_code):
            if node is None:
                return
            if node.char is not None:
                huffman_codes[node.char] = current_code or "0"
                return
            assign_codes(node.left, current_code + "0")
            assign_codes(node.right, current_code + "1")
        assign_codes(root, "")
        encoded = "".join(huffman_codes[code] for code in codes)
        return encoded, huffman_codes

    @staticmethod
    def decode_lzw(encoded, codes):
        if not encoded:
            return []
        if not codes:
            raise ValueError("Invalid Huffman data: codes are required")
        reverse_codes = {code: value for value, code in codes.items()}
        decoded = []
        current_code = ""
        for bit in encoded:
            if bit not in "01":
                raise ValueError("Invalid Huffman data: encoded text must contain only 0 and 1")
            current_code += bit
            if current_code in reverse_codes:
                decoded.append(reverse_codes[current_code])
                current_code = ""
        if current_code:
            raise ValueError("Invalid Huffman data: encoded bits ended mid-code")
        return decoded