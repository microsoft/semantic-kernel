#!/usr/bin/env python
from os.path import basename, splitext
from typing import BinaryIO, List, Optional, Set

try:
    from os import PathLike
except ImportError:  # pragma: no cover
    PathLike = str  # type: ignore

import logging

from .cd import (
    coherence_ratio,
    encoding_languages,
    mb_encoding_languages,
    merge_coherence_ratios,
)
from .constant import IANA_SUPPORTED, TOO_BIG_SEQUENCE, TOO_SMALL_SEQUENCE
from .md import mess_ratio
from .models import CharsetMatch, CharsetMatches
from .utils import (
    any_specified_encoding,
    iana_name,
    identify_sig_or_bom,
    is_cp_similar,
    is_multi_byte_encoding,
    should_strip_sig_or_bom,
)

logger = logging.getLogger("charset_normalizer")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)


def from_bytes(
    sequences: bytes,
    steps: int = 5,
    chunk_size: int = 512,
    threshold: float = 0.2,
    cp_isolation: List[str] = None,
    cp_exclusion: List[str] = None,
    preemptive_behaviour: bool = True,
    explain: bool = False,
) -> CharsetMatches:
    """
    Given a raw bytes sequence, return the best possibles charset usable to render str objects.
    If there is no results, it is a strong indicator that the source is binary/not text.
    By default, the process will extract 5 blocs of 512o each to assess the mess and coherence of a given sequence.
    And will give up a particular code page after 20% of measured mess. Those criteria are customizable at will.

    The preemptive behavior DOES NOT replace the traditional detection workflow, it prioritize a particular code page
    but never take it for granted. Can improve the performance.

    You may want to focus your attention to some code page or/and not others, use cp_isolation and cp_exclusion for that
    purpose.

    This function will strip the SIG in the payload/sequence every time except on UTF-16, UTF-32.
    """

    if not isinstance(sequences, (bytearray, bytes)):
        raise TypeError(
            "Expected object of type bytes or bytearray, got: {0}".format(
                type(sequences)
            )
        )

    if not explain:
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.INFO)

    length = len(sequences)  # type: int

    if length == 0:
        logger.warning(
            "Given content is empty, stopping the process very early, returning empty utf_8 str match"
        )
        return CharsetMatches([CharsetMatch(sequences, "utf_8", 0.0, False, [], "")])

    if cp_isolation is not None:
        logger.warning(
            "cp_isolation is set. use this flag for debugging purpose. "
            "limited list of encoding allowed : %s.",
            ", ".join(cp_isolation),
        )
        cp_isolation = [iana_name(cp, False) for cp in cp_isolation]
    else:
        cp_isolation = []

    if cp_exclusion is not None:
        logger.warning(
            "cp_exclusion is set. use this flag for debugging purpose. "
            "limited list of encoding excluded : %s.",
            ", ".join(cp_exclusion),
        )
        cp_exclusion = [iana_name(cp, False) for cp in cp_exclusion]
    else:
        cp_exclusion = []

    if length <= (chunk_size * steps):
        logger.warning(
            "override steps (%i) and chunk_size (%i) as content does not fit (%i byte(s) given) parameters.",
            steps,
            chunk_size,
            length,
        )
        steps = 1
        chunk_size = length

    if steps > 1 and length / steps < chunk_size:
        chunk_size = int(length / steps)

    is_too_small_sequence = len(sequences) < TOO_SMALL_SEQUENCE  # type: bool
    is_too_large_sequence = len(sequences) >= TOO_BIG_SEQUENCE  # type: bool

    if is_too_small_sequence:
        logger.warning(
            "Trying to detect encoding from a tiny portion of ({}) byte(s).".format(
                length
            )
        )
    elif is_too_large_sequence:
        logger.info(
            "Using lazy str decoding because the payload is quite large, ({}) byte(s).".format(
                length
            )
        )

    prioritized_encodings = []  # type: List[str]

    specified_encoding = (
        any_specified_encoding(sequences) if preemptive_behaviour is True else None
    )  # type: Optional[str]

    if specified_encoding is not None:
        prioritized_encodings.append(specified_encoding)
        logger.info(
            "Detected declarative mark in sequence. Priority +1 given for %s.",
            specified_encoding,
        )

    tested = set()  # type: Set[str]
    tested_but_hard_failure = []  # type: List[str]
    tested_but_soft_failure = []  # type: List[str]

    fallback_ascii = None  # type: Optional[CharsetMatch]
    fallback_u8 = None  # type: Optional[CharsetMatch]
    fallback_specified = None  # type: Optional[CharsetMatch]

    results = CharsetMatches()  # type: CharsetMatches

    sig_encoding, sig_payload = identify_sig_or_bom(sequences)

    if sig_encoding is not None:
        prioritized_encodings.append(sig_encoding)
        logger.info(
            "Detected a SIG or BOM mark on first %i byte(s). Priority +1 given for %s.",
            len(sig_payload),
            sig_encoding,
        )

    prioritized_encodings.append("ascii")

    if "utf_8" not in prioritized_encodings:
        prioritized_encodings.append("utf_8")

    for encoding_iana in prioritized_encodings + IANA_SUPPORTED:

        if cp_isolation and encoding_iana not in cp_isolation:
            continue

        if cp_exclusion and encoding_iana in cp_exclusion:
            continue

        if encoding_iana in tested:
            continue

        tested.add(encoding_iana)

        decoded_payload = None  # type: Optional[str]
        bom_or_sig_available = sig_encoding == encoding_iana  # type: bool
        strip_sig_or_bom = bom_or_sig_available and should_strip_sig_or_bom(
            encoding_iana
        )  # type: bool

        if encoding_iana in {"utf_16", "utf_32"} and bom_or_sig_available is False:
            logger.info(
                "Encoding %s wont be tested as-is because it require a BOM. Will try some sub-encoder LE/BE.",
                encoding_iana,
            )
            continue

        try:
            is_multi_byte_decoder = is_multi_byte_encoding(encoding_iana)  # type: bool
        except (ModuleNotFoundError, ImportError):
            logger.debug(
                "Encoding %s does not provide an IncrementalDecoder", encoding_iana
            )
            continue

        try:
            if is_too_large_sequence and is_multi_byte_decoder is False:
                str(
                    sequences[: int(50e4)]
                    if strip_sig_or_bom is False
                    else sequences[len(sig_payload) : int(50e4)],
                    encoding=encoding_iana,
                )
            else:
                decoded_payload = str(
                    sequences
                    if strip_sig_or_bom is False
                    else sequences[len(sig_payload) :],
                    encoding=encoding_iana,
                )
        except (UnicodeDecodeError, LookupError) as e:
            if not isinstance(e, LookupError):
                logger.warning(
                    "Code page %s does not fit given bytes sequence at ALL. %s",
                    encoding_iana,
                    str(e),
                )
            tested_but_hard_failure.append(encoding_iana)
            continue

        similar_soft_failure_test = False  # type: bool

        for encoding_soft_failed in tested_but_soft_failure:
            if is_cp_similar(encoding_iana, encoding_soft_failed):
                similar_soft_failure_test = True
                break

        if similar_soft_failure_test:
            logger.warning(
                "%s is deemed too similar to code page %s and was consider unsuited already. Continuing!",
                encoding_iana,
                encoding_soft_failed,
            )
            continue

        r_ = range(
            0 if bom_or_sig_available is False else len(sig_payload),
            length,
            int(length / steps),
        )

        multi_byte_bonus = (
            is_multi_byte_decoder
            and decoded_payload is not None
            and len(decoded_payload) < length
        )  # type: bool

        if multi_byte_bonus:
            logger.info(
                "Code page %s is a multi byte encoding table and it appear that at least one character "
                "was encoded using n-bytes.",
                encoding_iana,
            )

        max_chunk_gave_up = int(len(r_) / 4)  # type: int

        if max_chunk_gave_up < 2:
            max_chunk_gave_up = 2

        early_stop_count = 0  # type: int

        md_chunks = []  # type: List[str]
        md_ratios = []

        for i in r_:
            cut_sequence = sequences[i : i + chunk_size]

            if bom_or_sig_available and strip_sig_or_bom is False:
                cut_sequence = sig_payload + cut_sequence

            chunk = cut_sequence.decode(encoding_iana, errors="ignore")  # type: str

            # multi-byte bad cutting detector and adjustment
            # not the cleanest way to perform that fix but clever enough for now.
            if is_multi_byte_decoder and i > 0 and sequences[i] >= 0x80:

                chunk_partial_size_chk = (
                    16 if chunk_size > 16 else chunk_size
                )  # type: int

                if (
                    decoded_payload
                    and chunk[:chunk_partial_size_chk] not in decoded_payload
                ):
                    for j in range(i, i - 4, -1):
                        cut_sequence = sequences[j : i + chunk_size]

                        if bom_or_sig_available and strip_sig_or_bom is False:
                            cut_sequence = sig_payload + cut_sequence

                        chunk = cut_sequence.decode(encoding_iana, errors="ignore")

                        if chunk[:chunk_partial_size_chk] in decoded_payload:
                            break

            md_chunks.append(chunk)

            md_ratios.append(mess_ratio(chunk, threshold))

            if md_ratios[-1] >= threshold:
                early_stop_count += 1

            if (early_stop_count >= max_chunk_gave_up) or (
                bom_or_sig_available and strip_sig_or_bom is False
            ):
                break

        if md_ratios:
            mean_mess_ratio = sum(md_ratios) / len(md_ratios)  # type: float
        else:
            mean_mess_ratio = 0.0

        if mean_mess_ratio >= threshold or early_stop_count >= max_chunk_gave_up:
            tested_but_soft_failure.append(encoding_iana)
            logger.warning(
                "%s was excluded because of initial chaos probing. Gave up %i time(s). "
                "Computed mean chaos is %f %%.",
                encoding_iana,
                early_stop_count,
                round(mean_mess_ratio * 100, ndigits=3),
            )
            # Preparing those fallbacks in case we got nothing.
            if encoding_iana in ["ascii", "utf_8", specified_encoding]:
                fallback_entry = CharsetMatch(
                    sequences, encoding_iana, threshold, False, [], decoded_payload
                )
                if encoding_iana == specified_encoding:
                    fallback_specified = fallback_entry
                elif encoding_iana == "ascii":
                    fallback_ascii = fallback_entry
                else:
                    fallback_u8 = fallback_entry
            continue

        logger.info(
            "%s passed initial chaos probing. Mean measured chaos is %f %%",
            encoding_iana,
            round(mean_mess_ratio * 100, ndigits=3),
        )

        if not is_multi_byte_decoder:
            target_languages = encoding_languages(encoding_iana)  # type: List[str]
        else:
            target_languages = mb_encoding_languages(encoding_iana)

        if target_languages:
            logger.info(
                "{} should target any language(s) of {}".format(
                    encoding_iana, str(target_languages)
                )
            )

        cd_ratios = []

        for chunk in md_chunks:
            chunk_languages = coherence_ratio(
                chunk, 0.1, ",".join(target_languages) if target_languages else None
            )

            cd_ratios.append(chunk_languages)

        cd_ratios_merged = merge_coherence_ratios(cd_ratios)

        if cd_ratios_merged:
            logger.info(
                "We detected language {} using {}".format(
                    cd_ratios_merged, encoding_iana
                )
            )

        results.append(
            CharsetMatch(
                sequences,
                encoding_iana,
                mean_mess_ratio,
                bom_or_sig_available,
                cd_ratios_merged,
                decoded_payload,
            )
        )

        if (
            encoding_iana in [specified_encoding, "ascii", "utf_8"]
            and mean_mess_ratio < 0.1
        ):
            logger.info(
                "%s is most likely the one. Stopping the process.", encoding_iana
            )
            return CharsetMatches([results[encoding_iana]])

        if encoding_iana == sig_encoding:
            logger.info(
                "%s is most likely the one as we detected a BOM or SIG within the beginning of the sequence.",
                encoding_iana,
            )
            return CharsetMatches([results[encoding_iana]])

    if len(results) == 0:
        if fallback_u8 or fallback_ascii or fallback_specified:
            logger.warning(
                "Nothing got out of the detection process. Using ASCII/UTF-8/Specified fallback."
            )

        if fallback_specified:
            logger.warning(
                "%s will be used as a fallback match", fallback_specified.encoding
            )
            results.append(fallback_specified)
        elif (
            (fallback_u8 and fallback_ascii is None)
            or (
                fallback_u8
                and fallback_ascii
                and fallback_u8.fingerprint != fallback_ascii.fingerprint
            )
            or (fallback_u8 is not None)
        ):
            logger.warning("utf_8 will be used as a fallback match")
            results.append(fallback_u8)
        elif fallback_ascii:
            logger.warning("ascii will be used as a fallback match")
            results.append(fallback_ascii)

    return results


