// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;

import javax.annotation.Nonnull;

/** Settings for a chat completion request */
public class ChatRequestSettings extends CompletionRequestSettings {
    public ChatRequestSettings() {
        super();
    }

    public ChatRequestSettings(@Nonnull CompletionRequestSettings requestSettings) {
        super(requestSettings);
    }
}
