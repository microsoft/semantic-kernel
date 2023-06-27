package com.microsoft.semantickernel.syntaxexamples;

import java.util.Arrays;
import java.util.List;

public class RunAll {
    public interface MainMethod {
        void run(String[] args) throws Exception;
    }

    public static void main(String[] args) {
        List<MainMethod> mains = Arrays.asList(
                Example01_NativeFunctions::main,
                Example02_Pipeline::main,
                Example06_TemplateLanguage::main,
                Example08_RetryHandler::main,
                Example12_SequentialPlanner::main,
                Example13_ConversationSummarySkill::main,
                Example14_SemanticMemory::main,
                Example17_ChatGPT::main,
                Example28_ActionPlanner::main
        );

        mains.forEach(mainMethod -> {
            try {
                mainMethod.run(args);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
