# coding: utf-8
#
# This file is part of pyasn1-modules software.
#
# Created by Joel Johnson with asn1ate tool.
# Copyright (c) 2005-2018, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/pyasn1/license.html
#
# PKCS #10: Certification Request Syntax Specification
#
# ASN.1 source from:
# http://www.ietf.org/rfc/rfc2986.txt
#
from pyasn1.type import univ
from pyasn1.type import char
from pyasn1.type import namedtype
from pyasn1.type import namedval
from pyasn1.type import opentype
from pyasn1.type import tag
from pyasn1.type import constraint
from pyasn1.type import useful

MAX = float('inf')


class AttributeType(univ.ObjectIdentifier):
    pass


class AttributeValue(univ.Any):
    pass


certificateAttributesMap = {}


class AttributeTypeAndValue(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('type', AttributeType()),
        namedtype.NamedType(
            'value', AttributeValue(),
            openType=opentype.OpenType('type', certificateAttributesMap)
        )
    )


class Attribute(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('type', AttributeType()),
        namedtype.NamedType('values',
                            univ.SetOf(componentType=AttributeValue()),
                            openType=opentype.OpenType('type', certificateAttributesMap))
    )


class Attributes(univ.SetOf):
    pass


Attributes.componentType = Attribute()


class RelativeDistinguishedName(univ.SetOf):
    pass


RelativeDistinguishedName.componentType = AttributeTypeAndValue()
RelativeDistinguishedName.subtypeSpec = constraint.ValueSizeConstraint(1, MAX)


class RDNSequence(univ.SequenceOf):
    pass


RDNSequence.componentType = RelativeDistinguishedName()


class Name(univ.Choice):
    pass


Name.componentType = namedtype.NamedTypes(
    namedtype.NamedType('rdnSequence', RDNSequence())
)


class AlgorithmIdentifier(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('algorithm', univ.ObjectIdentifier()),
        namedtype.OptionalNamedType('parameters', univ.Any())
    )


class SubjectPublicKeyInfo(univ.Sequence):
    pass


SubjectPublicKeyInfo.componentType = namedtype.NamedTypes(
    namedtype.NamedType('algorithm', AlgorithmIdentifier()),
    namedtype.NamedType('subjectPublicKey', univ.BitString())
)


class CertificationRequestInfo(univ.Sequence):
    pass


CertificationRequestInfo.componentType = namedtype.NamedTypes(
    namedtype.NamedType('version', univ.Integer()),
    namedtype.NamedType('subject', Name()),
    namedtype.NamedType('subjectPKInfo', SubjectPublicKeyInfo()),
    namedtype.NamedType('attributes', Attributes().subtype(implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 0)))
)


class CertificationRequest(univ.Sequence):
    pass


CertificationRequest.componentType = namedtype.NamedTypes(
    namedtype.NamedType('certificationRequestInfo', CertificationRequestInfo()),
    namedtype.NamedType('signatureAlgorithm', AlgorithmIdentifier()),
    namedtype.NamedType('signature', univ.BitString())
)
