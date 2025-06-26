/**
 * Local test script for the Claude SDK Lambda function
 * Run with: node test-local.js
 */

// Test event that simulates an API Gateway request
const testEvent = {
  version: "2.0",
  routeKey: "POST /claude-sdk",
  rawPath: "/claude-sdk",
  rawQueryString: "",
  headers: {
    "accept": "*/*",
    "content-type": "application/json",
    "host": "localhost:3000",
    "user-agent": "test-client/1.0"
  },
  requestContext: {
    accountId: "123456789012",
    apiId: "test-api",
    domainName: "localhost:3000",
    domainPrefix: "test-api",
    http: {
      method: "POST",
      path: "/claude-sdk",
      protocol: "HTTP/1.1",
      sourceIp: "127.0.0.1",
      userAgent: "test-client/1.0"
    },
    requestId: "test-request-id",
    routeKey: "POST /claude-sdk",
    stage: "test",
    time: new Date().toISOString(),
    timeEpoch: Date.now()
  },
  body: JSON.stringify({
    userInput: "キャベツと鶏むね肉",
    channel: "test",
    userId: "test-user"
  }),
  isBase64Encoded: false
};

// Import and run the handler
async function runTest() {
  try {
    console.log("🧪 Testing Claude SDK Lambda function locally...\n");
    
    // Note: This requires the TypeScript to be compiled first
    const { handler } = require('./dist/index');
    
    console.log("📨 Test Event:", JSON.stringify(testEvent, null, 2));
    console.log("\n⏳ Invoking handler...\n");
    
    const response = await handler(testEvent, {
      functionName: 'test-function',
      functionVersion: '$LATEST',
      invokedFunctionArn: 'arn:aws:lambda:test:123456789012:function:test-function',
      memoryLimitInMB: '512',
      awsRequestId: 'test-request-id',
      logGroupName: '/aws/lambda/test-function',
      logStreamName: '2024/01/01/[$LATEST]test',
      getRemainingTimeInMillis: () => 30000,
      done: () => {},
      fail: () => {},
      succeed: () => {}
    });
    
    console.log("✅ Response:", JSON.stringify(response, null, 2));
    
    if (response.statusCode === 200) {
      const body = JSON.parse(response.body);
      console.log("\n🍽️ Generated Recipes:");
      if (body.recipes && Array.isArray(body.recipes)) {
        body.recipes.forEach(recipe => {
          console.log(`\n${recipe.number}. ${recipe.name}`);
          console.log(`   - ${recipe.description}`);
        });
      }
    }
    
  } catch (error) {
    console.error("❌ Error:", error);
  }
}

// Run the test
runTest();