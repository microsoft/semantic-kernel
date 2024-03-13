// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation;

import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.mockito.Mockito;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.CALLS_REAL_METHODS;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.withSettings;

import java.io.ByteArrayInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class EmbeddedResourceLoaderTest {

    @Test
    public void testReadFile_Classpath() {
        assertThrows(FileNotFoundException.class, () -> {
            EmbeddedResourceLoader.readFile("nonexistent.txt", this.getClass());
        });
    }

    @Test
    public void testReadFile_ClasspathRoot() {
        assertThrows(FileNotFoundException.class, () -> {
            EmbeddedResourceLoader.readFile("nonexistent.txt", this.getClass(),
                EmbeddedResourceLoader.ResourceLocation.CLASSPATH_ROOT);
        });
    }

    @Test
    public void testReadFile_FileSystem() {
        assertThrows(FileNotFoundException.class, () -> {
            EmbeddedResourceLoader.readFile("nonexistent.txt", this.getClass(),
                EmbeddedResourceLoader.ResourceLocation.FILESYSTEM);
        });
    }

    @Test
    public void testReadFile_Classpath_ExistingFile() throws FileNotFoundException {
        try (MockedStatic<EmbeddedResourceLoader> mocked = Mockito.mockStatic(
            EmbeddedResourceLoader.class,
            withSettings().defaultAnswer(CALLS_REAL_METHODS))) {

            mocked
                .when(() -> EmbeddedResourceLoader.getResourceAsStream(any(String.class),
                    any(Class.class)))
                .thenReturn("file content");

            String result = EmbeddedResourceLoader.readFile("existent.txt",
                EmbeddedResourceLoaderTest.class);
            assertEquals("file content", result);
        }
    }

    @Test
    public void testReadFile_ClasspathRoot_ExistingFile() throws FileNotFoundException {
        ClassLoader mockClassLoader = Mockito.mock(ClassLoader.class);

        InputStream inputStream = new ByteArrayInputStream(
            "file content".getBytes(StandardCharsets.UTF_8));
        when(mockClassLoader.getResourceAsStream(any(String.class))).thenReturn(inputStream);

        Thread.currentThread().setContextClassLoader(mockClassLoader);

        String result = EmbeddedResourceLoader.readFile("existent.txt",
            EmbeddedResourceLoaderTest.class,
            EmbeddedResourceLoader.ResourceLocation.CLASSPATH_ROOT);
        assertEquals("file content", result);
    }

    @Test
    public void testReadFile_FileSystem_ExistingFile() throws IOException {
        try (MockedStatic<EmbeddedResourceLoader> mocked = Mockito.mockStatic(
            EmbeddedResourceLoader.class,
            withSettings().defaultAnswer(CALLS_REAL_METHODS))) {

            mocked.when(() -> EmbeddedResourceLoader.readFileFromFileSystem(any(String.class)))
                .thenReturn("file content");

            String result = EmbeddedResourceLoader.readFile("existent.txt",
                EmbeddedResourceLoaderTest.class,
                EmbeddedResourceLoader.ResourceLocation.FILESYSTEM);
            assertEquals("file content", result);
        }
    }
}