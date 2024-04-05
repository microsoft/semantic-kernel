// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

public enum ResponseFormat {

    /**
     * Only valid for openai chat completion, with GPT-4 and gpt-3.5-turbo-1106+ models.
     */
    JSON_OBJECT, TEXT;
}
