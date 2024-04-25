package com.microsoft.semantickernel.aiservices.openai.assistants;

import javax.annotation.Nullable;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.aiservices.openai.OpenAiService;
/**
 * Represents an OpenAI Assistant.
 */
public class AssistantService extends OpenAiService {


    public AssistantService(
        OpenAIAsyncClient client, 
        @Nullable String serviceId, 
        String modelId) {
        super(client, serviceId, modelId);
    }
    
}
