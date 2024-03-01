from promptflow import PFClient

pf_client = PFClient()

inputs = {
    "text": "What would you have left if you spent $3 when you only had $2 to begin with"
}  # The inputs of the flow.
flow_result = pf_client.test(flow="perform_math", inputs=inputs)
print(f"Flow outputs: {flow_result}")
