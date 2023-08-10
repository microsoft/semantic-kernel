// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.settings;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.AIException;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

public class GPT3Settings {

    public static final Map<String, Integer> encoder;
    public static final Map<Tuple2<String, String>, Integer> bpeRanks;

    static {
        try {
            encoder = getEncoder();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        try {
            bpeRanks = getBpeRanks();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    // Gets the cached encoding table (encoder.json).
    private static Map<String, Integer> getEncoder() throws IOException {
        try {
            String encodingTableJson = EmbeddedResource.readEncodingTable();

            // Read the JSON file and convert it to a Map
            ObjectMapper objectMapper = new ObjectMapper();
            return objectMapper.readValue(
                    encodingTableJson, new TypeReference<Map<String, Integer>>() {});
        } catch (IOException e) {
            System.out.println(e.getMessage());

            throw new AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    "Encoding table deserialization returned NULL");
        }
    }

    // Gets the cached byte pair encoding table (vocab.bpe).

    private static Map<Tuple2<String, String>, Integer> getBpeRanks() throws IOException {
        String table = EmbeddedResource.readBytePairEncodingTable();

        // Skip past the header line
        int pos = table.indexOf('\n') + 1;

        // For each line, split on the first space and add the pair to the map as a key with the
        // value being the entry number.
        Map<Tuple2<String, String>, Integer> result = new HashMap<>();
        int nextPos;
        while ((nextPos = table.indexOf('\n', pos)) >= 0) {
            String line = table.substring(pos, nextPos).trim();
            pos = line.indexOf(' ');
            if (pos >= 0) {
                String first = line.substring(0, pos);
                String second = line.substring(pos + 1);
                result.put(Tuples.of(first, second), result.size());
            }
            pos = nextPos + 1;
        }

        return result;
    }
}
