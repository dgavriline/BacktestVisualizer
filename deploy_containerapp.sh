#!/bin/bash

# Load environment variables
source .env

# Fail fast on errors
set -e

echo "Getting ACR credentials..."
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

echo "Building Docker image..."
docker build -t $IMAGE_NAME . -f backend/Dockerfile

echo "Tagging image..."
docker tag $IMAGE_NAME $ACR_NAME.azurecr.io/$IMAGE_NAME

echo "Pushing image to ACR..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME

echo "Creating Container App Environment (if not exists)..."
az containerapp env create \
  --name $ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION || true

echo "Deploying Container App..."
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENV_NAME \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --query properties.configuration.ingress.fqdn

echo "Done!"
