#!/bin/bash

set -e  # Stop if any command fails

# Load .env variables
source .env

# Tags for required policies (adjust as needed)
TAGS="owner=dennis autokillDays=7 reason=project"

echo "Creating Resource Group: $RESOURCE_GROUP"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags $TAGS

echo "Creating Azure Container Registry: $ACR_NAME"
az acr create \
  --name "$ACR_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku Basic \
  --admin-enabled true

echo "Getting ACR credentials..."
ACR_USER=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)

echo "Building Docker image..."
docker build -t backtest-api . -f backend/Dockerfile

echo "Tagging image for ACR..."
docker tag backtest-api "$ACR_NAME.azurecr.io/backtest-api"

echo "Pushing image to ACR..."
docker push "$ACR_NAME.azurecr.io/backtest-api"

echo "Creating Container Apps environment (if not exists)..."
az containerapp env create \
  --name backtest-env \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --logs-destination none

echo "Deploying Azure Container App..."
az containerapp create \
  --name backtest-api-app \
  --resource-group "$RESOURCE_GROUP" \
  --environment backtest-env \
  --image "$ACR_NAME.azurecr.io/backtest-api" \
  --registry-server "$ACR_NAME.azurecr.io" \
  --registry-username "$ACR_USER" \
  --registry-password "$ACR_PASS" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1

echo "Deployment complete!"

echo -n "App URL: "
az containerapp show \
  --name backtest-api-app \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn \
  -o tsv
