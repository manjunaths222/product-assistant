# API Testing Guide

## Complete Flow to Test

### Step 1: Start the Server

```bash
cd /Users/yml/Documents/voltron/product-assistant
python main.py
# Or
uvicorn main:app --reload
```

Server will be available at: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Step 2: Create a Project

**Endpoint:** `POST /projects`

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "github_repo": "https://github.com/manjunaths222/rag-langchain-langgraph-legal-system.git",
    "description": "RAG system for legal document Q&A"
  }'
```

**Response:** Returns project with auto-generated `project_id` (UUID) and `repo_path`

**Note:** Feature discovery runs automatically in the background after project creation.
Feature discovery runs in the background. Check the features endpoint after a few moments.

**Save the `project_id` from response** - you'll need it for next steps!

---

## Step 3: List Projects (Optional)

**Endpoint:** `GET /projects`

```bash
curl -X GET "http://localhost:8000/projects"
```

---

## Step 4: Discover Features (Optional)
This is optional API considering that the POST /projects already runs feature discovery by default.

**Endpoint:** `POST /projects/{project_id}/features/discover`

Replace `{project_id}` with the project_id from Step 2.

```bash
curl -X POST "http://localhost:8000/projects/YOUR_PROJECT_ID/features/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "force": false
  }'
```

**Response:** Returns immediately with status message:
```json
{
  "status": "started",
  "message": "Feature discovery started for project 'YOUR_PROJECT_ID'. Check /projects/YOUR_PROJECT_ID/features for results once discovery completes.",
  "project_id": "YOUR_PROJECT_ID"
}
```

**Note:** Feature discovery runs in the background. Check the features endpoint after a few moments.

**Get discovered features:**
```bash
# List all features
curl -X GET "http://localhost:8000/projects/YOUR_PROJECT_ID/features"

# Get a specific feature (includes chat_id if available)
curl -X GET "http://localhost:8000/projects/YOUR_PROJECT_ID/features/{feature_id}"
```

---

## Step 5: Analyze Feasibility

**Endpoint:** `POST /projects/{project_id}/feasibility`

Replace `{project_id}` with the project_id from Step 2.

```bash
curl -X POST "http://localhost:8000/projects/YOUR_PROJECT_ID/feasibility" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Add support for PDF document upload",
    "context": "Users need to upload legal PDFs for analysis"
  }'
```

**Response includes:**
- `high_level_design` - Business-friendly approach
- `risks` - List of business risks
- `open_questions` - Questions needing product decisions
- `technical_feasibility` - High/Medium/Low
- `rough_estimate` - Time and effort estimates
- **`chat_id`** - Save this for follow-up questions!

---

## Step 6: Chat About the Analysis

**Endpoint:** `POST /chats/{chat_id}/message`

Replace `{chat_id}` with the chat_id from Step 4.

```bash
curl -X POST "http://localhost:8000/chats/YOUR_CHAT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain more about the risks?"
  }'
```

**Response:** Conversational response with context from the analysis

**Try more questions:**
```bash
# Follow-up question
curl -X POST "http://localhost:8000/chats/YOUR_CHAT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the dependencies for this feature?"
  }'
```

---

## Step 7: Get Chat History

**Endpoint:** `GET /chats/{chat_id}/history`

```bash
curl -X GET "http://localhost:8000/chats/YOUR_CHAT_ID/history"
```

**Response:** Full conversation history with all messages

---

## Alternative Flow: Feature Discovery and Chat

### Step 1: Discover Features

**Endpoint:** `POST /projects/{project_id}/features/discover`

```bash
curl -X POST "http://localhost:8000/projects/YOUR_PROJECT_ID/features/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "force": false
  }'
```

**Note:** This runs in the background. Wait a few moments, then check for features.

---

### Step 2: Get Discovered Features

**Endpoint:** `GET /projects/{project_id}/features`

```bash
curl -X GET "http://localhost:8000/projects/YOUR_PROJECT_ID/features"
```

**Response:** List of discovered features, each with:
- `feature_id` - ID of the feature
- `feature_name` - Name of the feature
- `high_level_overview` - Overview of the feature
- `scope` - Feature scope
- `dependencies` - List of dependencies
- `key_considerations` - Key considerations
- `limitations` - Limitations
- **`chat_id`** - Use this to chat about the feature (if available)

---

### Step 3: Get Specific Feature

**Endpoint:** `GET /projects/{project_id}/features/{feature_id}`

```bash
curl -X GET "http://localhost:8000/projects/YOUR_PROJECT_ID/features/{feature_id}"
```

**Response includes:**
- Full feature details
- **`chat_id`** - Use this to chat about the feature (if available)
- `chat_history` - Previous conversation history (if chat exists)

---

### Step 4: Chat About the Feature

**Endpoint:** `POST /chats/{chat_id}/message`

Use the `chat_id` from the feature response.

```bash
curl -X POST "http://localhost:8000/chats/YOUR_CHAT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What user interactions are supported?"
  }'
