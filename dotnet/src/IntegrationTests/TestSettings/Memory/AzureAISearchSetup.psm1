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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Write-Information "Resource Group does not exist, creating '$overrideResourceGroup' ..."
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Write-Information "Resource Group does not exist, creating '$overrideResourceGroup' ..."
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        Write-Information "Resource Group does not exist, creating '$overrideResourceGroup' ..."
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Write-Information "Resource Group does not exist, creating '$overrideResourceGroup' ..."
=======
        Write-Host "Resource Group does not exist, creating '$overrideResourceGroup' ..."
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        New-AzResourceGroup -Name $overrideResourceGroup -Location "North Europe"
    }

    # Create the ai search service if it doesn't exist.
    $service = Get-AzSearchService -ResourceGroupName $resourceGroup -Name $aiSearchResourceName
    if (-not $service) {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Write-Output "Service does not exist, creating '$overrideAISearchResourceName' ..."
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Write-Output "Service does not exist, creating '$overrideAISearchResourceName' ..."
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        Write-Output "Service does not exist, creating '$overrideAISearchResourceName' ..."
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Write-Output "Service does not exist, creating '$overrideAISearchResourceName' ..."
=======
        Write-Host "Service does not exist, creating '$overrideAISearchResourceName' ..."
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
[CmdletBinding(SupportsShouldProcess)] function Set-AzureAISearchIntegrationInfraUserSecrets($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
[CmdletBinding(SupportsShouldProcess)] function Set-AzureAISearchIntegrationInfraUserSecrets($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
[CmdletBinding(SupportsShouldProcess)] function Set-AzureAISearchIntegrationInfraUserSecrets($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
[CmdletBinding(SupportsShouldProcess)] function Set-AzureAISearchIntegrationInfraUserSecrets($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
function Set-AzureAISearchIntegrationInfraUserSecrets($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
[CmdletBinding(SupportsShouldProcess)] function Remove-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
[CmdletBinding(SupportsShouldProcess)] function Remove-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
[CmdletBinding(SupportsShouldProcess)] function Remove-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
[CmdletBinding(SupportsShouldProcess)] function Remove-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
=======
function Remove-AzureAISearchIntegrationInfra($overrideResourceGroup = $resourceGroup, $overrideAISearchResourceName = $aiSearchResourceName) {
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    Remove-AzSearchService -ResourceGroupName $overrideResourceGroup -Name $overrideAISearchResourceName
}