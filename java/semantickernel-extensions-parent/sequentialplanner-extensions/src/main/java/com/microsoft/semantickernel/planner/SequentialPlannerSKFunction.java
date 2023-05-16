// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.orchestration.SKFunction;

import javax.annotation.Nullable;
import java.util.List;

public interface SequentialPlannerSKFunction extends SKFunction<Void, SequentialPlannerSKContext> {

    interface Builder {
        SequentialPlannerSKFunction createFunction(
                String promptTemplate,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description,
                int maxTokens,
                double temperature,
                double topP,
                double presencePenalty,
                double frequencyPenalty,
                @Nullable List<String> stopSequences);
    }
}
