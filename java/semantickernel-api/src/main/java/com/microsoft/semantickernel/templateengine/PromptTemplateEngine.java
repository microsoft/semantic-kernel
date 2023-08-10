// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine;

import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.templateengine.blocks.Block;
import java.util.List;
import reactor.core.publisher.Mono;

/** Prompt template engine interface */
public interface PromptTemplateEngine {

    /*
        /// <summary>
        /// Given a prompt template string, extract all the blocks (text, variables, function calls)
        /// </summary>
        /// <param name="templateText">Prompt template (see skprompt.txt files)</param>
        /// <param name="validate">Whether to validate the blocks syntax, or just return the blocks found, which could contain invalid code</param>
        /// <returns>A list of all the blocks, ie the template tokenized in text, variables and function calls</returns>
        IList<Block> ExtractBlocks(
                string?templateText,
                bool validate =true);
    */

    /**
     * Given a prompt template, replace the variables with their values and execute the functions
     * replacing their reference with the function result
     *
     * @param templateText Prompt template (see skprompt.txt files)
     * @param context Access into the current kernel execution context
     * @return The prompt template ready to be used for an AI request
     */
    Mono<String> renderAsync(String templateText, SKContext context);

    /**
     * Given a prompt template string, extract all the blocks (text, variables, function calls)
     *
     * @param promptTemplate Prompt template (see skprompt.txt files)
     * @return A list of all the blocks, ie the template tokenized in text, variables and function
     *     calls
     */
    List<Block> extractBlocks(String promptTemplate);

    abstract class Builder {
        protected Builder() {}

        public abstract PromptTemplateEngine build();
    }
}
