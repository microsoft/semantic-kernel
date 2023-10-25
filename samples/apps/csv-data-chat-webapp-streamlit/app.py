import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import semantic_kernel as sk
import re
import traceback

from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
)
from semantic_kernel.orchestration.context_variables import ContextVariables

# Initialize the Semantic Kernel
kernel = sk.Kernel()
api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_chat_service(
    "chat_completion", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
)
# Import the necessary skills
skills_directory = "plugins"
interpret_skill = kernel.import_semantic_skill_from_directory(
    skills_directory, "Interpret"
)
codegen_skill = kernel.import_semantic_skill_from_directory(skills_directory, "CodeGen")
# Semantic Functions
analyzeDataframe = interpret_skill["AnalyzeDataframe"]
decipherPrompt = interpret_skill["DecipherPrompt"]
createQuery = codegen_skill["GenerateCode"]
repairCode = codegen_skill["CodeRepair"]


# Chat
st.title("📊 CSV Data Chat")
st.write(
    "You can ask questions about the data, and the AI will answer them. Upload a CSV file to get started."
)

# Upload sidebar
df_analyzed = False
st.sidebar.header("Upload CSV")
st.sidebar.write("Upload a CSV file to analyze")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df_head = df.head()
    df_head_short = df_head.to_string()[:1000]
    df_analysis = analyzeDataframe(
        variables=ContextVariables(content=df_head_short)
    ).result
    df_analyzed = True
    st.sidebar.write("Dataframe Analysis:")
    st.sidebar.caption(df_analysis)

# Check dataframe
if df_analyzed:
    if st.button("Check Dataframe"):
        if df_analyzed:
            st.write("The dataframe has been analyzed")
        else:
            st.write("The dataframe has not been analyzed")
        st.write(df_head)
        if st.button("Exit"):
            st.stop()

# Chat form
form = st.form(key="chat_form")
message = form.text_input(label="Message")
submit = form.form_submit_button(label="Send")

# Generate Response when submit button is clicked
if submit and uploaded_file is not None:
    # Prompt
    prompt = f"{message}"
    print("Prompt: ", prompt)
    # Modify prompt using decipherPrompt semantic function
    prompt = decipherPrompt(
        variables=ContextVariables(
            content=prompt, variables={"dataframe": df_head_short}
        )
    ).result
    print("New Prompt: ", prompt)
    # Generate Code using createQuery semantic function
    response = createQuery(
        variables=ContextVariables(
            content=prompt, variables={"dataframe": df_head_short}
        )
    ).result
    print("Response: ", response)
    # Extract the code using regex
    try:
        code = re.search(
            r"\[STARTCODE\]\n(.*?)\n\[ENDCODE\]", response, re.DOTALL
        ).group(1)
    except:
        code = 'st.write("Error. Try again.")'
    # Extract the explanation using regex
    try:
        explanation = re.search(
            r"\[EXPLANATION\]\n(.*?)\n\[ENDEXPLANATION\]", response, re.DOTALL
        ).group(1)
    except:
        explanation = "No Explanation"
    # Run the code and repair if there are errors.
    # Loop three times to try to repair the code
    for i in range(3):
        try:
            exec(code)
            break
        except:
            print("Code provided error trying to repair...")
            # Display error if third run
            error_message = traceback.format_exc()
            if i == 2:
                st.write(error_message)
            # Repair the code
            print("Prompt: ", error_message)
            code = repairCode(
                variables=ContextVariables(
                    content=error_message,
                    variables={
                        "task": prompt,
                        "df": df_head_short,
                        "code": code,
                    },
                )
            ).result
            print("New Code: ", code)
    # Write the explanation
    st.write(explanation)
