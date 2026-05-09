import matplotlib.pyplot as plt
from Huffman import Huffman
from LZW import LZW
import os
from green_eggs import green_eggs
from tkinter import filedialog as fd

def create_compression_graph(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    original_size = len(text.encode('utf-8'))

    huffman_encoded, huffman_codes = Huffman.encode(text)
    huffman_size_bytes = len(huffman_encoded) / 8
    huffman_rate = (1 - huffman_size_bytes / original_size) * 100

    lzw_compressed = LZW.compress_text(text)
    lzw_size_bytes = len(lzw_compressed) * 2
    lzw_rate = (1 - lzw_size_bytes / original_size) * 100

    lzw_huffman_encoded, _ = Huffman.encode_lzw(lzw_compressed)
    lzw_huffman_size_bytes = len(lzw_huffman_encoded) / 8
    lzw_huffman_rate = (1 - lzw_huffman_size_bytes / original_size) * 100

    word_list = green_eggs.get_word_list(text)
    val, code_length = green_eggs.assign_binary(word_list)
    encoded = green_eggs.encode(text, val)
    green_eggs_size_bytes = len(encoded) / 8
    green_eggs_rate = (1 - green_eggs_size_bytes / original_size) * 100

    algorithms = ['Huffman', 'LZW', 'LZW + Huffman', 'Word Frequency']
    compression_rates = [huffman_rate, lzw_rate, lzw_huffman_rate, green_eggs_rate]
    colors = ['blue', 'green', 'red', 'purple']

    plt.figure(figsize=(12, 6))
    bars = plt.bar(algorithms, compression_rates, color=colors)
    for bar, rate in zip(bars, compression_rates):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{rate:.2f}%', ha='center', va='bottom', fontweight='bold')
    plt.xlabel('Compression Algorithm')
    plt.ylabel('Compression Rate (%)')
    plt.title(f'Compression Rates Comparison - {os.path.basename(file_path)}')
    plt.ylim(0, 100)
    plt.grid(axis='y', alpha=0.3)

    output_file = f"{os.path.splitext(file_path)[0]}_compression_graph.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')

    print(f"Huffman: {huffman_rate:.2f}%")
    print(f"LZW: {lzw_rate:.2f}%")
    print(f"LZW + Huffman: {lzw_huffman_rate:.2f}%")
    print(f"Word Frequency: {green_eggs_rate:.2f}%")

    plt.show()

if __name__ == "__main__":
    test_file = fd.askopenfilename()
    create_compression_graph(test_file)