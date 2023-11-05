// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

/** Base class for blocks parsed from a prompt template */
public abstract class Block {
    private final String content;
    private final BlockTypes type;

    /**
     * Base constructor
     *
     * @param content Block content
     * @param type Block type
     */
    public Block(String content, BlockTypes type) {
        if (content == null) {
            content = "";
        }

        this.content = content;
        this.type = type;
    }

    /**
     * Get the block content
     *
     * @return Block content
     */
    public String getContent() {
        return content;
    }

    /**
     * Check if the block content is valid.
     *
     * @return True if the block content is valid
     */
    public abstract boolean isValid();

    /**
     * Get the block type
     *
     * @return Block type
     */
    public BlockTypes getType() {
        return type;
    }
}
