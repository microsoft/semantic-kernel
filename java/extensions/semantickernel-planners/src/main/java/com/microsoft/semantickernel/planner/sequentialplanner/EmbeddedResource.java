// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class EmbeddedResource {

    public static String read(String name) {
        try (InputStream stream = SequentialPlanner.class.getResourceAsStream(name)) {
            byte[] buffer = new byte[stream.available()];
            stream.read(buffer);
            return new String(buffer, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
