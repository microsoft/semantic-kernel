// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.ContextVariables;

public class TextBlock extends Block implements TextRendering {

    // internal override BlockTypes Type => BlockTypes.Text;

    public TextBlock(String text) {
        super(text, BlockTypes.Text);
    }

    @Override
    public boolean isValid() {
        return true;
    }

    @Override
    public String render(ContextVariables variables) {
        return super.getContent();
    }

    public TextBlock(String text, int startIndex, int stopIndex) {
        super(text.substring(startIndex, stopIndex), BlockTypes.Text);
    }
    /*

       public override bool IsValid(out string errorMsg)
       {
           errorMsg = "";
           return true;
       }

       public string Render(ContextVariables? variables)
       {
           return this.Content;
       }

    */
}
