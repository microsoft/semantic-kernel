package com.microsoft.semantickernel.templateengine.semantickernel.blocks;

import com.microsoft.semantickernel.Todo;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import javax.annotation.Nullable;

public class NamedArgBlock extends Block implements TextRendering {

    private final String name;

    /**
     * Base constructor
     *
     * @param content Block content
     * @param type    Block type
     */
    public NamedArgBlock(String name, String content, BlockTypes type) {
        super(content, type);
        this.name = name;
    }

    @Override
    public boolean isValid() {
        throw new Todo();
    }

    @Nullable
    @Override
    public String render(KernelArguments variables) {
        throw new Todo();
    }

    public VarBlock getVarBlock() {
        throw new Todo();
    }

    public String getName() {
        return name;
    }

    public ContextVariable<?> getValue(KernelArguments arguments) {
        throw new Todo();
    }
}
