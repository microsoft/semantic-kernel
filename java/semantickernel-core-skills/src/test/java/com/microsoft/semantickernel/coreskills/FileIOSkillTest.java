package com.microsoft.semantickernel.coreskills;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import reactor.test.StepVerifier;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class FileIOSkillTest {

    @Test
    public void testReadFileAsync() throws IOException {
        // Create a temporary file with some content
        String content = "Hello, World!";
        Path tempFile = Files.createTempFile("test", ".txt");
        Files.write(tempFile, content.getBytes());

        // Create an instance of FileIOSkill
        FileIOSkill fileIOSkill = new FileIOSkill();

        // Call the readFileAsync method with the temporary file path
        String filePath = tempFile.toAbsolutePath().toString();
        StepVerifier.create(fileIOSkill.readFileAsync(filePath))
                .expectNext(content)
                .expectComplete()
                .verify();

        // Delete the temporary file
        Files.delete(tempFile);
    }

    @Test
    public void testWriteFileAsync() throws IOException {
        // Create a temporary file
        Path tempFile = Files.createTempFile("test", ".txt");

        // Create an instance of FileIOSkill
        FileIOSkill fileIOSkill = new FileIOSkill();

        // Define the content to write
        String content = "Hello, World!";

        // Call the writeFileAsync method with the temporary file path and content
        StepVerifier.create(
                        fileIOSkill.writeFileAsync(tempFile.toAbsolutePath().toString(), content))
                .expectComplete()
                .verify();

        // Read the written file to verify the content
        String fileContents = new String(Files.readAllBytes(tempFile));
        Assertions.assertEquals(content, fileContents);

        // Delete the temporary file
        Files.delete(tempFile);
    }
}
