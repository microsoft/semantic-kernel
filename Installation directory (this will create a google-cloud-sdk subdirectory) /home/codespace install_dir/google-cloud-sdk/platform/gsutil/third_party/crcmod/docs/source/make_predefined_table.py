
from __future__ import print_function

import numbers

import crcmod.predefined

table_data = [
    [   "Name",            'name',     32,    ],
    [   "Polynomial",      'poly',     22,    ],
    [   "Reversed?",       'reverse',  10,    ],
    [   "Init-value",      'init',     20,    ],
    [   "XOR-out",         'xor_out',  20,    ],
    [   "Check",           'check',    20,    ],
]

ccitt_defns = [
    'kermit',
    'crc-ccitt-false',
    'crc-aug-ccitt',
]

column_dashes = '  '.join(('=' * table_data_item[2] for table_data_item in table_data))
print(column_dashes)
print('  '.join(("%-*s" % (table_data_item[2], table_data_item[0]) for table_data_item in table_data)).strip())
print(column_dashes)

for defn in crcmod.predefined._crc_definitions:
    poly_width = crcmod.crcmod._verifyPoly(defn['poly'])
    hex_width = (poly_width + 3) // 4
    defn_data_list = []
    for (header_text, key, width) in table_data:
        if isinstance(defn[key], bool):
            item = "%s" % (defn[key],)
        elif isinstance(defn[key], numbers.Integral):
            item = "0x%0*X" % (hex_width, defn[key])
        else:
            item = "``%s``" % (defn[key])
            if defn['name'] in ccitt_defns:
                item = ' '.join([item, '[#ccitt]_'])
        item = "%-*s" % (width, item)
        defn_data_list.append(item)
    print('  '.join(defn_data_list).strip())

print(column_dashes)
