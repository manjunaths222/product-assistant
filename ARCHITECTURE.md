# Unified Orchestrator Architecture

## Overview

The system now uses a **unified orchestrator pattern** similar to Google ADK's coordinator/dispatcher pattern. A single orchestrator routes requests to appropriate agents (chat or analysis) based on the request type.

## Architecture Flow

```
User Request
    ↓
Unified Orchestrator
    ↓
Router Node (LLM-based decision)
    ↓
    ├──→ Chat Agent (with context + conversation history)
    ├──→ Feature Analysis Agent
    └──→ Feasibility Analysis Agent
    ↓
Response (with chat_id for follow-ups)
```

## Key Components

### 1. Unified State (`unified_state.py`)
- Single state schema that handles all request types
- Contains fields for chat, feature analysis, and feasibility analysis
- Allows seamless routing between different agent types

### 2. Router Node (`router_node.py`)
- Determines request type using:
  - Explicit parameters (chat_id, query, requirement)
  - LLM-based intent classification if ambiguous
- Routes to appropriate agent:
  - `chat` - For follow-up questions
  - `feature_analysis` - For analyzing existing features
  - `feasibility_analysis` - For analyzing new requirements

### 3. Chat Node (`chat_node.py`)
- Handles conversational responses
- Uses analysis context from previous analyses
- Maintains conversation history
- Provides business-friendly responses (no technical jargon)

### 4. Analysis Adapters (`analysis_adapters.py`)
- Bridge between unified state and existing analysis nodes
- Converts unified state to specific analysis states
- Runs existing analysis nodes
- Converts results back to unified state

### 5. Unified Graph (`unified_graph.py`)
- LangGraph workflow with conditional routing
- Router → Decision → Agent → Response
- All paths end at END node

### 6. Unified Orchestrator (`unified_orchestrator.py`)
- Single entry point for all requests
- Handles:
  - Loading conversation history from database
  - Running Codex analysis when needed
  - Creating chat sessions after analysis
  - Updating chat history after conversations

## Usage

### Chat Request
```python
orchestrator = UnifiedOrchestrator()
result = orchestrator.run(
    project_id="project-123",
    chat_id=456,
    message="Can you explain more about the risks?",
    db=db_session
)
# Returns: {"status": "success", "request_type": "chat", "response": "...", "chat_id": 456}
```

### Feature Analysis Request
```python
result = orchestrator.run(
    project_id="project-123",
    recipe_id=789,
    query="How does authentication work?",
    db=db_session
)
# Returns: {"status": "success", "request_type": "feature_analysis", 
#           "high_level_design": "...", "feature_details": "...", "chat_id": 999}
```

### Feasibility Analysis Request
```python
result = orchestrator.run(
    project_id="project-123",
    requirement="Add OAuth2 authentication",
    context="Need to support Google and GitHub",
    db=db_session
)
# Returns: {"status": "success", "request_type": "feasibility_analysis",
#           "high_level_design": "...", "risks": [...], "chat_id": 1000}
```

## Benefits

1. **Single Entry Point**: One orchestrator handles all request types
2. **Intelligent Routing**: LLM-based routing when intent is unclear
3. **Context Preservation**: Chat maintains analysis context and conversation history
4. **Unified State**: Single state schema simplifies data flow
5. **Extensible**: Easy to add new agent types or routing logic

## Current Status

All routers and endpoints now use `UnifiedOrchestrator`. The system provides:
- Intelligent routing between chat and analysis
- Context-aware conversations
- Automatic chat session creation after analysis
- Ability to trigger new analysis from chat conversations

