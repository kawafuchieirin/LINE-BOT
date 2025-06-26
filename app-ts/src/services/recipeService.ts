import { claude } from '@instantlyeasy/claude-code-sdk-ts';

interface Recipe {
  number: string;
  name: string;
  description: string;
}

interface RecipeResult {
  success: boolean;
  recipes: Recipe[] | null;
  error: string | null;
  inputType: 'mood' | 'ingredient';
}

export class RecipeService {
  private moodKeywords = [
    'さっぱり', 'あっさり', 'こってり', 'ガッツリ', 'ヘルシー',
    '夏バテ', '疲れ', 'スタミナ', '温まる', '冷たい', '辛い', '甘い',
    '気分', '食べたい', '系', '元気', '軽め', '重め', '食欲'
  ];

  async generateRecipe(userInput: string): Promise<RecipeResult> {
    try {
      const isMoodBased = this.isMoodBasedInput(userInput);
      const inputType = isMoodBased ? 'mood' : 'ingredient';
      
      // Create appropriate prompt
      const prompt = this.createPrompt(userInput, isMoodBased);
      
      // Use claude-code-sdk-ts to generate response
      const response = await claude()
        .withModel('sonnet')  // Claude 3.5 Sonnet
        .skipPermissions()
        .query(prompt)
        .asText();
      
      // Parse recipes from response
      const recipes = this.parseRecipes(response);
      
      return {
        success: true,
        recipes,
        error: null,
        inputType
      };
      
    } catch (error) {
      console.error('Error generating recipe:', error);
      
      return {
        success: false,
        recipes: null,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        inputType: 'ingredient'
      };
    }
  }

  private isMoodBasedInput(userInput: string): boolean {
    const inputLower = userInput.toLowerCase();
    const hasMoodKeyword = this.moodKeywords.some(keyword => 
      inputLower.includes(keyword)
    );
    
    const ingredientIndicators = ['と', 'や', '、', 'の', 'が残って', 'がある'];
    const ingredientCount = ingredientIndicators.filter(indicator => 
      userInput.includes(indicator)
    ).length;
    
    if (ingredientCount >= 2) {
      return false;
    }
    
    return hasMoodKeyword;
  }

  private createPrompt(userInput: string, isMoodBased: boolean): string {
    if (isMoodBased) {
      return `あなたはプロの料理アドバイザーです。
ユーザーの今の気分や食べたいものの希望に基づいて、ぴったりの晩御飯メニューを提案してください。

ユーザーの気分・希望: ${userInput}

この気分にぴったり合う晩御飯メニューを2-3個提案してください。

提案フォーマット:
1. [メニュー名]
   - 簡単な説明

2. [メニュー名]  
   - 簡単な説明

メニュー名は具体的で、説明は2-3文で記載してください。`;
    } else {
      return `あなたは優秀な料理アドバイザーです。
以下の食材を使って、美味しい晩御飯のメニューを2-3個提案してください。

食材: ${userInput}

提案フォーマット:
1. [メニュー名]
   - 簡単な説明

2. [メニュー名]
   - 簡単な説明

メニュー名は具体的で、説明は1-2文で記載してください。`;
    }
  }

  private parseRecipes(responseText: string): Recipe[] {
    const recipes: Recipe[] = [];
    const pattern = /(\d+)\.\s*(.+?)\n\s*-\s*(.+?)(?=\n\d+\.|$)/gs;
    let match;
    
    while ((match = pattern.exec(responseText)) !== null) {
      recipes.push({
        number: match[1].trim(),
        name: match[2].trim(),
        description: match[3].trim()
      });
    }
    
    // Fallback parsing if no matches
    if (recipes.length === 0) {
      const lines = responseText.split('\n');
      let currentRecipe: Recipe | null = null;
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        const numberMatch = trimmedLine.match(/^(\d+)\./);
        
        if (numberMatch) {
          if (currentRecipe) {
            recipes.push(currentRecipe);
          }
          currentRecipe = {
            number: numberMatch[1],
            name: trimmedLine.replace(/^\d+\.\s*/, ''),
            description: ''
          };
        } else if (trimmedLine.startsWith('-') && currentRecipe) {
          currentRecipe.description = trimmedLine.substring(1).trim();
        }
      }
      
      if (currentRecipe) {
        recipes.push(currentRecipe);
      }
    }
    
    return recipes;
  }
}