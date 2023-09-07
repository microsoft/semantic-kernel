// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.util;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

public class EmbeddedResourceLoader {

    public enum ResourceLocation {
        CLASSPATH,
        FILESYSTEM,
        CLASSPATH_ROOT
    }

    /**
     * Loads a file to a string from the classpath using getResourceAsStream
     *
     * @param fileName Filename to read
     * @return File content
     * @throws FileNotFoundException Error in case the file doesn't exist
     */
    public static String readFile(String fileName, Class<?> clazz) throws FileNotFoundException {
        return readFile(fileName, clazz, ResourceLocation.CLASSPATH);
    }

    /**
     * Loads a file to a string from the classpath, classpath root or filesystem
     *
     * @param fileName Filename to read
     * @return File content
     * @throws FileNotFoundException Error in case the file doesn't exist
     */
    public static String readFile(String fileName, Class<?> clazz, ResourceLocation... locations)
            throws FileNotFoundException {

        List<ResourceLocation> locationsList =
                Arrays.stream(locations).collect(Collectors.toList());

        Optional<String> fileContents =
                locationsList.stream()
                        .map(
                                type -> {
                                    switch (type) {
                                        case CLASSPATH:
                                            try (InputStream inputStream =
                                                    clazz.getResourceAsStream(fileName)) {
                                                return readInputStream(fileName, inputStream);
                                            } catch (Exception e) {
                                                // IGNORE
                                            }
                                            break;
                                        case CLASSPATH_ROOT:
                                            try (InputStream inputStream =
                                                    clazz.getClassLoader()
                                                            .getResourceAsStream(fileName)) {
                                                return readInputStream(fileName, inputStream);
                                            } catch (IOException e) {
                                                // IGNORE
                                            }
                                            break;
                                        case FILESYSTEM:
                                            File file = new File(fileName);
                                            if (file.exists()) {
                                                try (InputStream inputStream =
                                                        Files.newInputStream(file.toPath())) {
                                                    return readInputStream(fileName, inputStream);
                                                } catch (IOException e) {
                                                    // IGNORE
                                                }
                                            }
                                            break;
                                        default:
                                    }
                                    return null;
                                })
                        .filter(Objects::nonNull)
                        .findFirst();

        if (fileContents.isPresent()) {
            return fileContents.get();
        }

        throw new FileNotFoundException("Could not find file " + fileName);
    }

    private static String readInputStream(String fileName, InputStream inputStream)
            throws FileNotFoundException {
        if (inputStream == null) {
            throw new FileNotFoundException("File not found: " + fileName);
        }

        return new BufferedReader(
                        new InputStreamReader(inputStream, java.nio.charset.StandardCharsets.UTF_8))
                .lines()
                .collect(Collectors.joining("\n"));
    }
}
