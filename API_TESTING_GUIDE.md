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

**Save the `project_id` from response** - you'll need it for next steps!

---

## Step 3: List Projects (Optional)

**Endpoint:** `GET /projects`

```bash
curl -X GET "http://localhost:8000/projects"
```

---

## Step 4: Analyze Feasibility

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

## Step 5: Chat About the Analysis

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

## Step 6: Get Chat History

**Endpoint:** `GET /chats/{chat_id}/history`

```bash
curl -X GET "http://localhost:8000/chats/YOUR_CHAT_ID/history"
```

**Response:** Full conversation history with all messages

---

## Alternative Flow: Feature Analysis

### Step 1: Create a Recipe (Feature)

**Endpoint:** `POST /recipes`

```bash
curl -X POST "http://localhost:8000/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "YOUR_PROJECT_ID",
    "recipe_name": "Document Upload",
    "description": "Feature for uploading documents"
  }'
```

**Save the `id` (recipe_id) from response**

---

### Step 2: Query Feature Details

**Endpoint:** `POST /recipes/{recipe_id}/query`

Replace `{recipe_id}` with the id from Step 1.

```bash
curl -X POST "http://localhost:8000/recipes/YOUR_RECIPE_ID/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the document upload feature work?"
  }'
```

**Response includes:**
- `high_level_design` - Feature overview
- `feature_details` - Detailed feature breakdown
- **`chat_id`** - Save this for follow-up questions!

---

### Step 3: Chat About the Feature

**Endpoint:** `POST /chats/{chat_id}/message`

```bash
curl -X POST "http://localhost:8000/chats/YOUR_CHAT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What user interactions are supported?"
  }'
```

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

echo -e "\n2. Analyzing feasibility..."
FEASIBILITY_RESPONSE=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/feasibility" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Add user authentication",
    "context": "Need OAuth2 support"
  }')

CHAT_ID=$(echo $FEASIBILITY_RESPONSE | jq -r '.chat_id')
echo "Chat ID: $CHAT_ID"

echo -e "\n3. Sending chat message..."
curl -X POST "$BASE_URL/chats/$CHAT_ID/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main risks?"
  }' | jq

echo -e "\n4. Getting chat history..."
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

1. **Feasibility/Feature Analysis:**
   - Router determines it's an analysis request
   - Routes to appropriate analysis agent
   - Analysis agent runs Codex analysis
   - Returns business-friendly results
   - **Automatically creates chat session** for follow-ups

2. **Chat Messages:**
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
✅ **Automatic chat creation** - After every analysis  
✅ **Context-aware chat** - Remembers previous analysis  
✅ **Business-friendly responses** - No technical jargon  
✅ **Unified routing** - Single orchestrator handles everything  

---

## Testing Checklist

- [ ] Create a project (auto-generates project_id)
- [ ] List projects
- [ ] Analyze feasibility (get chat_id)
- [ ] Send chat message about feasibility analysis
- [ ] Get chat history
- [ ] Create a recipe
- [ ] Query feature details (get chat_id)
- [ ] Send chat message about feature
- [ ] Test multiple follow-up questions in same chat

---

## Troubleshooting

**If you get "project not found":**
- Make sure you're using the correct project_id from the create project response

**If you get "chat not found":**
- Make sure you're using the chat_id from the analysis response
- Chat is automatically created after analysis completes

**If analysis takes too long:**
- Codex analysis may take time depending on codebase size
- Check server logs for progress

**If chat doesn't have context:**
- Make sure you're using the chat_id from the analysis response
- The chat is linked to that specific analysis

