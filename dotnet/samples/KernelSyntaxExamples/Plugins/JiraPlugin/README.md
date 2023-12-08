# Jira Open Api Schema

We have our own curated version of the Jira Open Api schema because the one available online
at https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json,
doesn't follow OpenApi specification for all of its operations. For example CreateIssueV2, its body param does not describe properties
and so we can't build the body automatically.
