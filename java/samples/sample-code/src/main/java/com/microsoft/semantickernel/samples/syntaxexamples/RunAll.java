package com.microsoft.semantickernel.samples.syntaxexamples;

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
                Example03_Variables::main,
                Example04_CombineLLMPromptsAndNativeCode::main,
                Example05_InlineFunctionDefinition::main,
                Example06_TemplateLanguage::main,
                Example08_RetryHandler::main,
                Example09_FunctionTypes::main,
                Example12_SequentialPlanner::main,
                Example13_ConversationSummarySkill::main,
                Example14_SemanticMemory::main,
                Example15_MemorySkill::main,
                Example17_ChatGPT::main,
                Example25_ReadOnlyMemoryStore::main,
                Example28_ActionPlanner::main,
                Example29_Tokenizer::main,
                Example33_StreamingChat::main
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
