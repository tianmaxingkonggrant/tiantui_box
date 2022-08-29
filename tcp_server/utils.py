

def crc16(list_data):
    """
    crc16 CRC-CCITT (0xFFFF)  CRC-16/CCITT-FALSE 校验
    :param list_data: 16进制字符串  ['78', '75', '6e', '6a', '69', '00', '14', '84', 'ef', '40', '82', '01', '85', '15', '3b', '01', 'aa', '55', 'eb', '67']
    :return: 16进制校验码
    """
    data = " ".join(list_data)
    data = bytearray.fromhex(data)
    offset = 0
    length = len(data)

    if data is None or offset < 0 or offset > len(data )- 1 and offset +length > len(data):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i] << 8
        for j in range(0, 8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF
