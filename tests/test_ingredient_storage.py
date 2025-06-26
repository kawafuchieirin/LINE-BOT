"""
Test cases for ingredient storage functionality
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch, MagicMock
from app.ingredient_storage import IngredientStorage


class TestIngredientStorage(unittest.TestCase):
    """Test cases for IngredientStorage class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_dynamodb = Mock()
        
        # Patch boto3.client to return our mock
        patcher = patch('app.ingredient_storage.boto3.client')
        self.mock_boto3_client = patcher.start()
        self.mock_boto3_client.return_value = self.mock_dynamodb
        self.addCleanup(patcher.stop)
        
        self.storage = IngredientStorage()
        self.test_user_id = "U12345678"
    
    def test_get_ingredients_empty(self):
        """Test getting ingredients when none are stored"""
        # Mock empty response
        self.mock_dynamodb.get_item.return_value = {}
        
        result = self.storage.get_ingredients(self.test_user_id)
        
        self.assertEqual(result, [])
        self.mock_dynamodb.get_item.assert_called_once_with(
            TableName='DinnerBotIngredients',
            Key={'user_id': {'S': self.test_user_id}}
        )
    
    def test_get_ingredients_with_data(self):
        """Test getting ingredients when data exists"""
        # Mock response with ingredients
        self.mock_dynamodb.get_item.return_value = {
            'Item': {
                'user_id': {'S': self.test_user_id},
                'ingredients': {
                    'L': [
                        {'S': 'キャベツ'},
                        {'S': '鶏肉'},
                        {'S': 'にんじん'}
                    ]
                }
            }
        }
        
        result = self.storage.get_ingredients(self.test_user_id)
        
        self.assertEqual(result, ['キャベツ', '鶏肉', 'にんじん'])
    
    def test_add_ingredients_new_user(self):
        """Test adding ingredients for a new user"""
        # Mock get_item to return empty (new user)
        self.mock_dynamodb.get_item.return_value = {}
        
        # Mock put_item to succeed
        self.mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = self.storage.add_ingredients(self.test_user_id, ['キャベツ', '鶏肉'])
        
        self.assertTrue(result)
        self.mock_dynamodb.put_item.assert_called_once()
        
        # Check the put_item call arguments
        put_call_args = self.mock_dynamodb.put_item.call_args[1]
        self.assertEqual(put_call_args['TableName'], 'DinnerBotIngredients')
        self.assertEqual(put_call_args['Item']['user_id']['S'], self.test_user_id)
        
        # Check ingredients (order might vary due to set conversion)
        ingredients = [item['S'] for item in put_call_args['Item']['ingredients']['L']]
        self.assertIn('キャベツ', ingredients)
        self.assertIn('鶏肉', ingredients)
    
    def test_add_ingredients_existing_user(self):
        """Test adding ingredients to existing user's list"""
        # Mock get_item to return existing ingredients
        self.mock_dynamodb.get_item.return_value = {
            'Item': {
                'user_id': {'S': self.test_user_id},
                'ingredients': {
                    'L': [{'S': 'キャベツ'}]
                }
            }
        }
        
        # Mock put_item to succeed
        self.mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = self.storage.add_ingredients(self.test_user_id, ['鶏肉', 'にんじん'])
        
        self.assertTrue(result)
        
        # Check that all ingredients are included (no duplicates)
        put_call_args = self.mock_dynamodb.put_item.call_args[1]
        ingredients = [item['S'] for item in put_call_args['Item']['ingredients']['L']]
        self.assertEqual(len(ingredients), 3)
        self.assertIn('キャベツ', ingredients)
        self.assertIn('鶏肉', ingredients)
        self.assertIn('にんじん', ingredients)
    
    def test_add_ingredients_duplicate_handling(self):
        """Test that duplicate ingredients are not added"""
        # Mock get_item to return existing ingredients
        self.mock_dynamodb.get_item.return_value = {
            'Item': {
                'user_id': {'S': self.test_user_id},
                'ingredients': {
                    'L': [{'S': 'キャベツ'}, {'S': '鶏肉'}]
                }
            }
        }
        
        # Mock put_item to succeed
        self.mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = self.storage.add_ingredients(self.test_user_id, ['キャベツ', 'にんじん'])
        
        self.assertTrue(result)
        
        # Check that キャベツ is not duplicated
        put_call_args = self.mock_dynamodb.put_item.call_args[1]
        ingredients = [item['S'] for item in put_call_args['Item']['ingredients']['L']]
        self.assertEqual(len(ingredients), 3)  # Should have 3 unique ingredients
        self.assertEqual(ingredients.count('キャベツ'), 1)  # No duplicates
    
    def test_clear_ingredients(self):
        """Test clearing ingredients for a user"""
        # Mock delete_item to succeed
        self.mock_dynamodb.delete_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = self.storage.clear_ingredients(self.test_user_id)
        
        self.assertTrue(result)
        self.mock_dynamodb.delete_item.assert_called_once_with(
            TableName='DinnerBotIngredients',
            Key={'user_id': {'S': self.test_user_id}}
        )
    
    def test_format_ingredients_list_empty(self):
        """Test formatting empty ingredients list"""
        result = self.storage.format_ingredients_list([])
        self.assertEqual(result, "現在登録されている食材はありません。")
    
    def test_format_ingredients_list_with_items(self):
        """Test formatting ingredients list with items"""
        ingredients = ['キャベツ', '鶏肉', 'にんじん']
        result = self.storage.format_ingredients_list(ingredients)
        
        expected = "📋 登録済み食材:\n1. キャベツ\n2. 鶏肉\n3. にんじん"
        self.assertEqual(result, expected)
    
    def test_error_handling_get_ingredients(self):
        """Test error handling in get_ingredients"""
        from botocore.exceptions import ClientError
        
        # Mock ClientError
        self.mock_dynamodb.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetItem'
        )
        
        result = self.storage.get_ingredients(self.test_user_id)
        
        # Should return empty list on error
        self.assertEqual(result, [])
    
    def test_error_handling_add_ingredients(self):
        """Test error handling in add_ingredients"""
        from botocore.exceptions import ClientError
        
        # Mock get_item to succeed but put_item to fail
        self.mock_dynamodb.get_item.return_value = {}
        self.mock_dynamodb.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}},
            'PutItem'
        )
        
        result = self.storage.add_ingredients(self.test_user_id, ['キャベツ'])
        
        # Should return False on error
        self.assertFalse(result)
    
    def test_error_handling_clear_ingredients(self):
        """Test error handling in clear_ingredients"""
        from botocore.exceptions import ClientError
        
        # Mock ClientError
        self.mock_dynamodb.delete_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}},
            'DeleteItem'
        )
        
        result = self.storage.clear_ingredients(self.test_user_id)
        
        # Should return False on error
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()