// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

/**
 * Marker interface for Text AI services, typically Chat or Text generation for OpenAI
 */
public interface TextAIService extends AIService {
    int MAX_RESULTS_PER_PROMPT = 128;
}
