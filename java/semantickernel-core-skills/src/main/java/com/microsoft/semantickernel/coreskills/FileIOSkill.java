package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import reactor.core.publisher.Mono;

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
    public Mono<String> readFileAsync(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(name = "path", description = "Source file")
                    String path) {
        return Mono.create(
                monoSink -> {
                    try {
                        Path filePath = Paths.get(path);
                        byte[] fileBytes = Files.readAllBytes(filePath);
                        String fileContents = new String(fileBytes);
                        monoSink.success(fileContents);
                    } catch (Exception e) {
                        monoSink.error(e);
                    }
                });
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
     * @return An awaitable task.
     */
    @DefineSKFunction(description = "Write a file", name = "writeAsync")
    public Mono<Void> writeFileAsync(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(name = "path", description = "Destination file")
                    String path,
            @SKFunctionParameters(
                            name = "content",
                            description = "File content",
                            defaultValue = "",
                            type = String.class)
                    String content) {
        return Mono.create(
                monoSink -> {
                    try {
                        Path filePath = Paths.get(path);
                        Files.write(filePath, content.getBytes());
                        monoSink.success();
                    } catch (Exception e) {
                        monoSink.error(e);
                    }
                });
    }
}
