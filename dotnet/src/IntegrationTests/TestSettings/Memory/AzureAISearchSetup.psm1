# Copyright (c) Microsoft. All rights reserved.

# This module requires powershell 7 and the Az and Az.Search modules. You may need to import Az and install Az.Search.
# Import-Module -Name Az
# Install-Module -Name Az.Search

# Before running any of the functions you will need to connect to your azure account and pick the appropriate subscription.
# Connect-AzAccount
# Select-AzSubscription -SubscriptionName "My Dev Subscription"

$resourceGroup = "sk-integration-test-infra"
$aiSearchResourceName = "aisearch-integration-test-basic"

<#
.SYNOPSIS
    Setup the infra required for Azure AI Search Integration tests,
    retrieve the connection information for it, and update the secrets
    store with these settings.

.Parameter OverrideResourceGroup
    Optional override resource group name if the default doesn't work.

.Parameter OverrideAISearchResourceName
    Optional override ai search resource name if the default doesn't work.
#>
function New-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
    # Create the resource group if it doesn't exist.
    Get-AzResourceGroup -Name $overrideResourceGroup -ErrorVariable notPresent -ErrorAction SilentlyContinue
    if ($notPresent) {
        Write-Host "Resource Group does not exist, creating '$overrideResourceGroup' ..."
        New-AzResourceGroup -Name $overrideResourceGroup -Location "North Europe"
    }

    # Create the ai search service if it doesn't exist.
    $service = Get-AzSearchService -ResourceGroupName $resourceGroup -Name $aiSearchResourceName
    if (-not $service) {
        Write-Host "Service does not exist, creating '$overrideAISearchResourceName' ..."
        New-AzSearchService -ResourceGroupName $overrideResourceGroup -Name $overrideAISearchResourceName -Sku "Basic" -Location "North Europe" -PartitionCount 1 -ReplicaCount 1 -HostingMode Default
    }

    # Set the required local secrets.
    Set-AzureAISearchIntegrationInfraUserSecrets -OverrideResourceGroup $overrideResourceGroup -OverrideAISearchResourceName $overrideAISearchResourceName
}

<#
.SYNOPSIS
    Set the user secrets required to run the Azure AI Search integration tests.

.Parameter OverrideResourceGroup
    Optional override resource group name if the default doesn't work.

.Parameter OverrideAISearchResourceName
    Optional override ai search resource name if the default doesn't work.
#>
function Set-AzureAISearchIntegrationInfraUserSecrets($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
    # Set the required local secrets.
    $keys = Get-AzSearchAdminKeyPair -ResourceGroupName $overrideResourceGroup -ServiceName $overrideAISearchResourceName
    dotnet user-secrets set "AzureAISearch:ServiceUrl" "https://$overrideAISearchResourceName.search.windows.net" --project ../../IntegrationTests.csproj
    dotnet user-secrets set "AzureAISearch:ApiKey" $keys.Primary --project ../../IntegrationTests.csproj
}

<#
.SYNOPSIS
    Tear down the infra required for Azure AI Search Integration tests.

.Parameter OverrideResourceGroup
    Optional override resource group name if the default doesn't work.

.Parameter OverrideAISearchResourceName
    Optional override ai search resource name if the default doesn't work.
#>
function Remove-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
    Remove-AzSearchService -ResourceGroupName $overrideResourceGroup -Name $overrideAISearchResourceName
}