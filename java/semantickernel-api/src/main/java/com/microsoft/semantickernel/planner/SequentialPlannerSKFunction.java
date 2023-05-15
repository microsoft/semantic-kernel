// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.orchestration.SKFunction;

import java.util.List;

import javax.annotation.Nullable;

public interface SequentialPlannerSKFunction extends SKFunction<Void, SequentialPlannerSKContext> {

    static SequentialPlannerSKFunction.Builder builder() {
        return BuildersSingleton.INST.getFunctionBuilders().plannerBuilders(null);
    }

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
