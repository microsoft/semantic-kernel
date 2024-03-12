#-----------------------------------------------------------------------------
# Demonstrate the use of the code generator
from crcmod import Crc

g8 = 0x185
g16 = 0x11021
g24 = 0x15D6DCB
g32 = 0x104C11DB7

def polyFromBits(bits):
    p = 0
    for n in bits:
        p = p | (1 << n)
    return p

# The following is from Standard ECMA-182 "Data Interchange on 12,7 mm 48-Track
# Magnetic Tape Cartridges -DLT1 Format-", December 1992.

g64 = polyFromBits([64, 62, 57, 55, 54, 53, 52, 47, 46, 45, 40, 39, 38, 37,
            35, 33, 32, 31, 29, 27, 24, 23, 22, 21, 19, 17, 13, 12, 10, 9, 7,
            4, 1, 0])

print('Generating examples.c')
out = open('examples.c', 'w')
out.write('''// Define the required data types
typedef unsigned char      UINT8;
typedef unsigned short     UINT16;
typedef unsigned int       UINT32;
typedef unsigned long long UINT64;
''')
Crc(g8, rev=False).generateCode('crc8',out)
Crc(g8, rev=True).generateCode('crc8r',out)
Crc(g16, rev=False).generateCode('crc16',out)
Crc(g16, rev=True).generateCode('crc16r',out)
Crc(g24, rev=False).generateCode('crc24',out)
Crc(g24, rev=True).generateCode('crc24r',out)
Crc(g32, rev=False).generateCode('crc32',out)
Crc(g32, rev=True).generateCode('crc32r',out)
Crc(g64, rev=False).generateCode('crc64',out)
Crc(g64, rev=True).generateCode('crc64r',out)

# Check out the XOR-out feature.
Crc(g16, initCrc=0, rev=True, xorOut=~0).generateCode('crc16x',out)
Crc(g24, initCrc=0, rev=True, xorOut=~0).generateCode('crc24x',out)
Crc(g32, initCrc=0, rev=True, xorOut=~0).generateCode('crc32x',out)
Crc(g64, initCrc=0, rev=True, xorOut=~0).generateCode('crc64x',out)

out.close()
print('Done')
