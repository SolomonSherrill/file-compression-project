from tkinter import filedialog as fd
import os


class LZW:
    MAGIC = b"LZW1"

    @staticmethod
    def compress_text(text):
        if not text:
            print("please enter valid text\n")
            return []
        compressed_string = []
        chars_dict = {chr(i): i for i in range(256)}
        next_code = 256
        buffer_char = text[0]
        for char in text[1:]:
            if buffer_char + char in chars_dict:
                buffer_char = buffer_char + char
            else:
                compressed_string.append(chars_dict[buffer_char])
                chars_dict[buffer_char + char] = next_code
                next_code += 1
                buffer_char = char
        compressed_string.append(chars_dict[buffer_char])
        return compressed_string
    @staticmethod
    def decompress_codes(codes):
        if not codes:
            return ""
        chars_list = [chr(i) for i in range (256)]
        previous = chars_list[codes[0]]
        output = previous
        for code in codes[1:]:
            if code < len(chars_list):
                entry = chars_list[code]
            else:
                entry = previous + previous[0]
            output += entry
            chars_list.append(previous+entry[0])
            previous = entry
        return output

    @staticmethod
    def compress_bytes(data):
        if not data:
            return []
        compressed_codes = []
        bytes_dict = {bytes([i]): i for i in range(256)}
        next_code = 256
        buffer_bytes = bytes([data[0]])
        for byte in data[1:]:
            next_bytes = buffer_bytes + bytes([byte])
            if next_bytes in bytes_dict:
                buffer_bytes = next_bytes
            else:
                compressed_codes.append(bytes_dict[buffer_bytes])
                bytes_dict[next_bytes] = next_code
                next_code += 1
                buffer_bytes = bytes([byte])
        compressed_codes.append(bytes_dict[buffer_bytes])
        return compressed_codes

    @staticmethod
    def decompress_bytes(codes):
        if not codes:
            return b""
        bytes_list = [bytes([i]) for i in range(256)]
        if codes[0] >= len(bytes_list):
            raise ValueError("Invalid compressed data: first code is out of range")
        previous = bytes_list[codes[0]]
        output = bytearray(previous)
        for code in codes[1:]:
            if code < len(bytes_list):
                entry = bytes_list[code]
            elif code == len(bytes_list):
                entry = previous + previous[:1]
            else:
                raise ValueError("Invalid compressed data: code is out of range")
            output.extend(entry)
            bytes_list.append(previous + entry[:1])
            previous = entry
        return bytes(output)

    @staticmethod
    def codes_to_bytes(codes):
        return b"".join(code.to_bytes(4, byteorder="big") for code in codes)

    @staticmethod
    def bytes_to_codes(data):
        if len(data) % 4 != 0:
            raise ValueError("Invalid compressed data: byte length must be divisible by 4")
        return [int.from_bytes(data[i:i + 4], byteorder="big") for i in range(0, len(data), 4)]

    @staticmethod
    def compress_file_data(data):
        return LZW.MAGIC + LZW.codes_to_bytes(LZW.compress_bytes(data))

    @staticmethod
    def decompress_file_data(data):
        if not data.startswith(LZW.MAGIC):
            raise ValueError("Invalid compressed data: missing LZW1 header")
        return LZW.decompress_bytes(LZW.bytes_to_codes(data[len(LZW.MAGIC):]))

    @staticmethod
    def compress_file(input_path, output_path=None):
        if output_path is None:
            output_path = input_path + ".lzw"
        with open(input_path, "rb") as file:
            original_data = file.read()
        compressed_data = LZW.compress_file_data(original_data)
        with open(output_path, "wb") as file:
            file.write(compressed_data)
        return output_path

    @staticmethod
    def decompress_file(input_path, output_path):
        with open(input_path, "rb") as file:
            compressed_data = file.read()
        original_data = LZW.decompress_file_data(compressed_data)
        with open(output_path, "wb") as file:
            file.write(original_data)
        return output_path