def from_fp(
    fp: BinaryIO,
    steps: int = 5,
    chunk_size: int = 512,
    threshold: float = 0.20,
    cp_isolation: List[str] = None,
    cp_exclusion: List[str] = None,
    preemptive_behaviour: bool = True,
    explain: bool = False,
) -> CharsetMatches:
    """
    Same thing than the function from_bytes but using a file pointer that is already ready.
    Will not close the file pointer.
    """
    return from_bytes(
        fp.read(),
        steps,
        chunk_size,
        threshold,
        cp_isolation,
        cp_exclusion,
        preemptive_behaviour,
        explain,
    )


def from_path(
    path: PathLike,
    steps: int = 5,
    chunk_size: int = 512,
    threshold: float = 0.20,
    cp_isolation: List[str] = None,
    cp_exclusion: List[str] = None,
    preemptive_behaviour: bool = True,
    explain: bool = False,
) -> CharsetMatches:
    """
    Same thing than the function from_bytes but with one extra step. Opening and reading given file path in binary mode.
    Can raise IOError.
    """
    with open(path, "rb") as fp:
        return from_fp(
            fp,
            steps,
            chunk_size,
            threshold,
            cp_isolation,
            cp_exclusion,
            preemptive_behaviour,
            explain,
        )


def normalize(
    path: PathLike,
    steps: int = 5,
    chunk_size: int = 512,
    threshold: float = 0.20,
    cp_isolation: List[str] = None,
    cp_exclusion: List[str] = None,
    preemptive_behaviour: bool = True,
) -> CharsetMatch:
    """
    Take a (text-based) file path and try to create another file next to it, this time using UTF-8.
    """
    results = from_path(
        path,
        steps,
        chunk_size,
        threshold,
        cp_isolation,
        cp_exclusion,
        preemptive_behaviour,
    )

    filename = basename(path)
    target_extensions = list(splitext(filename))

    if len(results) == 0:
        raise IOError(
            'Unable to normalize "{}", no encoding charset seems to fit.'.format(
                filename
            )
        )

    result = results.best()

    target_extensions[0] += "-" + result.encoding  # type: ignore

    with open(
        "{}".format(str(path).replace(filename, "".join(target_extensions))), "wb"
    ) as fp:
        fp.write(result.output())  # type: ignore

    return result  # type: ignore
