// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.ServiceLoadUtil;
import java.util.function.Supplier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SuppressWarnings("ImmutableEnumChecker")
enum InternalBuildersSingleton {
    INST;

    // Fallback classes in case the META-INF/services directory is missing

    private static final String FALLBACK_VARIABLE_BUILDER_CLASS =
            "com.microsoft.semantickernel.orchestration.DefaultContextVariables$WritableBuilder";

    private final Supplier<WritableContextVariables.Builder> variables;

    InternalBuildersSingleton() {
        try {
            variables =
                    ServiceLoadUtil.findServiceLoader(
                            WritableContextVariables.Builder.class,
                            FALLBACK_VARIABLE_BUILDER_CLASS);

        } catch (Throwable e) {
            Logger LOGGER = LoggerFactory.getLogger(InternalBuildersSingleton.class);
            LOGGER.error("Failed to discover Semantic Kernel Builders", e);
            LOGGER.error(
                    "This is likely due to:\n\n"
                        + "- The Semantic Kernel implementation (typically provided by"
                        + " semantickernel-core) is not present on the classpath at runtime, ensure"
                        + " that this dependency is available at runtime. In maven this would be"
                        + " achieved by adding:\n"
                        + "\n"
                        + "        <dependency>\n"
                        + "            <groupId>com.microsoft.semantickernel</groupId>\n"
                        + "            <artifactId>semantickernel-core</artifactId>\n"
                        + "            <version>${skversion}</version>\n"
                        + "            <scope>runtime</scope>\n"
                        + "        </dependency>\n\n"
                        + "- The META-INF/services files that define the service loading have been"
                        + " filtered out and are not present within the running application\n\n"
                        + "- The class names have been changed (for instance shaded) preventing"
                        + " discovering the classes");

            throw e;
        }
    }

    public static WritableContextVariables.Builder variables() {
        return INST.variables.get();
    }
}
