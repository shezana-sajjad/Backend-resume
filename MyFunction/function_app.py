import azure.functions as func
import logging
from azure.cosmos import CosmosClient, exceptions
import os
import json

# Initialize the Cosmos DB client with your credentials
cosmos_endpoint = 'https://shez.documents.azure.com:443/'  # Your Cosmos DB endpoint
cosmos_key = 'AZURE_COSMOSDB_KEY'  # Your Cosmos DB key
database_name = 'visit-counter'  # Your database name
container_name = 'count'  # Your container name

# Create a Cosmos DB client
client = CosmosClient(cosmos_endpoint, cosmos_key)

# Get the database and container clients
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)  # Set to ANONYMOUS

@app.route(route="visitor-counter")
def visitor_counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing visitor count request.')

    try:
        # Check if the visitor count item exists
        try:
            visitor_count_item = container.read_item(item='visitor_count', partition_key='visitor_count')
            visitor_count = visitor_count_item['count']
        except exceptions.CosmosResourceNotFoundError:
            # If the item does not exist, start the count at 0
            visitor_count = 0

        # Increment the visitor count
        visitor_count += 1

        # Upsert the new count into Cosmos DB
        container.upsert_item({
            'id': 'visitor_count',  # Unique ID for the document
            'count': visitor_count
        })

        # Prepare the response data
        response_data = {
            'count': visitor_count
        }

        # Return the visitor count as JSON
        return func.HttpResponse(
            json.dumps(response_data),
            mimetype="application/json",
            status_code=200
        )

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Error storing item in Cosmos DB: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to update the visitor count in Cosmos DB."}),
            mimetype="application/json",
            status_code=500
        )
