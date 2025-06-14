"""
Cython版的UUEncoding编解码库，uu库只能硬盘操作，这里实现了纯内存操作
"""

from libc.stdlib cimport malloc, free


cpdef Encode(binArr: bytes | bytearray):
    """UUEncoding编码，输入bytes返回str"""
    length = len(binArr)
    cdef unsigned char* buffer = <unsigned char*>malloc(<int>(length * 4 / 3 + 2))
    _encode(<const unsigned char*>binArr, length, buffer)
    code: str = buffer.decode('ascii')   # 转换为Python str，因为合法的编码只包含英文和符号，所以可以用ascii编码
    free(buffer)
    return code

cpdef Decode(codeStr: str):
    """UUEncoding解码，输入str返回bytes"""
    cdef unsigned char* buffer = <unsigned char*> malloc(<int>(len(codeStr) * 3 / 4 + 1))
    _bytes = codeStr.encode('ascii')
    bin_length = _decode(<const unsigned char*>_bytes, len(_bytes), buffer)
    binArr: bytes = buffer[:bin_length]    # 转换为Python bytes
    free(buffer)
    return binArr


cdef _encode(const unsigned char* binArr, Py_ssize_t length, unsigned char* buffer):
    """
    对传入二进制串进行UUEncoding编码，结果（字符串）写入到buffer，结尾写入\0
    :param binArr: 需要编码的二进制值数组
    :param length: binArr的长度
    :param buffer: 编码结果（字符串）的写入缓存，长度需要至少是binArr长度的4/3+1
    :return: 实际写入buffer的长度
    """
    cdef int i = 0, j = 0, k = 0
    while i < length:
        buffer[j] = binArr[i] >> 2
        if length - i == 1:
            buffer[j + 1] = (binArr[i] & 0b00000011) << 4
            j += 2
        elif length - i == 2:
            buffer[j + 1] = ((binArr[i] & 0b00000011) << 4) | (binArr[i + 1] >> 4)
            buffer[j + 2] = (binArr[i + 1] & 0b00001111) << 2
            j += 3
        else:
            buffer[j + 1] = ((binArr[i] & 0b00000011) << 4) | binArr[i + 1] >> 4
            buffer[j + 2] = ((binArr[i + 1] & 0b00001111) << 2) | (binArr[i + 2] >> 6)
            buffer[j + 3] = binArr[i + 2] & 0b00111111
            j += 4
        i += 3

    while k < j:
        buffer[k] += 33
        k += 1

    buffer[k] = '\0'
    return k


cdef _decode(const unsigned char* chars, Py_ssize_t length, unsigned char* buffer):
    """
    对传入字符串进行UUEncoding解码，结果（二进制串）写入到buffer
    :param chars: 需要解码的字符串
    :param length: chars的长度
    :param buffer: 解码结果（二进制串）的写入缓存，长度需要至少是binArr长度的3/4
    :return: 实际写入buffer的长度
    """
    cdef int i = 0, k = 0
    cdef unsigned char char_0, char_1, char_2, char_3
    while i < length:   # 注意：合法的UUEncoding字串在最后一小节只可能有2、3、4字节，不可能只有1字节
        char_0 = chars[i] - 33
        char_1 = chars[i + 1] - 33
        buffer[k] = (char_0 << 2) | char_1 >> 4
        k += 1
        if length - i > 2:
            char_2 = chars[i + 2] - 33
            buffer[k] = ((char_1 & 0b00001111) << 4) | (char_2 >> 2)
            k += 1
        if length - i > 3:
            char_3 = chars[i + 3] - 33
            buffer[k] = (char_2 & 0b00000011) << 6 | char_3
            k += 1
        i += 4
    return k
