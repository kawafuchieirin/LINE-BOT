"""
Ingredient storage service for DynamoDB operations
"""
import boto3
import json
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError

class IngredientStorage:
    """Service for managing ingredient storage in DynamoDB"""
    
    def __init__(self):
        """Initialize DynamoDB client"""
        self.dynamodb = boto3.client('dynamodb')
        self.table_name = 'DinnerBotIngredients'
    
    def get_ingredients(self, user_id: str) -> List[str]:
        """Get stored ingredients for a user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of ingredients for the user
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'user_id': {'S': user_id}
                }
            )
            
            if 'Item' in response and 'ingredients' in response['Item']:
                # Extract ingredients from DynamoDB format
                ingredients = []
                if 'L' in response['Item']['ingredients']:
                    for item in response['Item']['ingredients']['L']:
                        if 'S' in item:
                            ingredients.append(item['S'])
                return ingredients
            
            return []
            
        except ClientError as e:
            print(f"Error getting ingredients for user {user_id}: {str(e)}")
            return []
    
    def add_ingredients(self, user_id: str, new_ingredients: List[str]) -> bool:
        """Add ingredients to user's storage
        
        Args:
            user_id: Unique identifier for the user
            new_ingredients: List of ingredients to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing ingredients
            current_ingredients = self.get_ingredients(user_id)
            
            # Merge with new ingredients (avoid duplicates)
            all_ingredients = list(set(current_ingredients + new_ingredients))
            
            # Save to DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'user_id': {'S': user_id},
                    'ingredients': {
                        'L': [{'S': ingredient} for ingredient in all_ingredients]
                    }
                }
            )
            
            return True
            
        except ClientError as e:
            print(f"Error adding ingredients for user {user_id}: {str(e)}")
            return False
    
    def clear_ingredients(self, user_id: str) -> bool:
        """Clear all ingredients for a user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.dynamodb.delete_item(
                TableName=self.table_name,
                Key={
                    'user_id': {'S': user_id}
                }
            )
            return True
            
        except ClientError as e:
            print(f"Error clearing ingredients for user {user_id}: {str(e)}")
            return False
    
    def format_ingredients_list(self, ingredients: List[str]) -> str:
        """Format ingredients list for display
        
        Args:
            ingredients: List of ingredients
            
        Returns:
            Formatted string for display
        """
        if not ingredients:
            return "🆕 冷蔵庫は空っぽです。`/dinner add 食材名` で食材を追加しましょう！"
        
        formatted_list = "❄️ 冷蔵庫の食材:\n"
        for idx, ingredient in enumerate(ingredients, 1):
            formatted_list += f"{idx}. {ingredient}\n"
        
        return formatted_list.strip()