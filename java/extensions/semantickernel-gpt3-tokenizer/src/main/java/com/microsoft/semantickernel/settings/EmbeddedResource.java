// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.settings;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public class EmbeddedResource {
    /**
     * Return content of BPE file.
     *
     * @return BPE file content
     */
    public static String readBytePairEncodingTable() throws IOException {
        return readFile("vocab.bpe");
    }

    /**
     * Return content of encoding table file.
     *
     * @return Encoding table string
     */
    public static String readEncodingTable() throws IOException {
        return readFile("encoder.json");
    }

    /**
     * Read a content file embedded in the project. Files are read from disk, not from the classpath
     * or the JAR file, to avoid inflating the JAR size.
     *
     * @param fileName Filename to read
     * @return File content
     * @throws FileNotFoundException Error in case the file doesn't exist
     */
    private static String readFile(String fileName) throws IOException {
        ClassLoader classLoader = EmbeddedResource.class.getClassLoader();
        InputStream inputStream = classLoader.getResourceAsStream(fileName);

        if (inputStream == null) {
            throw new FileNotFoundException("File not found: " + fileName);
        }

        try (InputStreamReader streamReader =
                        new InputStreamReader(inputStream, StandardCharsets.UTF_8);
                BufferedReader reader = new BufferedReader(streamReader)) {

            String line;
            StringBuilder builder = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                builder.append(line);
                builder.append(System.lineSeparator());
            }

            return builder.toString();
        }
    }
}
