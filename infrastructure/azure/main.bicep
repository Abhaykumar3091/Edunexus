// UniAssist AI - Azure Infrastructure as Code (Bicep Template)
// Configured specifically for Azure Student Subscription & Cost Optimization

@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Environment name prefix')
param environmentName string = 'uniassist'

@description('PostgreSQL administrator login name')
param pgAdminUsername string = 'uniassist_admin'

@secure()
@description('PostgreSQL administrator password')
param pgAdminPassword string

// 1. Log Analytics & Application Insights (0.5GB daily cap)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${environmentName}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: json('0.5')
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${environmentName}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// 2. Azure Storage Account for University Documents
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${environmentName}${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource docContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'university-documents'
  properties: {
    publicAccess: 'None'
  }
}

// 3. Azure AI Search Service (Basic Tier for RAG)
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: 'search-${environmentName}-${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    semanticSearch: 'free'
  }
}

// 4. Azure Database for PostgreSQL (Flexible Server - Burstable B1ms)
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: 'psql-${environmentName}-${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: pgAdminUsername
    administratorLoginPassword: pgAdminPassword
    version: '16'
    storage: {
      storageSizeGB: 32
      autoGrow: 'Disabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

output storageAccountName string = storageAccount.name
output searchServiceName string = searchService.name
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
