// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Read and write from a file.
 *
 * <p>Usage: kernel.ImportSkill("file", new FileIOSkill());
 *
 * <p>Examples:
 *
 * <pre>{@code
 * file.readAsync($path) => "hello world"
 * file.writeAsync()
 * }</pre>
 */
public class FileIOSkill {

    /**
     * Read a file.
     *
     * <p>Example:
     *
     * <pre>{@code
     * file.readAsync($path) => "hello world"
     * }</pre>
     *
     * @param path Source file.
     * @return File content.
     */
    @DefineSKFunction(description = "Read a file", name = "readAsync")
    public String readFileAsync(
            @SKFunctionInputAttribute(description = "Source file") String path,
            @SKFunctionParameters(
                            name = "charset",
                            description = "Character set to use to read the file",
                            defaultValue = "UTF-8")
                    String charset)
            throws IOException {
        Path filePath = Paths.get(path);
        byte[] fileBytes;
        fileBytes = Files.readAllBytes(filePath);
        String fileContents = new String(fileBytes, Charset.forName(charset));
        return fileContents;
    }

    /**
     * Write a file.
     *
     * <p>Example:
     *
     * <pre>{@code
     * file.writeAsync()
     * }</pre>
     *
     * @param path The destination file.
     * @param content Contains the 'content' to write
     */
    @DefineSKFunction(description = "Write a file", name = "writeAsync")
    public void writeFileAsync(
            @SKFunctionInputAttribute(description = "Destination file") String path,
            @SKFunctionParameters(
                            name = "content",
                            description = "File content",
                            defaultValue = "",
                            type = String.class)
                    String content,
            @SKFunctionParameters(
                            name = "charset",
                            description = "Character set to use to read the file",
                            defaultValue = "UTF-8")
                    String charset)
            throws IOException {
        Path filePath = Paths.get(path);
        Files.write(filePath, content.getBytes(charset));
    }
}
