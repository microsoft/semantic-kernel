package com.microsoft.semantickernel.templateengine.semantickernel.blocks;

import static com.microsoft.semantickernel.templateengine.semantickernel.blocks.BlockTypes.NamedArg;

import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NamedArgBlock extends Block implements TextRendering {

    private static final Logger LOGGER = LoggerFactory.getLogger(NamedArgBlock.class);

    private final String name;
    private final String value;
    private final VarBlock argNameAsVarBlock;
    private final VarBlock varBlock;
    private final ValBlock valBlock;

    public NamedArgBlock(String content, String name, String value) {
        super(content.trim(), NamedArg);
        this.name = name.trim();
        this.value = value.trim();

        this.argNameAsVarBlock = new VarBlock(Symbols.VarPrefix + name);

        if (value.startsWith(String.valueOf(Symbols.VarPrefix))) {
            this.varBlock = new VarBlock(value);
            valBlock = null;
        } else {
            this.valBlock = new ValBlock(value);
            varBlock = null;
        }
    }

    public NamedArgBlock(String content) {
        super(content, NamedArg);

        this.name = tryGetName(content);
        this.value = tryGetValue(content);
        this.argNameAsVarBlock = new VarBlock(Symbols.VarPrefix + name);

        if (value.startsWith(String.valueOf(Symbols.VarPrefix))) {
            this.varBlock = new VarBlock(value);
            valBlock = null;
        } else {
            this.valBlock = new ValBlock(value);
            varBlock = null;
        }
    }

    @Override
    public boolean isValid() {
        if (Verify.isNullOrEmpty(this.name)) {
            LOGGER.error("A named argument must have a name");
            return false;
        }

        if (this.valBlock != null && !this.valBlock.isValid()) {
            LOGGER.error("There was an issue with the named argument value for '" + name);
            return false;
        } else if (this.varBlock != null && !this.varBlock.isValid()) {
            LOGGER.error("There was an issue with the named argument value for '" + name);
            return false;
        } else if (this.valBlock == null && this.varBlock == null) {
            LOGGER.error("A named argument must have a value");
            return false;
        }

        // Argument names share the same validation as variables
        return this.argNameAsVarBlock.isValid();
    }

    @Nullable
    @Override
    public String render(KernelArguments variables) {
        return getContent();
    }

    @Nullable
    public VarBlock getVarBlock() {
        return varBlock;

    }

    public String getName() {
        return name;
    }

    public String getValue(KernelArguments arguments) {
        boolean valueIsValidValBlock = this.valBlock != null && this.valBlock.isValid();
        if (valueIsValidValBlock) {
            return this.valBlock.render(arguments);
        }

        boolean valueIsValidVarBlock = this.varBlock != null && this.varBlock.isValid();
        if (valueIsValidVarBlock) {
            return this.varBlock.render(arguments);
        }

        return "";
    }

    /// <summary>
    /// Attempts to extract the name and value of a named argument block from a string
    /// </summary>
    /// <param name="text">String from which to extract a name and value</param>
    /// <param name="name">Name extracted from argument block, when successful. Empty string otherwise.</param>
    /// <param name="value">Value extracted from argument block, when successful. Empty string otherwise.</param>
    /// <returns>true when a name and value are successfully extracted from the given text, false otherwise</returns>

    @Nullable
    public static String tryGetName(String text) {
        return splitAndGetPart(text, 0);
    }

    @Nullable
    public static String tryGetValue(String text) {
        return splitAndGetPart(text, 1);
    }

    @Nullable
    private static String splitAndGetPart(String text, int x) {
        if (Verify.isNullOrEmpty(text)) {
            return null;
        }

        String[] argBlockParts = text.split(String.valueOf(Symbols.NamedArgBlockSeparator));

        if (argBlockParts.length == 2) {
            return argBlockParts[x].trim();
        }
        return null;
    }
}
