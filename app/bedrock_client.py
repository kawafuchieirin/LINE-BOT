"""
AWS Bedrock クライアントユーティリティ
"""
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockClient:
    """AWS Bedrockとの通信を管理するクライアント"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        BedrockClientの初期化
        
        Args:
            region_name: AWSリージョン名
        """
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def generate_recipe_suggestion(
        self, 
        user_input: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        ユーザー入力からレシピを生成（食材ベースまたは気分ベース）
        
        Args:
            user_input: ユーザーからの入力（食材または気分）
            max_tokens: 最大トークン数
            temperature: 生成の多様性（0-1）
            
        Returns:
            生成されたレシピテキスト
        """
        # 入力が気分ベースか食材ベースかを判定
        is_mood_based = self._is_mood_based_input(user_input)
        
        if is_mood_based:
            logger.info(f"Detected mood-based input: {user_input}")
            prompt = self._create_mood_based_prompt(user_input)
        else:
            logger.info(f"Detected ingredient-based input: {user_input}")
            prompt = self._create_recipe_prompt(user_input)
        
        try:
            response = self._invoke_model(prompt, max_tokens, temperature)
            return self._extract_text_from_response(response)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                logger.error("Bedrock API rate limit exceeded")
                return "申し訳ございません。現在アクセスが集中しています。少し時間をおいてからお試しください。"
            elif error_code == 'ModelNotReadyException':
                logger.error("Bedrock model not ready")
                return "申し訳ございません。AIモデルが準備中です。しばらくお待ちください。"
            else:
                logger.error(f"Bedrock API error: {str(e)}")
                return "申し訳ございません。レシピの生成中にエラーが発生しました。"
                
        except Exception as e:
            logger.error(f"Unexpected error in recipe generation: {str(e)}")
            return "申し訳ございません。予期しないエラーが発生しました。"
    
    def _create_recipe_prompt(self, ingredients: str) -> str:
        """
        レシピ生成用のプロンプトを作成
        
        Args:
            ingredients: 食材
            
        Returns:
            プロンプト文字列
        """
        return f"""あなたは優秀な料理アドバイザーです。
以下の食材を使って、美味しい晩御飯のメニューを2-3個提案してください。
各メニューについて、簡単な説明も付けてください。

食材: {ingredients}

提案フォーマット:
🍽️ メニュー提案

1. [メニュー名]
   - 簡単な説明

2. [メニュー名]
   - 簡単な説明

必要に応じて3つ目のメニューも提案してください。
メニュー名は具体的で、作りたくなるような名前にしてください。
説明は1-2文で、調理方法の特徴や味の特徴を含めてください。"""
    
    def _is_mood_based_input(self, user_input: str) -> bool:
        """
        ユーザー入力が気分ベースかどうかを判定
        
        Args:
            user_input: ユーザーからの入力
            
        Returns:
            気分ベースの場合True、食材ベースの場合False
        """
        # 気分を表すキーワードリスト
        mood_keywords = [
            'さっぱり', 'あっさり', 'こってり', 'ガッツリ', 'ヘルシー',
            '夏バテ', '疲れ', 'スタミナ', '温まる', '冷たい',
            '辛い', '甘い', '優しい', '濃厚', 'サッパリ',
            '気分', '食べたい', '系', 'な感じ', '的な',
            '元気', 'パワー', '軽め', '重め', '食欲',
            'がっつり', 'しっかり', 'ボリューム', '満足',
            '和風', '洋風', '中華', 'エスニック', 'イタリアン'
        ]
        
        # 食材を示す否定的なキーワード（これらがある場合は食材ベースの可能性が高い）
        ingredient_indicators = ['と', 'や', '、', 'の', 'が残って', 'がある', 'を使って']
        
        # 入力をlowercaseに変換（ひらがな・カタカナは変換されないが、英語は変換される）
        input_lower = user_input.lower()
        
        # 気分キーワードが含まれているかチェック
        has_mood_keyword = any(keyword in input_lower for keyword in mood_keywords)
        
        # 食材リストの指標が多い場合は食材ベースと判定
        ingredient_count = sum(1 for indicator in ingredient_indicators if indicator in user_input)
        if ingredient_count >= 2:
            return False
        
        # 気分キーワードがあれば気分ベース
        return has_mood_keyword
    
    def _create_mood_based_prompt(self, mood_input: str) -> str:
        """
        気分ベースのレシピ生成用プロンプトを作成
        
        Args:
            mood_input: ユーザーの気分入力
            
        Returns:
            プロンプト文字列
        """
        return f"""あなたはプロの料理アドバイザーです。
ユーザーの今の気分や食べたいものの希望に基づいて、ぴったりの晩御飯メニューを提案してください。

ユーザーの気分・希望: {mood_input}

この気分にぴったり合う晩御飯メニューを2-3個提案してください。
各メニューについて、なぜその気分に合うのか、どんな味わいや特徴があるのかも含めて説明してください。

提案フォーマット:
🍽️ メニュー提案

1. [メニュー名]
   - 簡単な説明（この気分に合う理由、味の特徴、調理のポイントなど）

2. [メニュー名]
   - 簡単な説明（この気分に合う理由、味の特徴、調理のポイントなど）

必要に応じて3つ目のメニューも提案してください。
メニュー名は具体的で、作りたくなるような名前にしてください。
説明は2-3文で、なぜその気分にマッチするかを含めて記載してください。"""
    
    def _invoke_model(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """
        Bedrockモデルを呼び出し
        
        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            
        Returns:
            Bedrockからのレスポンス
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "temperature": temperature,
            "top_p": 0.95
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        return json.loads(response['body'].read())
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Bedrockレスポンスからテキストを抽出
        
        Args:
            response: Bedrockからのレスポンス
            
        Returns:
            抽出されたテキスト
        """
        try:
            return response['content'][0]['text']
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract text from response: {str(e)}")
            raise ValueError("Invalid response format from Bedrock")


def create_bedrock_client(region_name: Optional[str] = None) -> BedrockClient:
    """
    BedrockClientのファクトリ関数
    
    Args:
        region_name: AWSリージョン名（Noneの場合はデフォルトを使用）
        
    Returns:
        BedrockClientインスタンス
    """
    import os
    if region_name is None:
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
    
    return BedrockClient(region_name)