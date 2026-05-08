(function (global) {
  "use strict";

  const MAGIC = new Uint8Array([0x4c, 0x5a, 0x57, 0x00]);
  const FORMAT_VARIABLE_WIDTH = 0x02;
  const MAX_DICTIONARY_SIZE = 65536;
  const MIN_CODE_WIDTH = 9;
  const MAX_CODE_WIDTH = 16;
  const CLEAR_CODE = 256;
  const END_CODE = 257;
  const FIRST_DICTIONARY_CODE = 258;
  const CODE_CHUNK_COUNT = 65536;

  function isByteArray(value) {
    return Boolean(
      value &&
        value.BYTES_PER_ELEMENT === 1 &&
        typeof value.length === "number" &&
        typeof value.subarray === "function",
    );
  }

  function bytesToBinaryString(bytes) {
    let output = "";
    const chunkSize = 0x8000;
    for (let i = 0; i < bytes.length; i += chunkSize) {
      output += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
    }
    return output;
  }

  function binaryStringToBytes(text) {
    const bytes = new Uint8Array(text.length);
    for (let i = 0; i < text.length; i += 1) {
      bytes[i] = text.charCodeAt(i) & 0xff;
    }
    return bytes;
  }

  function compressBytes(bytes) {
    if (!isByteArray(bytes)) {
      throw new TypeError("compressBytes expects a Uint8Array");
    }
    if (bytes.length === 0) {
      return [];
    }

    const dictionary = new Map();
    for (let i = 0; i < 256; i += 1) {
      dictionary.set(String.fromCharCode(i), i);
    }

    const codes = [];
    let nextCode = 256;
    let buffer = String.fromCharCode(bytes[0]);

    for (let i = 1; i < bytes.length; i += 1) {
      const char = String.fromCharCode(bytes[i]);
      const candidate = buffer + char;

      if (dictionary.has(candidate)) {
        buffer = candidate;
      } else {
        codes.push(dictionary.get(buffer));
        if (nextCode < MAX_DICTIONARY_SIZE) {
          dictionary.set(candidate, nextCode);
          nextCode += 1;
        }
        buffer = char;
      }
    }

    codes.push(dictionary.get(buffer));
    return codes;
  }

  function createCodeWriter() {
    let buffer = new Uint8Array(CODE_CHUNK_COUNT * 4);
    let view = new DataView(buffer.buffer);
    let offset = 0;

    const parts = [MAGIC];
    let size = MAGIC.length;
    let codeCount = 0;

    function flush() {
      if (offset === 0) {
        return;
      }
      parts.push(buffer.slice(0, offset));
      size += offset;
      buffer = new Uint8Array(CODE_CHUNK_COUNT * 4);
      view = new DataView(buffer.buffer);
      offset = 0;
    }

    return {
      write(code) {
        if (!Number.isInteger(code) || code < 0 || code > 0xffffffff) {
          throw new Error("Invalid compressed data: code must fit in 4 bytes");
        }
        if (offset === buffer.length) {
          flush();
        }
        view.setUint32(offset, code, false);
        offset += 4;
        codeCount += 1;
      },
      finish() {
        flush();
        return { parts, size, codeCount };
      },
    };
  }

  function createBitWriter() {
    let buffer = new Uint8Array(CODE_CHUNK_COUNT);
    let offset = 0;
    let bitBuffer = 0;
    let bitCount = 0;

    const parts = [MAGIC, new Uint8Array([FORMAT_VARIABLE_WIDTH])];
    let size = MAGIC.length + 1;
    let codeCount = 0;

    function writeByte(byte) {
      if (offset === buffer.length) {
        flush();
      }
      buffer[offset] = byte;
      offset += 1;
      size += 1;
    }

    function flush() {
      if (offset === 0) {
        return;
      }
      parts.push(buffer.slice(0, offset));
      buffer = new Uint8Array(CODE_CHUNK_COUNT);
      offset = 0;
    }

    return {
      write(code, width) {
        if (!Number.isInteger(code) || code < 0 || code >= 2 ** width) {
          throw new Error("Invalid compressed data: code does not fit current width");
        }

        bitBuffer = (bitBuffer << width) | code;
        bitCount += width;
        codeCount += 1;

        while (bitCount >= 8) {
          const shift = bitCount - 8;
          writeByte((bitBuffer >> shift) & 0xff);
          bitCount -= 8;
          bitBuffer &= bitCount === 0 ? 0 : (1 << bitCount) - 1;
        }
      },
      finish() {
        if (bitCount > 0) {
          writeByte((bitBuffer << (8 - bitCount)) & 0xff);
          bitBuffer = 0;
          bitCount = 0;
        }
        flush();
        return { parts, size, codeCount };
      },
    };
  }

  function createBitReader(bytes) {
    let offset = 0;
    let bitBuffer = 0;
    let bitCount = 0;

    return {
      read(width) {
        while (bitCount < width) {
          if (offset >= bytes.length) {
            throw new Error("Invalid compressed data: missing end code");
          }
          bitBuffer = (bitBuffer << 8) | bytes[offset];
          bitCount += 8;
          offset += 1;
        }

        const shift = bitCount - width;
        const code = (bitBuffer >> shift) & ((1 << width) - 1);
        bitCount -= width;
        bitBuffer &= bitCount === 0 ? 0 : (1 << bitCount) - 1;
        return code;
      },
    };
  }

  function createInitialDictionary() {
    const dictionary = new Map();
    for (let i = 0; i < 256; i += 1) {
      dictionary.set(String.fromCharCode(i), i);
    }
    return dictionary;
  }

  function createInitialDecodeDictionary() {
    const dictionary = [];
    for (let i = 0; i < 256; i += 1) {
      dictionary[i] = String.fromCharCode(i);
    }
    return dictionary;
  }

  function compressFileDataParts(bytes) {
    if (!isByteArray(bytes)) {
      throw new TypeError("compressFileDataParts expects a Uint8Array");
    }

    const writer = createBitWriter();
    let dictionary = createInitialDictionary();
    let nextCode = FIRST_DICTIONARY_CODE;
    let width = MIN_CODE_WIDTH;

    if (bytes.length === 0) {
      writer.write(END_CODE, width);
      return writer.finish();
    }

    let buffer = String.fromCharCode(bytes[0]);

    for (let i = 1; i < bytes.length; i += 1) {
      const char = String.fromCharCode(bytes[i]);
      const candidate = buffer + char;

      if (dictionary.has(candidate)) {
        buffer = candidate;
      } else {
        writer.write(dictionary.get(buffer), width);

        if (nextCode < MAX_DICTIONARY_SIZE) {
          dictionary.set(candidate, nextCode);
          nextCode += 1;
          if (nextCode === 2 ** width && width < MAX_CODE_WIDTH) {
            width += 1;
          }
        } else {
          writer.write(CLEAR_CODE, width);
          dictionary = createInitialDictionary();
          nextCode = FIRST_DICTIONARY_CODE;
          width = MIN_CODE_WIDTH;
        }

        buffer = char;
      }
    }

    writer.write(dictionary.get(buffer), width);
    writer.write(END_CODE, width);
    return writer.finish();
  }

  function decompressCodes(codes) {
    if (!Array.isArray(codes)) {
      throw new TypeError("decompressCodes expects an array of numbers");
    }
    if (codes.length === 0) {
      return new Uint8Array();
    }

    const dictionary = [];
    for (let i = 0; i < 256; i += 1) {
      dictionary[i] = String.fromCharCode(i);
    }

    const firstCode = codes[0];
    if (firstCode < 0 || firstCode >= dictionary.length) {
      throw new Error("Invalid compressed data: first code is out of range");
    }

    let previous = dictionary[firstCode];
    const output = [previous];

    for (let i = 1; i < codes.length; i += 1) {
      const code = codes[i];
      let entry;

      if (code < dictionary.length) {
        entry = dictionary[code];
      } else if (code === dictionary.length) {
        entry = previous + previous[0];
      } else {
        throw new Error("Invalid compressed data: code is out of range");
      }

      output.push(entry);
      if (dictionary.length < MAX_DICTIONARY_SIZE) {
        dictionary.push(previous + entry[0]);
      }
      previous = entry;
    }

    return binaryStringToBytes(output.join(""));
  }

  function decompressVariableWidthData(bytes) {
    const reader = createBitReader(bytes);
    let dictionary = createInitialDecodeDictionary();
    let nextCode = FIRST_DICTIONARY_CODE;
    let width = MIN_CODE_WIDTH;
    let previous = null;
    const output = [];

    while (true) {
      const code = reader.read(width);

      if (code === END_CODE) {
        break;
      }

      if (code === CLEAR_CODE) {
        dictionary = createInitialDecodeDictionary();
        nextCode = FIRST_DICTIONARY_CODE;
        width = MIN_CODE_WIDTH;
        previous = null;
        continue;
      }

      let entry;
      if (code < dictionary.length && dictionary[code] !== undefined) {
        entry = dictionary[code];
      } else if (previous !== null && code === nextCode) {
        entry = previous + previous[0];
      } else {
        throw new Error("Invalid compressed data: code is out of range");
      }

      output.push(entry);

      if (previous !== null && nextCode < MAX_DICTIONARY_SIZE) {
        dictionary[nextCode] = previous + entry[0];
        nextCode += 1;
        if (nextCode + 1 === 2 ** width && width < MAX_CODE_WIDTH) {
          width += 1;
        }
      }

      previous = entry;
    }

    return binaryStringToBytes(output.join(""));
  }

  function codesToBytes(codes) {
    const bytes = new Uint8Array(codes.length * 4);
    const view = new DataView(bytes.buffer);

    for (let i = 0; i < codes.length; i += 1) {
      const code = codes[i];
      if (!Number.isInteger(code) || code < 0 || code > 0xffffffff) {
        throw new Error("Invalid compressed data: code must fit in 4 bytes");
      }
      view.setUint32(i * 4, code, false);
    }

    return bytes;
  }

  function bytesToCodes(bytes) {
    if (bytes.length % 4 !== 0) {
      throw new Error("Invalid compressed data: byte length must be divisible by 4");
    }

    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const codes = [];
    for (let i = 0; i < bytes.length; i += 4) {
      codes.push(view.getUint32(i, false));
    }
    return codes;
  }

  function hasMagic(bytes) {
    if (bytes.length < MAGIC.length) {
      return false;
    }
    for (let i = 0; i < MAGIC.length; i += 1) {
      if (bytes[i] !== MAGIC[i]) {
        return false;
      }
    }
    return true;
  }

  function withMagic(payload) {
    const fileBytes = new Uint8Array(MAGIC.length + payload.length);
    fileBytes.set(MAGIC, 0);
    fileBytes.set(payload, MAGIC.length);
    return fileBytes;
  }

  function compressFileData(bytes) {
    const compressed = compressFileDataParts(bytes);
    const fileBytes = new Uint8Array(compressed.size);
    let offset = 0;
    for (const part of compressed.parts) {
      fileBytes.set(part, offset);
      offset += part.length;
    }
    return fileBytes;
  }

  function decompressFileData(bytes) {
    if (!isByteArray(bytes)) {
      throw new TypeError("decompressFileData expects a Uint8Array");
    }
    if (!hasMagic(bytes)) {
      throw new Error("Invalid .lzw file: missing LZW\\x00 header");
    }

    const body = bytes.subarray(MAGIC.length);
    if (body.length === 0) {
      return decompressCodes([]);
    }
    if (body[0] === FORMAT_VARIABLE_WIDTH) {
      return decompressVariableWidthData(body.subarray(1));
    }
    return decompressCodes(bytesToCodes(body));
  }

  global.LZWCodec = {
    MAGIC,
    FORMAT_VARIABLE_WIDTH,
    MAX_DICTIONARY_SIZE,
    MIN_CODE_WIDTH,
    MAX_CODE_WIDTH,
    CLEAR_CODE,
    END_CODE,
    CODE_CHUNK_COUNT,
    compressBytes,
    decompressCodes,
    codesToBytes,
    bytesToCodes,
    compressFileData,
    compressFileDataParts,
    decompressFileData,
    hasMagic,
  };
})(window);
