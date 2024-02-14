package com.microsoft.semantickernel.syntaxexamples;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.recording.RecordSpecBuilder;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

public class WiremockRecord {

    public static void main(String[] args) throws IOException {
        record(
            () -> {
                WiremockExamplesIT.mains.forEach(testClazz -> {
                    try {
                        Method main = testClazz.getMethod("main", String[].class);
                        main.invoke(null, new Object[] { null });
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                });
            },
            args[0]);
    }

    public static void compressRecordings(Path mappings) throws IOException {
        Files.newDirectoryStream(mappings)
            .forEach(path -> {
                try {
                    JsonNode data = new ObjectMapper().readTree(path.toFile());

                    JsonNode body = new ObjectMapper().readTree(
                        data.get("response").get("body").asText());

                    if (body.get("id").asText().contains("chatcmpl-")) {

                        ((ObjectNode) body).put("id", "chatcmpl-xxx");

                        body
                            .get("choices")
                            .forEach(choice -> {
                                ((ObjectNode) choice.get("message")).put("content",
                                    UUID.randomUUID().toString());
                            });

                        ((ObjectNode) data.get("response")).put("body", body.toString());
                    } else if (body.get("id").asText().contains("cmpl-")) {

                        ((ObjectNode) body).put("id", "cmpl-xxx");

                        body
                            .get("choices")
                            .forEach(choice -> {
                                ((ObjectNode) choice).put("text", UUID.randomUUID().toString());
                            });

                        ((ObjectNode) data.get("response")).put("body", body.toString());
                    }

                    Files.writeString(path, data.toPrettyString());
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            });
    }

    public static void record(Runnable run, String targetUrl) throws IOException {
        Path dir = Path.of("target", "wiremock");
        if (dir.toFile().exists()) {
            dir.toFile().delete();
        }

        Files.createDirectories(dir.resolve("mappings"));

        System.out.println("Recording to: " + dir.toFile().getCanonicalPath());

        WireMockServer wireMockServer = WiremockExamplesIT.createWiremockServer(
            dir.toFile().getCanonicalPath() + "/");
        wireMockServer.start();
        wireMockServer.startRecording(
            new RecordSpecBuilder()
                .forTarget(targetUrl)
                .makeStubsPersistent(true)
                .build());

        try {
            run.run();
        } finally {
            wireMockServer.stopRecording().getStubMappings();
            wireMockServer.stop();
        }

        compressRecordings(dir.resolve("mappings"));

        System.out.println("Saved output to: " + dir.toFile().getAbsolutePath());

    }
}
