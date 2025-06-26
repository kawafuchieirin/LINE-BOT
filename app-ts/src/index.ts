import { APIGatewayProxyEvent, APIGatewayProxyResult, Context } from 'aws-lambda';
import { RecipeService } from './services/recipeService';

/**
 * Lambda handler using claude-code-sdk-ts for recipe generation
 */
export const handler = async (
  event: APIGatewayProxyEvent,
  context: Context
): Promise<APIGatewayProxyResult> => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  try {
    // Parse request body
    const body = JSON.parse(event.body || '{}');
    const { userInput, channel, userId } = body;
    
    if (!userInput) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'userInput is required'
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      };
    }
    
    // Create recipe service instance
    const recipeService = new RecipeService();
    
    // Generate recipe
    const result = await recipeService.generateRecipe(userInput);
    
    // Log the result for debugging
    console.log('Recipe generation result:', JSON.stringify(result, null, 2));
    
    // Return success response
    return {
      statusCode: 200,
      body: JSON.stringify({
        success: result.success,
        recipes: result.recipes,
        inputType: result.inputType,
        error: result.error,
        channel,
        userId
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
  } catch (error) {
    console.error('Error in handler:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    };
  }
};