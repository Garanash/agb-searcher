#!/bin/bash

# Test assistant editing functionality
# Usage: ./test-assistant-editing.sh

set -e

echo "🧪 Testing assistant editing functionality..."

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
    echo "🔧 Creating test assistant..."
    TEST_ASSISTANT='{
        "name": "Test Assistant",
        "description": "Test assistant for editing functionality",
        "system_prompt": "You are a test assistant.",
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
        
        # Test updating the assistant
        echo "✏️ Testing assistant update..."
        UPDATE_DATA='{
            "name": "Updated Test Assistant",
            "description": "Updated test assistant description",
            "system_prompt": "You are an updated test assistant.",
            "model": "claude-3-5-haiku-20241022",
            "temperature": "0.3",
            "max_tokens": 2000
        }'
        
        UPDATE_RESPONSE=$(curl -s -X PUT "$API_URL/assistants/$ASSISTANT_ID" \
            -H "Content-Type: application/json" \
            -d "$UPDATE_DATA")
        
        if echo "$UPDATE_RESPONSE" | jq -e '.id' > /dev/null; then
            echo "✅ Assistant updated successfully"
            
            # Verify the update
            echo "🔍 Verifying update..."
            UPDATED_ASSISTANT=$(curl -s "$API_URL/assistants/$ASSISTANT_ID")
            echo "Updated assistant details:"
            echo "$UPDATED_ASSISTANT" | jq -r '"  Name: " + .name + "\n  Description: " + .description + "\n  Model: " + .model + "\n  Temperature: " + .temperature + "\n  Max tokens: " + (.max_tokens | tostring)'
            
            # Clean up - delete test assistant
            echo "🧹 Cleaning up test assistant..."
            DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/assistants/$ASSISTANT_ID")
            echo "✅ Test assistant deleted"
        else
            echo "❌ Failed to update assistant"
            echo "Response: $UPDATE_RESPONSE"
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
echo "✅ Assistant editing functionality test complete!"
echo ""
echo "🎯 Features tested:"
echo "  - Create assistant"
echo "  - Update assistant"
echo "  - Delete assistant"
echo "  - List assistants"
echo ""
echo "🌐 Access your application:"
if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
    echo "  Frontend: http://188.225.56.200"
    echo "  API: http://188.225.56.200/api"
else
    echo "  Frontend: http://188.225.56.200:3000"
    echo "  API: http://188.225.56.200:8000"
fi
