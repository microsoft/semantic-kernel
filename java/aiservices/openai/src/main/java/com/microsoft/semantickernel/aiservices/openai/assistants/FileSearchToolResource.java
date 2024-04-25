package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.List;

public interface FileSearchToolResource extends ToolResource {

    @Override
    default ToolType getType() {
        return ToolType.FILE_SEARCH;
    }

    List<String> getVectorStoreIds();
}
