package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.planner.sequentialplanner.DefaultSequentialPlannerSKFunction;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import javax.annotation.Nullable;
import java.util.List;

public class PlannerBuilders {
    public static SequentialPlannerSKFunction.Builder getPlannerBuilder(@Nullable Kernel kernel) {
        return new SequentialPlannerSKFunction.Builder() {
            @Override
            public SequentialPlannerSKFunction createFunction(
                    String promptTemplate,
                    @Nullable String functionName,
                    @Nullable String skillName,
                    @Nullable String description,
                    int maxTokens,
                    double temperature,
                    double topP,
                    double presencePenalty,
                    double frequencyPenalty,
                    @Nullable List<String> stopSequences) {
                return new DefaultSequentialPlannerSKFunction(
                        promptTemplate,

                        );
            }
        };
    }


    private static class InternalSequentialPlannerSKFunctionBuilder
            implements SequentialPlannerSKFunction.Builder {
        private final @Nullable Kernel kernel;

        private InternalSequentialPlannerSKFunctionBuilder(@Nullable Kernel kernel) {
            this.kernel = kernel;
        }

        private SequentialPlannerSKFunction register(SequentialPlannerSKFunction function) {
            if (kernel != null) {
                kernel.registerSemanticFunction(function);
            }
            return function;
        }

        @Override
        public SequentialPlannerSKFunction createFunction(
                String promptTemplate,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description,
                int maxTokens,
                double temperature,
                double topP,
                double presencePenalty,
                double frequencyPenalty,
                @Nullable List<String> stopSequences) {
            return register(
                    DefaultSequentialPlannerSKFunction.createFunction(
                            promptTemplate,
                            functionName,
                            skillName,
                            description,
                            maxTokens,
                            temperature,
                            topP,
                            presencePenalty,
                            frequencyPenalty,
                            stopSequences));
        }
    }
    ;

    public static final SequentialPlannerSKFunction.Builder PLANNER_BUILDERS =
            new InternalSequentialPlannerSKFunctionBuilder(null);

    @Override
    public CompletionSKFunction.Builder completionBuilders(@Nullable Kernel kernel) {
        if (kernel == null) {
            return COMPLETION_BUILDERS;
        } else {
            return new InternalCompletionBuilder(kernel);
        }
    }

    @Override
    public SequentialPlannerSKFunction.Builder plannerBuilders(@Nullable Kernel kernel) {
        if (kernel == null) {
            return PLANNER_BUILDERS;
        } else {
            return new InternalSequentialPlannerSKFunctionBuilder(kernel);
        }
    }
}