```

**Note:** If the feature doesn't have a `chat_id`, chats are created automatically when needed during feasibility analysis or other operations.

---

## Quick Test Script

Save this as `test_apis.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "1. Creating project..."
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "github_repo": "https://github.com/manjunaths222/rag-langchain-langgraph-legal-system.git",
    "description": "Test project"
  }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.project_id')
echo "Project ID: $PROJECT_ID"

echo -e "\n2. Triggering feature discovery (runs in background)..."
curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/features/discover" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' | jq

echo -e "\n3. Waiting a few seconds for feature discovery..."
sleep 5

echo -e "\n4. Getting discovered features..."
curl -s -X GET "$BASE_URL/projects/$PROJECT_ID/features" | jq

echo -e "\n5. Analyzing feasibility..."
FEASIBILITY_RESPONSE=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/feasibility" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Add user authentication",
    "context": "Need OAuth2 support"
  }')

CHAT_ID=$(echo $FEASIBILITY_RESPONSE | jq -r '.chat_id')
echo "Chat ID: $CHAT_ID"

echo -e "\n6. Sending chat message..."
curl -X POST "$BASE_URL/chats/$CHAT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main risks?"
  }' | jq

echo -e "\n7. Getting chat history..."
curl -s -X GET "$BASE_URL/chats/$CHAT_ID/history" | jq
```

Make it executable and run:
```bash
chmod +x test_apis.sh
./test_apis.sh
```

---

## Expected Behavior

### Unified Orchestrator Flow

1. **Feature Discovery:**
   - Runs in background using FastAPI BackgroundTasks
   - Endpoint returns immediately with status message
   - Discovery process analyzes codebase and stores features
   - Compatible with render.com deployment

2. **Feasibility/Feature Analysis:**
   - Router determines it's an analysis request
   - Routes to appropriate analysis agent
   - Analysis agent runs Codex analysis
   - Returns business-friendly results
   - **Automatically creates chat session** for follow-ups

3. **Chat Messages:**
   - Router determines it's a chat request
   - Routes to chat agent
   - Chat agent uses:
     - Previous analysis context
     - Full conversation history
   - Returns conversational response
   - Updates chat history in database

### Key Features

✅ **Auto-generated project_id** - No need to provide it  
✅ **Stored repo_path** - Retrieved from database automatically  
✅ **Background feature discovery** - Runs asynchronously, returns immediately
✅ **Automatic chat creation** - After every analysis  
✅ **Context-aware chat** - Remembers previous analysis  
✅ **Business-friendly responses** - No technical jargon  
✅ **Unified routing** - Single orchestrator handles everything  
✅ **Render.com compatible** - Uses FastAPI BackgroundTasks

---

## Testing Checklist

- [ ] Create a project (auto-generates project_id, feature discovery runs in background)
- [ ] List projects
- [ ] Trigger feature discovery (runs in background)
- [ ] Get discovered features
- [ ] Get specific feature (includes chat_id if available)
- [ ] Analyze feasibility (get chat_id)
- [ ] Send chat message about feasibility analysis
- [ ] Get chat history
- [ ] Test multiple follow-up questions in same chat

---

## Troubleshooting

**If you get "project not found":**
- Make sure you're using the correct project_id from the create project response

**If you get "chat not found":**
- Make sure you're using the chat_id from the analysis response
- Chat is automatically created after analysis completes

**If feature discovery takes too long:**
- Feature discovery runs in background - endpoint returns immediately
- Wait a few moments, then check /projects/{project_id}/features
- Check server logs for progress

**If analysis takes too long:**
- Codex analysis may take time depending on codebase size
- Check server logs for progress

**If chat doesn't have context:**
- Make sure you're using the chat_id from the analysis response
- The chat is linked to that specific analysis

