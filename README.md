# BacktestVisualizer
A tool that will let users backtest and visualize algotrading strategies

VENV startup: 

source $(poetry env info --path)/bin/activate

How to test: 

1) from root directory:
# Build the container
docker build -t backtest-api . -f backend/Dockerfile

# Run the container
docker run -p 8000:8000 backtest-api

2) http://localhost:8000/docs#/default/run_backtest_run_backtest_post

- "Try it out" button
- paste in test JSON:

{
  "start": "2022-01-03",
  "end": "2025-04-01",
  "dip_threshold": 0.25,
  "gain_threshold": 0.10,
  "hold_days": 5,
  "initial_cash": 1000000,
  "max_alloc_amount": 10000,
  "dip_lookback_days": 30
}

3) for end to end test: 
- run docker container
- split terminal
- in second terminal run: 
    streamlit run app.py
- set params and click run backtest

Setting up azure container:

1) Make sure variables defined in .env and .env is in root directory

2) Run deploy.sh. (Make executable using <chmod +x deploy.sh> if necessary)

3) If login error wait a few seconds then try: <az acr login --name backtestacr>

4) Build, tag and push the dockerfile:

# In your project root
docker build -t backtest-api . -f backend/Dockerfile

# Tag it for ACR
docker tag backtest-api backtestacr.azurecr.io/backtest-api

# Push it to ACR
docker push backtestacr.azurecr.io/backtest-api

5) If an authorization error occurs, manually check:
az acr credential show --name backtestacr

copy the password, and enter in:
docker login backtestacr.azurecr.io -u backtestacr -p XXXXXXXXXXXXX

6) Retry the push:
docker tag backtest-api backtestacr.azurecr.io/backtest-api
docker push backtestacr.azurecr.io/backtest-api

7) Check deploy_containerapp.sh, then:
chmod +x deploy_containerapp.sh
./deploy_containerapp.sh

NOTE: If using a mac, docker will deploy the container using arm64 instead of the linux/amd64 expected by azure
can be fixed using: 
docker buildx create --name mybuilder --use
docker buildx inspect mybuilder --bootstrap

docker buildx build --platform linux/amd64 \
  -t backtestacr.azurecr.io/backtest-api \
  -f backend/Dockerfile \
  --push .

and then redeploy:

az containerapp update \
  --name backtest-api-app \
  --resource-group BacktestGroup \
  --image backtestacr.azurecr.io/backtest-api


NOTE 2: If after running <streamlit run app.py> there's an error pertaining to lack of public permissions

run:
az containerapp ingress enable \
  --name backtest-api-app \
  --resource-group BacktestGroup \
  --type external

response will look like this:
Ingress enabled. Access your app at https://backtest-api-app.icymoss-e1d44fae.eastus.azurecontainerapps.io/
copy that url into the app.py file and rerun the streamlit app

(PUBICLY ACCESSBLE APPS WILL RETURN A URL, if response is null it didn't work)


======================== MOVING FORWARD ========================
When changes are made to any of the affected files the docker image needs to be rebuilt and pushed to ACR:

1) Rebuild (Make sure to use linux/amd64):
docker buildx build \
  --platform linux/amd64 \
  -t backtest-api . -f backend/Dockerfile \
  --load

2) Tag for ACR:
docker tag backtest-api backtestacr.azurecr.io/backtest-api

3) Push to ACR:
docker push backtestacr.azurecr.io/backtest-api

4) Update azure container to use latest image:
az containerapp update \
  --name backtest-api-app \
  --resource-group BacktestGroup \
  --image backtestacr.azurecr.io/backtest-api


In case of errors when testing use this to check logs:
az containerapp logs show \
  --name backtest-api-app \
  --resource-group BacktestGroup \
  --follow


Stopping and restarting the container:

Stop: 
az containerapp stop \
  --name backtest-api-app \
  --resource-group BacktestGroup

Start: 
az containerapp start \
  --name backtest-api-app \
  --resource-group BacktestGroup