// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.settings.GPT3Settings;

import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class GPT3Tokenizer {
    /**
     * Port of GPT3 Javascript tokenizer recommended by OpenAI. See <a
     * href="https://platform.openai.com/tokenizer">GPT3 tokernizer</a> and <a
     * href="https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them">What
     * are tokens and how to count them</a>
     */
    private static final char[] bytesToUnicode =
            new char[] {
                (char) 0x0100, (char) 0x0101, (char) 0x0102, (char) 0x0103, (char) 0x0104,
                        (char) 0x0105, (char) 0x0106, (char) 0x0107,
                (char) 0x0108, (char) 0x0109, (char) 0x010A, (char) 0x010B, (char) 0x010C,
                        (char) 0x010D, (char) 0x010E, (char) 0x010F,
                (char) 0x0110, (char) 0x0111, (char) 0x0112, (char) 0x0113, (char) 0x0114,
                        (char) 0x0115, (char) 0x0116, (char) 0x0117,
                (char) 0x0118, (char) 0x0119, (char) 0x011A, (char) 0x011B, (char) 0x011C,
                        (char) 0x011D, (char) 0x011E, (char) 0x011F,
                (char) 0x0120, (char) 0x0021, (char) 0x0022, (char) 0x0023, (char) 0x0024,
                        (char) 0x0025, (char) 0x0026, (char) 0x0027,
                (char) 0x0028, (char) 0x0029, (char) 0x002A, (char) 0x002B, (char) 0x002C,
                        (char) 0x002D, (char) 0x002E, (char) 0x002F,
                (char) 0x0030, (char) 0x0031, (char) 0x0032, (char) 0x0033, (char) 0x0034,
                        (char) 0x0035, (char) 0x0036, (char) 0x0037,
                (char) 0x0038, (char) 0x0039, (char) 0x003A, (char) 0x003B, (char) 0x003C,
                        (char) 0x003D, (char) 0x003E, (char) 0x003F,
                (char) 0x0040, (char) 0x0041, (char) 0x0042, (char) 0x0043, (char) 0x0044,
                        (char) 0x0045, (char) 0x0046, (char) 0x0047,
                (char) 0x0048, (char) 0x0049, (char) 0x004A, (char) 0x004B, (char) 0x004C,
                        (char) 0x004D, (char) 0x004E, (char) 0x004F,
                (char) 0x0050, (char) 0x0051, (char) 0x0052, (char) 0x0053, (char) 0x0054,
                        (char) 0x0055, (char) 0x0056, (char) 0x0057,
                (char) 0x0058, (char) 0x0059, (char) 0x005A, (char) 0x005B, (char) 0x005C,
                        (char) 0x005D, (char) 0x005E, (char) 0x005F,
                (char) 0x0060, (char) 0x0061, (char) 0x0062, (char) 0x0063, (char) 0x0064,
                        (char) 0x0065, (char) 0x0066, (char) 0x0067,
                (char) 0x0068, (char) 0x0069, (char) 0x006A, (char) 0x006B, (char) 0x006C,
                        (char) 0x006D, (char) 0x006E, (char) 0x006F,
                (char) 0x0070, (char) 0x0071, (char) 0x0072, (char) 0x0073, (char) 0x0074,
                        (char) 0x0075, (char) 0x0076, (char) 0x0077,
                (char) 0x0078, (char) 0x0079, (char) 0x007A, (char) 0x007B, (char) 0x007C,
                        (char) 0x007D, (char) 0x007E, (char) 0x0121,
                (char) 0x0122, (char) 0x0123, (char) 0x0124, (char) 0x0125, (char) 0x0126,
                        (char) 0x0127, (char) 0x0128, (char) 0x0129,
                (char) 0x012A, (char) 0x012B, (char) 0x012C, (char) 0x012D, (char) 0x012E,
                        (char) 0x012F, (char) 0x0130, (char) 0x0131,
                (char) 0x0132, (char) 0x0133, (char) 0x0134, (char) 0x0135, (char) 0x0136,
                        (char) 0x0137, (char) 0x0138, (char) 0x0139,
                (char) 0x013A, (char) 0x013B, (char) 0x013C, (char) 0x013D, (char) 0x013E,
                        (char) 0x013F, (char) 0x0140, (char) 0x0141,
                (char) 0x0142, (char) 0x00A1, (char) 0x00A2, (char) 0x00A3, (char) 0x00A4,
                        (char) 0x00A5, (char) 0x00A6, (char) 0x00A7,
                (char) 0x00A8, (char) 0x00A9, (char) 0x00AA, (char) 0x00AB, (char) 0x00AC,
                        (char) 0x0143, (char) 0x00AE, (char) 0x00AF,
                (char) 0x00B0, (char) 0x00B1, (char) 0x00B2, (char) 0x00B3, (char) 0x00B4,
                        (char) 0x00B5, (char) 0x00B6, (char) 0x00B7,
                (char) 0x00B8, (char) 0x00B9, (char) 0x00BA, (char) 0x00BB, (char) 0x00BC,
                        (char) 0x00BD, (char) 0x00BE, (char) 0x00BF,
                (char) 0x00C0, (char) 0x00C1, (char) 0x00C2, (char) 0x00C3, (char) 0x00C4,
                        (char) 0x00C5, (char) 0x00C6, (char) 0x00C7,
                (char) 0x00C8, (char) 0x00C9, (char) 0x00CA, (char) 0x00CB, (char) 0x00CC,
                        (char) 0x00CD, (char) 0x00CE, (char) 0x00CF,
                (char) 0x00D0, (char) 0x00D1, (char) 0x00D2, (char) 0x00D3, (char) 0x00D4,
                        (char) 0x00D5, (char) 0x00D6, (char) 0x00D7,
                (char) 0x00D8, (char) 0x00D9, (char) 0x00DA, (char) 0x00DB, (char) 0x00DC,
                        (char) 0x00DD, (char) 0x00DE, (char) 0x00DF,
                (char) 0x00E0, (char) 0x00E1, (char) 0x00E2, (char) 0x00E3, (char) 0x00E4,
                        (char) 0x00E5, (char) 0x00E6, (char) 0x00E7,
                (char) 0x00E8, (char) 0x00E9, (char) 0x00EA, (char) 0x00EB, (char) 0x00EC,
                        (char) 0x00ED, (char) 0x00EE, (char) 0x00EF,
                (char) 0x00F0, (char) 0x00F1, (char) 0x00F2, (char) 0x00F3, (char) 0x00F4,
                        (char) 0x00F5, (char) 0x00F6, (char) 0x00F7,
                (char) 0x00F8, (char) 0x00F9, (char) 0x00FA, (char) 0x00FB, (char) 0x00FC,
                        (char) 0x00FD, (char) 0x00FE, (char) 0x00FF
            };

    // Regex for English contractions, e.g. "he's", "we'll", "I'm" etc.
    private static final Pattern encodingRegex =
            Pattern.compile(
                    "'s|'t|'re|'ve|'m|'ll|'d| ?\\p{L}+| ?\\p{N}+|"
                            + " ?[^\\s\\p{L}\\p{N}]+|\\s+(?!\\S)|\\s+");

    private static final Map<String, List<String>> bpeCache;
    private static final String MAX_TOKENIZER_CACHE_SIZE_KEY = "MAX_TOKENIZER_CACHE_SIZE";
    private static final String MAX_TOKENIZER_CACHE_SIZE_DEFAULT = "100000";

    static {
        // Limit the maximum cache size
        int cacheSize =
                Integer.parseInt(
                        System.getProperty(
                                MAX_TOKENIZER_CACHE_SIZE_KEY, MAX_TOKENIZER_CACHE_SIZE_DEFAULT));
        bpeCache =
                new LinkedHashMap<String, List<String>>() {
                    @Override
                    protected boolean removeEldestEntry(Map.Entry<String, List<String>> eldest) {
                        return size() > cacheSize;
                    }
                };
    }

    /**
     * The tokenizer uses a byte-pair encoding (BPE) algorithm to split words into sub-words based
     * on frequency and merges rules. It can handle out-of-vocabulary words, punctuation, and
     * special tokens.
     *
     * @param text Text to tokenize
     * @return List of token IDs
     */
    public static List<Integer> encode(String text) {
        List<Integer> bpeTokens = new ArrayList<>();

        if (text != null && !text.isEmpty()) {
            // Find all the matches.
            Matcher matcher = encodingRegex.matcher(text);

            // Determine the maximum number of UTF8 bytes that any match value could require.
            int maxUtf8Length = 0;
            while (matcher.find()) {
                String matchValue = matcher.group();
                int utf8Length = encodingUtf8GetByteCount(matchValue);
                if (utf8Length > maxUtf8Length) {
                    maxUtf8Length = utf8Length;
                }
            }

            // Ensure we have a sufficient char array to accommodate maxUtf8Length chars.
            // The byte-to-char mapping scheme employed is 1:1, so we'll end up needing 1 char
            // for every 1 UTF8 byte.
            char[] chars = new char[maxUtf8Length];

            // Rather than using separate space for the UTF8 bytes, we just reinterpret the char
            // array as a byte array. Since our mapping is 1:1,
            // the space required for the bytes will always be half of the space required for
            // the chars. We can UTF8-encode into the first half,
            // and then walk backwards through the bytes, using the byte-to-char mapping
            // scheme to populate the chars from the back to the front. By going in reverse,
            // we guarantee we won't overwrite any bytes we haven't yet seen.
            byte[] bytes = new byte[maxUtf8Length];

            // Now that our space is created, do the actual encoding.
            matcher.reset();
            while (matcher.find()) {
                String matchValue = matcher.group();

                // Encode the UTF8 bytes.
                int bytesWritten = encodingUtf8GetBytes(matchValue, bytes);

                // Translate those bytes into chars.
                for (int i = bytesWritten - 1; i >= 0; i--) {
                    chars[i] = bytesToUnicode[bytes[i] & 0xFF];
                }

                // Evaluate the BPE for the encoded chars.
                for (String encoding : bytePairEncoding(new String(chars, 0, bytesWritten))) {
                    bpeTokens.add(GPT3Settings.encoder.get(encoding));
                }
            }
        }

        return bpeTokens;
    }

    public static List<Integer> encode(StringBuilder stringBuilder) {
        if (stringBuilder != null) {
            return encode(stringBuilder.toString());
        } else {
            return Collections.emptyList();
        }
    }

    public static List<Integer> encode(char[] chars) {
        if (chars != null) {
            return encode(new String(chars));
        } else {
            return Collections.emptyList();
        }
    }

    public static List<Integer> encode(Iterable<Character> chars) {
        if (chars != null) {
            StringBuilder sb = new StringBuilder();
            for (Character c : chars) {
                sb.append(c);
            }
            return encode(sb.toString());
        } else {
            return Collections.emptyList();
        }
    }

    private static int encodingUtf8GetByteCount(String str) {
        return str.getBytes(StandardCharsets.UTF_8).length;
    }

    private static int encodingUtf8GetBytes(String str, byte[] bytes) {
        assert str != null;
        assert bytes != null;

        byte[] strBytes = str.getBytes(StandardCharsets.UTF_8);
        System.arraycopy(strBytes, 0, bytes, 0, strBytes.length);
        return strBytes.length;
    }

    private static List<String> bytePairEncoding(String token) {
        if (bpeCache.containsKey(token)) {
            return bpeCache.get(token);
        }

        if (token.length() <= 1) {
            List<String> list = new ArrayList<>(1);
            list.add(token);
            bpeCache.put(token, list);
            return list;
        }

        List<String> word = new ArrayList<>(token.length());
        for (char c : token.toCharArray()) {
            word.add(String.valueOf(c));
        }

        long smallestRank = Long.MAX_VALUE;
        Tuple2<String, String> smallestPair = Tuples.of("", "");
        List<String> newWord;

        while (word.size() >= 2) {
            for (int pairIndex = 0; pairIndex < word.size() - 1; pairIndex++) {
                Tuple2<String, String> pair =
                        Tuples.of(word.get(pairIndex), word.get(pairIndex + 1));

                long pairRank =
                        GPT3Settings.bpeRanks.containsKey(pair)
                                ? GPT3Settings.bpeRanks.get(pair)
                                : 100_000_000_000L;

                if (pairRank <= smallestRank) {
                    smallestRank = pairRank;
                    smallestPair = pair;
                }
            }

            if (!GPT3Settings.bpeRanks.containsKey(smallestPair)) {
                break;
            }

            String first = smallestPair.getT1();
            String second = smallestPair.getT2();

            newWord = new ArrayList<>(word.size());
            for (int i = 0; i < word.size(); i++) {
                int j = word.subList(i, word.size()).indexOf(first);

                // Adjust j as sublist was used
                if (j >= 0) {
                    j += i;
                }

                int limit = j < 0 ? word.size() : j;
                for (int copy = i; copy < limit; copy++) {
                    newWord.add(word.get(copy));
                }

                if (j < 0) {
                    break;
                }

                i = j;

                if (i < (word.size() - 1)
                        && word.get(i).equals(first)
                        && word.get(i + 1).equals(second)) {
                    newWord.add(first + second);
                    i++;
                } else {
                    newWord.add(word.get(i));
                }
            }

            // Swap the new word in for the old
            List<String> temp = word;
            word = newWord;
            newWord = temp;

            // And reset state for the next go-around
            newWord.clear();
            smallestRank = Long.MAX_VALUE;
        }

        bpeCache.put(token, word);
        return word;
    }
}
