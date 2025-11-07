#!/bin/bash

# Test assistant editing functionality specifically
# Usage: ./test-assistant-editing-debug.sh

set -e

echo "🔧 Testing assistant editing functionality with debug info..."

# Check if using nginx or direct configuration
if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
    echo "🌐 Using Nginx configuration..."
    API_URL="http://188.225.56.200/api"
else
    echo "🔗 Using direct configuration..."
    API_URL="http://188.225.56.200:8000"
fi

# Test assistants endpoint
echo "📊 Testing assistants endpoint..."
if curl -s "$API_URL/assistants" > /dev/null; then
    echo "✅ Assistants endpoint is working"
    
    # Get list of assistants
    echo "📋 Available assistants:"
    curl -s "$API_URL/assistants" | jq -r '.[] | "  - \(.name) (ID: \(.id))"' 2>/dev/null || echo "  Assistants loaded successfully"
    
    # Test creating a test assistant
    echo "🤖 Creating test assistant for editing..."
    TEST_ASSISTANT='{
        "name": "Debug Test Assistant",
        "description": "Test assistant for debugging edit functionality",
        "system_prompt": "You are a test assistant for debugging.",
        "model": "gpt-4o-mini",
        "temperature": "0.7",
        "max_tokens": 1000
    }'
    
    CREATE_RESPONSE=$(curl -s -X POST "$API_URL/assistants" \
        -H "Content-Type: application/json" \
        -d "$TEST_ASSISTANT")
    
    if echo "$CREATE_RESPONSE" | jq -e '.id' > /dev/null; then
        ASSISTANT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
        echo "✅ Test assistant created with ID: $ASSISTANT_ID"
        
        # Get the assistant details
        echo "🔍 Getting assistant details..."
        ASSISTANT_DETAILS=$(curl -s "$API_URL/assistants/$ASSISTANT_ID")
        echo "Original assistant:"
        echo "$ASSISTANT_DETAILS" | jq -r '"  Name: " + .name + "\n  Description: " + .description + "\n  Model: " + .model + "\n  Temperature: " + .temperature + "\n  Max tokens: " + (.max_tokens | tostring)'
        
        # Test updating the assistant
        echo "✏️ Testing assistant update..."
        UPDATE_DATA='{
            "name": "Updated Debug Test Assistant",
            "description": "Updated test assistant for debugging edit functionality",
            "system_prompt": "You are an updated test assistant for debugging.",
            "model": "claude-3-5-haiku-20241022",
            "temperature": "0.3",
            "max_tokens": 2000
        }'
        
        echo "Sending update data:"
        echo "$UPDATE_DATA" | jq .
        
        UPDATE_RESPONSE=$(curl -s -X PUT "$API_URL/assistants/$ASSISTANT_ID" \
            -H "Content-Type: application/json" \
            -d "$UPDATE_DATA")
        
        echo "Update response:"
        echo "$UPDATE_RESPONSE" | jq . 2>/dev/null || echo "$UPDATE_RESPONSE"
        
        if echo "$UPDATE_RESPONSE" | jq -e '.id' > /dev/null; then
            echo "✅ Assistant updated successfully"
            
            # Verify the update
            echo "🔍 Verifying update..."
            UPDATED_ASSISTANT=$(curl -s "$API_URL/assistants/$ASSISTANT_ID")
            echo "Updated assistant details:"
            echo "$UPDATED_ASSISTANT" | jq -r '"  Name: " + .name + "\n  Description: " + .description + "\n  Model: " + .model + "\n  Temperature: " + .temperature + "\n  Max tokens: " + (.max_tokens | tostring)'
            
            # Test partial update
            echo "🔄 Testing partial update..."
            PARTIAL_UPDATE='{
                "name": "Partially Updated Assistant",
                "temperature": "0.9"
            }'
            
            PARTIAL_RESPONSE=$(curl -s -X PUT "$API_URL/assistants/$ASSISTANT_ID" \
                -H "Content-Type: application/json" \
                -d "$PARTIAL_UPDATE")
            
            if echo "$PARTIAL_RESPONSE" | jq -e '.id' > /dev/null; then
                echo "✅ Partial update successful"
                echo "Partially updated assistant:"
                echo "$PARTIAL_RESPONSE" | jq -r '"  Name: " + .name + "\n  Description: " + .description + "\n  Model: " + .model + "\n  Temperature: " + .temperature + "\n  Max tokens: " + (.max_tokens | tostring)'
            else
                echo "❌ Partial update failed"
                echo "Response: $PARTIAL_RESPONSE"
            fi
            
            # Clean up - delete test assistant
            echo "🧹 Cleaning up test assistant..."
            DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/assistants/$ASSISTANT_ID")
            echo "✅ Test assistant deleted"
        else
            echo "❌ Failed to update assistant"
            echo "Response: $UPDATE_RESPONSE"
            
            # Check if it's a validation error
            if echo "$UPDATE_RESPONSE" | grep -q "validation error"; then
                echo "🔍 This might be a validation error. Check the data format."
            fi
        fi
    else
        echo "❌ Failed to create test assistant"
        echo "Response: $CREATE_RESPONSE"
    fi
else
    echo "❌ Assistants endpoint not responding"
    echo "Checking backend logs..."
    if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.nginx.yml logs backend | tail -10
    else
        docker-compose logs backend | tail -10
    fi
fi

echo ""
echo "✅ Assistant editing debug test complete!"
echo ""
echo "🔍 If editing still doesn't work in the UI:"
echo "  1. Check browser console for JavaScript errors"
echo "  2. Check network tab for failed API requests"
echo "  3. Verify the assistant ID is correct"
echo "  4. Check if the form data is being sent correctly"
echo ""
echo "🌐 Access your application:"
if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
    echo "  Frontend: http://188.225.56.200"
    echo "  API: http://188.225.56.200/api"
else
    echo "  Frontend: http://188.225.56.200:3000"
    echo "  API: http://188.225.56.200:8000"
fi
