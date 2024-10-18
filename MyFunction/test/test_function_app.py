import unittest
from unittest.mock import patch, MagicMock
from azure.functions import HttpRequest
import json
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError  # Import the correct exceptions
from function_app import visitor_counter  # Assuming your function is named visitor_counter

class TestVisitorCounterFunction(unittest.TestCase):

    @patch('function_app.container')  # Mock the Cosmos DB container
    def test_visitor_counter_first_visit(self, mock_container):
        """Test the case where there is no existing visitor count (first visit)."""
        
        # Mock Cosmos DB read_item to raise a CosmosResourceNotFoundError
        mock_container.read_item.side_effect = CosmosResourceNotFoundError  # Use the correct exception
        
        # Mock the upsert_item method
        mock_container.upsert_item = MagicMock()
        
        # Create an HTTP request (empty, since it doesn't depend on the body)
        req = HttpRequest(
            method='GET',
            url='/api/visitor-counter',
            body=None
        )

        # Call the function
        response = visitor_counter(req)
        
        # Assert the status code and response content
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.get_body())
        self.assertEqual(response_data['count'], 1)  # Since it's the first visit
        
        # Ensure upsert_item was called to insert the count
        mock_container.upsert_item.assert_called_with({'id': 'visitor_count', 'count': 1})

    @patch('function_app.container')  # Mock the Cosmos DB container
    def test_visitor_counter_subsequent_visit(self, mock_container):
        """Test the case where there is an existing visitor count (subsequent visit)."""
        
        # Mock Cosmos DB to return an existing visitor count
        mock_container.read_item.return_value = {'id': 'visitor_count', 'count': 10}
        
        # Mock the upsert_item method
        mock_container.upsert_item = MagicMock()
        
        # Create an HTTP request
        req = HttpRequest(
            method='GET',
            url='/api/visitor-counter',
            body=None
        )

        # Call the function
        response = visitor_counter(req)
        
        # Assert the status code and response content
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.get_body())
        self.assertEqual(response_data['count'], 11)  # Since the previous count was 10
        
        # Ensure upsert_item was called to update the count
        mock_container.upsert_item.assert_called_with({'id': 'visitor_count', 'count': 11})

    @patch('function_app.container')  # Mock the Cosmos DB container
    def test_visitor_counter_cosmos_error(self, mock_container):
        """Test the case where Cosmos DB raises an error during the request."""
        
        # Mock Cosmos DB to raise a CosmosHttpResponseError
        mock_container.read_item.side_effect = CosmosHttpResponseError  # Use the correct exception
        
        # Create an HTTP request
        req = HttpRequest(
            method='GET',
            url='/api/visitor-counter',
            body=None
        )

        # Call the function
        response = visitor_counter(req)
        
        # Assert the status code and response content
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.get_body())
        self.assertEqual(response_data['error'], "Failed to update the visitor count in Cosmos DB.")

if __name__ == '__main__':
    unittest.main()
