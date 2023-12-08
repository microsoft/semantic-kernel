// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.core.util.ClientOptions;
import com.azure.core.util.Header;
import java.util.Collections;
import java.util.Map;
import javax.annotation.Nullable;

public class SemanticKernelHttpSettings {

    public static final String DEFAULT_USER_AGENT = "Semantic-Kernel-Java";

    public static ClientOptions getUserAgent(@Nullable Map<String, String> configuredSettings) {

        String useragent;

        if (configuredSettings == null) {
            useragent = DEFAULT_USER_AGENT;
        } else {
            useragent = configuredSettings.getOrDefault("useragent", DEFAULT_USER_AGENT);
        }

        return new ClientOptions()
                .setHeaders(Collections.singletonList(new Header("User-Agent", useragent)));
    }

    public static ClientOptions getUserAgent() {
        return getUserAgent(null);
    }
}
