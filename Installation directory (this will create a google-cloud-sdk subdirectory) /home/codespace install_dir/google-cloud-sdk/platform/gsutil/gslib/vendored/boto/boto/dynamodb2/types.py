# Shadow the DynamoDB v1 bits.
# This way, no end user should have to cross-import between versions & we
# reserve the namespace to extend v2 if it's ever needed.
from boto.dynamodb.types import NonBooleanDynamizer, Dynamizer


# Some constants for our use.
STRING = 'S'
NUMBER = 'N'
BINARY = 'B'
STRING_SET = 'SS'
NUMBER_SET = 'NS'
BINARY_SET = 'BS'
NULL = 'NULL'
BOOLEAN = 'BOOL'
MAP = 'M'
LIST = 'L'

QUERY_OPERATORS = {
    'eq': 'EQ',
    'lte': 'LE',
    'lt': 'LT',
    'gte': 'GE',
    'gt': 'GT',
    'beginswith': 'BEGINS_WITH',
    'between': 'BETWEEN',
}

FILTER_OPERATORS = {
    'eq': 'EQ',
    'ne': 'NE',
    'lte': 'LE',
    'lt': 'LT',
    'gte': 'GE',
    'gt': 'GT',
    # FIXME: Is this necessary? i.e. ``whatever__null=False``
    'nnull': 'NOT_NULL',
    'null': 'NULL',
    'contains': 'CONTAINS',
    'ncontains': 'NOT_CONTAINS',
    'beginswith': 'BEGINS_WITH',
    'in': 'IN',
    'between': 'BETWEEN',
}
