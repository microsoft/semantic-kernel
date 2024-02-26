# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents.chat_history import ChatHistory

class FunctionCallingStepwisePlannerResult(KernelBaseModel):
    
    final_answer: str = ""
    chat_history: ChatHistory = None
    iterations: int = 0