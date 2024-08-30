# Semantic Kernel Python Telemetry with Application Insights

This sample project shows how a Python application can be configured to send Semantic Kernel telemetry to Application Insights.

> Note that it is also possible to use other Application Performance Management (APM) vendors. An example is [Prometheus](https://prometheus.io/docs/introduction/overview/). Please refer to this [link](https://opentelemetry.io/docs/languages/python/exporters/) to learn more about exporters.


For more information, please refer to the following resources:
1. [Azure Monitor OpenTelemetry Exporter](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/monitor/azure-monitor-opentelemetry-exporter)
2. [Python Logging](https://docs.python.org/3/library/logging.html)
3. [Observability in Python](https://www.cncf.io/blog/2022/04/22/opentelemetry-and-python-a-complete-instrumentation-guide/)

## What to expect

The Semantic Kernel Python SDK is designed to efficiently generate comprehensive logs, traces, and metrics throughout the flow of function execution and model invocation. This allows you to effectively monitor your AI application's performance and accurately track token consumption.

## Configuration

### Required resources
1. [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource)
2. OpenAI or [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal)

### Dependencies
You will also need to install the following dependencies to your virtual environment to run this sample:
```
pip install azure-monitor-opentelemetry-exporter==1.0.0b24
```

## Running the sample

1. Open a terminal and navigate to this folder: `python/samples/demos/telemetry_with_application_insights/`. This is necessary for the `.env` file to be read correctly.
2. Create a `.env` file if one doesn't already exist in this folder. Copy and paste your Application Insights connection string to the file. Please refer to the [example file](./.env.example).
3. Activate your python virtual environment, and then run `python main.py`.

> This will output the Operation/Trace ID, which can be used later in Application Insights for searching the operation.

## Application Insights/Azure Monitor

### Logs and traces

Go to your Application Insights instance, click on _Transaction search_ on the left menu. Use the operation id output by the program to search for the logs and traces associated with the operation. Click on any of the search result to view the end-to-end transaction details. Read more [here](https://learn.microsoft.com/en-us/azure/azure-monitor/app/transaction-search-and-diagnostics?tabs=transaction-search).

### Metrics

Running the application once will only generate one set of measurements (for each metrics). Run the application a couple times to generate more sets of measurements.

> Note: Make sure not to run the program too frequently. Otherwise, you may get throttled.

Please refer to here on how to analyze metrics in [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/analyze-metrics).