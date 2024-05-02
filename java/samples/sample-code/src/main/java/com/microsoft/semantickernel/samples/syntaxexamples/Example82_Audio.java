// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.azure.core.util.BinaryData;
import com.microsoft.semantickernel.services.audio.AudioContent;
import com.microsoft.semantickernel.services.audio.AudioToTextExecutionSettings;
import com.microsoft.semantickernel.services.audio.AudioToTextService;
import com.microsoft.semantickernel.services.audio.TextToAudioExecutionSettings;
import com.microsoft.semantickernel.services.audio.TextToAudioService;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;

public class Example82_Audio {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    private static final String TextToAudioModel = "tts-1";
    private static final String AudioToTextModel = "whisper-1";

    public static void main(String[] args) throws IOException {
        System.out.println("======== Example82_Audio ========");
        File file = null;
        try {
            file = Files.createTempFile("audio", ".mp3").toFile();
            file.deleteOnExit();

            textToAudioAsync(file);
            audioToTextAsync(file);
        } finally {
            if (file != null) {
                file.delete();
            }
        }
    }

    public static void textToAudioAsync(File audioFile) throws IOException {

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        var textToAudioService = TextToAudioService.builder()
            .withModelId(TextToAudioModel)
            .withOpenAIAsyncClient(client)
            .build();

        String sampleText = "Hello, my name is John. I am a software engineer. I am working on a project to convert text to audio.";

        // Set execution settings (optional)
        TextToAudioExecutionSettings executionSettings = TextToAudioExecutionSettings.builder()
            .withVoice("alloy")
            .withResponseFormat("mp3")
            .withSpeed(1.0)
            .build();

        // Convert text to audio
        AudioContent audioContent = textToAudioService.getAudioContentAsync(
            sampleText,
            executionSettings)
            .block();

        // Save audio content to a file
        Files.write(audioFile.toPath(), audioContent.getData());
    }

    public static void audioToTextAsync(File audioFile) {
        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        var textToAudioService = AudioToTextService.builder()
            .withModelId(AudioToTextModel)
            .withOpenAIAsyncClient(client)
            .build();
        byte[] data = BinaryData.fromFile(audioFile.toPath()).toBytes();

        // Set execution settings (optional)
        AudioToTextExecutionSettings executionSettings = AudioToTextExecutionSettings.builder()
            .withLanguage("en")
            .withPrompt("sample prompt")
            .withResponseFormat("json")
            .withTemperature(0.3)
            .withFilename(audioFile.getName())
            .build();

        String text = textToAudioService.getTextContentsAsync(
            AudioContent.builder()
                .withData(data)
                .build(),
            executionSettings).block();

        System.out.println(text);
    }
}
