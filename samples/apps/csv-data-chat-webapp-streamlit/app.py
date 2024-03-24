import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import semantic_kernel as sk
import re
import traceback
import asyncio

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from io import StringIO

async def main():
    st.header("Streamlit Semantic Kernel Chat App 🤖")
    # Initialize the Semantic Kernel
    kernel = sk.Kernel()

    deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    service_id = "aoai_chat_completion"
    kernel.add_service(
        AzureChatCompletion(service_id=service_id, deployment_name=deployment, endpoint=endpoint, api_key=api_key),
    )

    csvDataFrame = '''Name,Age,Occupation
    John,34,Engineer
    Jane,28,Doctor
    Alice,30,Teacher
    Bob,45,Manager
    Charlie,25,Student
    '''

    # Import the necessary skills
    skills_directory = "plugins"

    interpret_skill =   kernel.import_plugin_from_prompt_directory(skills_directory, "Interpret")
    codegen_skill =   kernel.import_plugin_from_prompt_directory(skills_directory, "CodeGen")

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

        #data = StringIO(csvDataFrame)
        #df = pd.read_csv(data)
        df_head = df.head()
        df_head_short = df_head.to_string()[:1000]
        df_analysis = await kernel.invoke(analyzeDataframe, sk.KernelArguments(input=df_head_short))
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
    #if submit and df_analyzed is not None:
        # Prompt
        prompt = f"{message}"
        #st.write("Prompt: ", prompt)
        # Modify prompt using decipherPrompt semantic function
        prompt =  await kernel.invoke(decipherPrompt, sk.KernelArguments(input=prompt, dataframe=df_head_short))
        #st.write("New Prompt: ", prompt)
        # Generate Code using createQuery semantic function
        response =  await kernel.invoke(createQuery, sk.KernelArguments(input=prompt, dataframe=df_head_short))
        #st.write("Response: ", str(response))

    # Generate Response when submit button is clicked
    #if submit and uploaded_file is not None:
    if submit and df_analyzed is not None:
        # Prompt
        prompt = f"{message}"
        #st.write("Prompt: ", prompt)
        # Modify prompt using decipherPrompt semantic function
        prompt = await kernel.invoke(decipherPrompt, sk.KernelArguments(input=prompt, dataframe=df_head_short))
        #st.write("New Prompt: ", prompt)
        # Generate Code using createQuery semantic function
        response = await kernel.invoke(createQuery, sk.KernelArguments(input=prompt, dataframe=df_head_short))
        #st.write("Response: ", str(response))

        # Extract the code using regex
        try:
            if not isinstance(response, str):
                response = str(response)
            match = re.search(
                r"\[STARTCODE\]\n(.*?)\n\[ENDCODE\]", response, re.DOTALL
            )
            if match is not None:
                code = match.group(1)
            else:
                code = 'st.write("No match found")'
        except:
            code = 'st.write("Error. Try again.")'

        # Extract the explanation using regex
        try:
            explanation = re.search(
                r"\[EXPLANATION\]\n(.*?)\n\[ENDEXPLANATION\]", response, re.DOTALL
            ).group(1)
        except:
            explanation = "No Explanation"

        print(df.columns)

        # Run the code and repair if there are errors.
        # Loop three times to try to repair the code
        for i in range(3):
            try:

                # Remove Markdown syntax
                code = str(code).replace("```python", "").replace("```", "").strip()
                print(f"{i} : {code}")
                print(type(code))
                exec(str(code))
                break

            except:
                print("Code provided error trying to repair...")
                # Display error if third run
                error_message = traceback.format_exc()
                if i == 2:
                    print(error_message)
                # Repair the code
                print("** DEBUG ** Prompt: ", error_message)
                code =  await kernel.invoke(repairCode, sk.KernelArguments(input=error_message, task=prompt, df=df_head_short, code=code))
                print("New Code: ", code)
        # Write the explanation
        print(explanation)


asyncio.run(main())