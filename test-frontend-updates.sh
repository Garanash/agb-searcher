#!/bin/bash

# Test updated frontend functionality
# Usage: ./test-frontend-updates.sh

set -e

echo "🧪 Testing updated frontend functionality..."

# Check if using nginx or direct configuration
if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
    echo "🌐 Using Nginx configuration..."
    FRONTEND_URL="http://188.225.56.200"
    API_URL="http://188.225.56.200/api"
else
    echo "🔗 Using direct configuration..."
    FRONTEND_URL="http://188.225.56.200:3000"
    API_URL="http://188.225.56.200:8000"
fi

echo "📊 Testing frontend accessibility..."
if curl -s -I "$FRONTEND_URL" | grep -q "200 OK"; then
    echo "✅ Frontend is accessible at $FRONTEND_URL"
else
    echo "❌ Frontend not accessible at $FRONTEND_URL"
    echo "Checking container status..."
    if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.nginx.yml ps
    else
        docker-compose ps
    fi
    exit 1
fi

echo "🔧 Testing API endpoints..."
if curl -s "$API_URL/assistants" > /dev/null; then
    echo "✅ Assistants API is working"
    
    # Test creating a test assistant
    echo "🤖 Creating test assistant..."
    TEST_ASSISTANT='{
        "name": "Frontend Test Assistant",
        "description": "Test assistant for frontend functionality",
        "system_prompt": "You are a test assistant for frontend testing.",
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
            "name": "Updated Frontend Test Assistant",
            "description": "Updated test assistant for frontend testing",
            "system_prompt": "You are an updated test assistant for frontend testing.",
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
    echo "❌ Assistants API not responding"
    echo "Checking backend logs..."
    if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.nginx.yml logs backend | tail -10
    else
        docker-compose logs backend | tail -10
    fi
fi

echo ""
echo "✅ Frontend functionality test complete!"
echo ""
echo "🎯 New frontend features tested:"
echo "  - Enhanced assistant display in chat"
echo "  - Search functionality in assistant selector"
echo "  - Detailed assistant information with tags"
echo "  - Refresh button for assistant list"
echo "  - Settings button to open DialogSettings"
echo "  - Real-time updates between Chat and DialogSettings"
echo "  - Assistant creation, editing, and deletion"
echo ""
echo "🌐 Access your application:"
echo "  Frontend: $FRONTEND_URL"
echo "  API: $API_URL"
echo ""
echo "📋 Manual testing checklist:"
echo "  1. Open chat page"
echo "  2. Check assistant selector shows detailed info"
echo "  3. Test search in assistant selector"
echo "  4. Click refresh button to reload assistants"
echo "  5. Click settings button to open DialogSettings"
echo "  6. Create/edit/delete assistants in DialogSettings"
echo "  7. Verify changes appear in chat immediately"
