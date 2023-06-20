// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

/** Base class for blocks parsed from a prompt template */
public abstract class Block {
    private final String content;
    private final BlockTypes type;

    /// <summary>
    /// Base constructor
    /// </summary>
    /// <param name="content">Block content</param>
    /// <param name="log">App logger</param>
    public Block(String content, BlockTypes type) {
        if (content == null) {
            content = "";
        }

        this.content = content;
        this.type = type;
    }

    public String getContent() {
        return content;
    }

    /// <summary>
    /// Check if the block content is valid.
    /// </summary>
    /// <param name="errorMsg">Error message in case the content is not valid</param>
    /// <returns>True if the block content is valid</returns>
    // TODO ERROR MESSAGE
    public abstract boolean isValid();

    public BlockTypes getType() {
        return type;
    }
}
