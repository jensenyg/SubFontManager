

class UU:
    """UUEncoding编解码库，uu库只能硬盘操作，这里实现了纯内存操作"""

    @staticmethod
    def Encode(binArr: bytes) -> str:
        code_chars = []
        i = 0
        while i < len(binArr):
            chars = []
            if len(binArr) - i == 1:
                chars.append(binArr[i] >> 2)
                chars.append((binArr[i] & 0b00000011) << 4)
            elif len(binArr) - i == 2:
                chars.append(binArr[i] >> 2)
                chars.append(((binArr[i] & 0b00000011) << 4) | (binArr[i + 1] >> 4))
                chars.append((binArr[i + 1] & 0b00001111) << 2)
            else:
                chars.append(binArr[i] >> 2)
                chars.append(((binArr[i] & 0b00000011) << 4) | binArr[i + 1] >> 4)
                chars.append(((binArr[i + 1] & 0b00001111) << 2) | (binArr[i + 2] >> 6))
                chars.append(binArr[i + 2] & 0b00111111)
            i += 3
            code_chars.extend(chr(c + 33) for c in chars)
        return ''.join(code_chars)

    @staticmethod
    def Decode(codeStr: str) -> bytes:
        bin_arr = bytearray()
        code_num = [ord(c) - 33 for c in codeStr]
        i = 0
        while i < len(code_num):
            if len(codeStr) - i == 2:
                bin_arr.append((code_num[i] << 2) | code_num[i + 1] >> 4)
            elif len(codeStr) - i == 3:
                bin_arr.append((code_num[i] << 2) | code_num[i + 1] >> 4)
                bin_arr.append(((code_num[i + 1] & 0b00001111) << 4) | (code_num[i + 2] >> 2))
            else:
                bin_arr.append((code_num[i] << 2) | code_num[i + 1] >> 4)
                bin_arr.append(((code_num[i + 1] & 0b00001111) << 4) | (code_num[i + 2] >> 2))
                bin_arr.append((code_num[i + 2] & 0b00000011) << 6 | code_num[i + 3])
            i += 4
        return bin_arr
