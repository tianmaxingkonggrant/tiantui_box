def crc16(list_data):
    data = " ".join(list_data)
    data = bytearray.fromhex(data)
    offset = 0
    length = len(data)

    if data is None or offset < 0 or offset > len(data) - 1 and offset + length > len(data):
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


def main():
    data = '00 39 84 ef 40 82 01 85 04 15 04 01 1c 5a 9b 20 00 87 ff b6 05 1c 21 10 53 96 4a 34 1c 01 55 01 03 64 05 2e 4d b1 64 05 2e 4e ae 64 05 2e 4c ae c7 ff'.split()
    modified_data = crc16(data)
    print("CRC16: ", hex(modified_data))


if __name__ == "__main__":
    main()
