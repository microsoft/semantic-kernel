/**
 * Generate the structured output response format schema.
 *
 * @param name - The name of the schema
 * @param schema - The JSON schema object
 * @returns The structured output response format schema
 */
export function generateStructuredOutputResponseFormatSchema(
  name: string,
  schema: Record<string, any>
): Record<string, any> {
  return {
    type: 'json_schema',
    json_schema: { name, strict: true, schema },
  }
}
