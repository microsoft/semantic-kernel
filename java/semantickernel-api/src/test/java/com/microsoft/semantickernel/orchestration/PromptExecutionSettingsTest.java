package com.microsoft.semantickernel.orchestration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;

public class PromptExecutionSettingsTest {

    @Test
    public void testDefaultValues() {
        PromptExecutionSettings settings = new PromptExecutionSettings.Builder().build();

        assertEquals(PromptExecutionSettings.DEFAULT_SERVICE_ID, settings.getServiceId());
        assertEquals(PromptExecutionSettings.DEFAULT_MAX_TOKENS, settings.getMaxTokens());
        assertEquals(PromptExecutionSettings.DEFAULT_TEMPERATURE, settings.getTemperature());
        assertEquals(PromptExecutionSettings.DEFAULT_TOP_P, settings.getTopP());
        assertEquals(PromptExecutionSettings.DEFAULT_PRESENCE_PENALTY, settings.getPresencePenalty());
        assertEquals(PromptExecutionSettings.DEFAULT_FREQUENCY_PENALTY, settings.getFrequencyPenalty());
        assertEquals(PromptExecutionSettings.DEFAULT_BEST_OF, settings.getBestOf());
        assertEquals(PromptExecutionSettings.DEFAULT_RESULTS_PER_PROMPT, settings.getResultsPerPrompt());
        assertEquals("", settings.getModelId());
        assertEquals("", settings.getUser());
        assertTrue(settings.getStopSequences().isEmpty());
        assertTrue(settings.getTokenSelectionBiases().isEmpty());
    }

    @Test
    public void testCustomValues() {
        String serviceId = "custom-service";
        int maxTokens = 512;
        double temperature = 0.8;
        double topP = 0.5;
        double presencePenalty = 0.2;
        double frequencyPenalty = 0.3;
        int bestOf = 3;
        int resultsPerPrompt = 5;
        String modelId = "custom-model";
        String user = "custom-user";

        PromptExecutionSettings settings = new PromptExecutionSettings.Builder()
                .withServiceId(serviceId)
                .withMaxTokens(maxTokens)
                .withTemperature(temperature)
                .withTopP(topP)
                .withPresencePenalty(presencePenalty)
                .withFrequencyPenalty(frequencyPenalty)
                .withBestOf(bestOf)
                .withResultsPerPrompt(resultsPerPrompt)
                .withModelId(modelId)
                .withUser(user)
                .build();

        assertEquals(serviceId, settings.getServiceId());
        assertEquals(maxTokens, settings.getMaxTokens());
        assertEquals(temperature, settings.getTemperature());
        assertEquals(topP, settings.getTopP());
        assertEquals(presencePenalty, settings.getPresencePenalty());
        assertEquals(frequencyPenalty, settings.getFrequencyPenalty());
        assertEquals(bestOf, settings.getBestOf());
        assertEquals(resultsPerPrompt, settings.getResultsPerPrompt());
        assertEquals(modelId, settings.getModelId());
        assertEquals(user, settings.getUser());
        assertTrue(settings.getStopSequences().isEmpty());
        assertTrue(settings.getTokenSelectionBiases().isEmpty());
    }

    @Test
    void testJsonDeserialze() throws Exception {
        String json = "{"
            + "\"service_id\":\"custom-service\","
            + "\"max_tokens\":512,"
            + "\"temperature\":0.8,"
            + "\"top_p\":0.5,"
            + "\"presence_penalty\":0.2,"
            + "\"frequency_penalty\":0.3,"
            + "\"best_of\":3,"
            + "\"results_per_prompt\":5,"
            + "\"model_id\":\"custom-model\","
            + "\"user\":\"custom-user\""
            + "}";
        PromptExecutionSettings settings = new ObjectMapper().readValue(json, PromptExecutionSettings.class);

        assertEquals("custom-service", settings.getServiceId());
        assertEquals(512, settings.getMaxTokens());
        assertEquals(0.8, settings.getTemperature());
        assertEquals(0.5, settings.getTopP());
        assertEquals(0.2, settings.getPresencePenalty());
        assertEquals(0.3, settings.getFrequencyPenalty());
        assertEquals(3, settings.getBestOf());
        assertEquals(5, settings.getResultsPerPrompt());
        assertEquals("custom-model", settings.getModelId());
        assertEquals("custom-user", settings.getUser());
        assertTrue(settings.getStopSequences().isEmpty());
        assertTrue(settings.getTokenSelectionBiases().isEmpty());
    }

    @Test
    void testJsonDeserializeAndBuilder() throws Exception {
        String json = "{"
            + "\"service_id\":\"custom-service\","
            + "\"max_tokens\":512,"
            + "\"temperature\":0.8,"
            + "\"top_p\":0.5,"
            + "\"presence_penalty\":0.2,"
            + "\"frequency_penalty\":0.3,"
            + "\"best_of\":3,"
            + "\"results_per_prompt\":5,"
            + "\"model_id\":\"custom-model\","
            + "\"user\":\"custom-user\""
            + "}";
        PromptExecutionSettings settingsFromJson = new ObjectMapper().readValue(json, PromptExecutionSettings.class);

        PromptExecutionSettings settingsFromBuilder = PromptExecutionSettings.builder()
            .withServiceId("custom-service")
            .withMaxTokens(512)
            .withTemperature(0.8)
            .withTopP(0.5)
            .withPresencePenalty(0.2)
            .withFrequencyPenalty(0.3)
            .withBestOf(3)
            .withResultsPerPrompt(5)
            .withModelId("custom-model")
            .withUser("custom-user")
            .build();

        assertEquals(settingsFromBuilder, settingsFromJson);
    }
}
