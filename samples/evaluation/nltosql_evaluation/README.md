# Introduction 
**FMOps**(Fundamental Model Ops) is a critical aspect of the lifecycle management of the performance and quality of Open AI based systems. It consists of several steps to ensure effective system operation and improvement.  **The evaluation framework** plays an important role in the experimentation phase, facilitating rapid experimentation and providing valuable insights. 

<img width="1163" alt="image" src="https://github.com/microsoft/semantic-kernel/assets/6139790/6669fdcb-6b27-43f3-a662-f25d67c8bcfe">

This sample is an reference implementation of the evaluation framework to evaluate the qauality and the performance of NL-to-SQL capability of Azure Open AI service. It is basically a Jupiter notebook that shows how to evaluate generated completions from Azure Open AI service. It consists of three steps like loading evaluation dataset, assessing metrics and generating report. The result provides multiple statistical metrics and evaluation techniques to assess the performance of Azure Open AI models in NL-to-SQL tasks. The metrics contains query exact match, semantic accuracy(=result exact match), query syntax validity, query diff, Levenshtein score, and cosine similarity, which provide valuable insights into the performance and accuracy of the NL-to-SQL system.

This is the sample result reports.
<img width="984" alt="image" src="https://github.com/microsoft/semantic-kernel/assets/6139790/cadb8b7d-b09f-4d8c-a3ad-6ffc8047f206">

# Getting Started
1. Install required libraries
    ```shell
    pip install -r requirements.txt
    ```
1. Set up your own Azure OpenAI instance
    The evaluation framework connects directly to Azure OpenAI service for generating SQL from NL(Natural Language) input and calculating Cosine Similarity, so you need to create your own Azure OpenAI instance with both GPT model for NL-to-SQL tasks and Text Embedding model(like text-embedding-ada-002) for getting embedding vectors.
  
    After creating them, you need to update these global variables in .env with the information of your own Azure OpenAI instance. Please use .evn.example as a template.
    ```shell
    AZURE_OPENAI_DEPLOYMENT_NAME="your GPT model deployment name"
    AZURE_OPENAI_ENDPOINT="your Azure OpenAI endpoint"
    AZURE_OPENAI_API_KEY="your Azure OpenAI api key"
    # Azure Open AI Embeddings model deployment
    AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME="your Embeddings model deployment name"
    ```
    
1. Set up your own Azure SQL Server instance
    The framework also uses Azure SQL Server to check SQL Validiy, Results and Execution Time, so you need to create your own Azure SQL Server instance. It uses a sample database called "AdventureWorksLT" for evaluation, so you need to create it in your Azure SQL Server instance. 
    
    You can find how to create a free Azure SQL Server instance and a sample database in this link, https://learn.microsoft.com/en-us/azure/azure-sql/database/free-sql-db-free-account-how-to-deploy?view=azuresql#create-a-database

    After creating it, you need to update these global variables with the information of your SQL Server instance. Please use .evn.example as a template.
    ```shell
    # Azure SQL Server configuration
    AZURE_SQL_SERVER_NAME="your Azure SQL Server name"
    AZURE_SQL_SERVER_DATABASE_NAME="your Azure SQL Server database name"
    AZURE_SQL_SERVER_USERANME="your Azure SQL Server username"
    AZURE_SQL_SERVER_PASSWORD="your Azure SQL Server password$"
    AZURE_SQL_ODBC_DRIVER="your Azure SQL Server ODBC driver name"
    ```

# Build and Test
As it is a Jupyter notebook, you can run cells step by step by using hon_evaluation.ipynb.

1. Complete Getting Started above.
1. Run cells step by step, please see outputs if there are errors.
1. Check logs of the main process cell, which is a core evaluation process.
1. Check the results and statistical metrics.
1. Optionally, you can check details including charts.