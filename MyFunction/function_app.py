import os
import azure.functions as func
import logging
import json
from azure.cosmos import CosmosClient, exceptions

# Fetch CosmosDB client details from environment variables
endpoint = os.environ.get("AZURE_COSMOSDB_ENDPOINT")
key = os.environ.get("AZURE_COSMOSDB_KEY")

# Debugging: Print environment variables
print("AZURE_COSMOSDB_ENDPOINT:", endpoint)
print("AZURE_COSMOSDB_KEY:", key)

database_name = "VisitorCounterDB"
container_name = "VisitorCount"

client = CosmosClient(endpoint, credential=key)  # Use credential parameter for key
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_triggershez")
def http_triggershez(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    visitor_count = 0
    try:
        visitor_item = container.read_item(item="visitor_count", partition_key="visitor_count")
        visitor_count = visitor_item.get('count', 0)
        visitor_item['count'] = visitor_count + 1
        container.upsert_item(visitor_item)
        visitor_count = visitor_item['count']
    except exceptions.CosmosHttpResponseError:
        visitor_item = {
            'id': 'visitor_count',
            'count': 1
        }
        container.create_item(visitor_item)
        visitor_count = 1

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = None
        if req_body:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(
            json.dumps({"message": f"Hello, {name}. Your name has been added to the database.", "visitor_count": visitor_count}),
            status_code=200,
            mimetype="application/json"
        )
    else:
        return func.HttpResponse(
            json.dumps({"message": "This HTTP triggered function executed successfully.", "visitor_count": visitor_count}),
            status_code=200,
            mimetype="application/json"
        )
