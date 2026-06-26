"""
AI Agent Core Module

This module implements the main AI agent using LangChain v1's create_agent API.
The agent is powered by Google Gemini and has access to multiple tools:
- Slack tools (send messages, get history, etc.)
- RAG tools (semantic search across Slack history)
- Memory tools (remember user preferences)
- MCP tools (GitHub, Notion integration)
- Scheduler tools (set reminders, schedule messages)

Architecture:
    User Message
        ↓
    LangChain Agent (Gemini)
        ↓
    Middleware Pipeline:
        1. RAG Middleware (inject relevant context)
        2. Memory Middleware (inject user memories)
        3. Slack Context Middleware (add platform info)
        ↓
    Tool Execution
        ↓
    Response
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.config import config
from src.utils.logger import get_logger
from src.slack.tools import SLACK_TOOLS
from src.agent.middleware import (
    RAGMiddleware,
    MemoryMiddleware,
    SlackContextMiddleware
)

logger = get_logger(__name__)

# Global agent instance
agent = None
llm = None


async def initialize_agent():
    """
    Initialize the AI agent with Gemini and all tools.
    
    This function:
    1. Creates the Gemini LLM instance
    2. Collects all available tools (Slack, RAG, Memory, MCP)
    3. Creates the agent with middleware
    4. Returns the configured agent
    
    Returns:
        Agent: Configured LangChain agent
    """
    global agent, llm
    
    logger.info("Initializing AI agent...")
    
    # Create Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model=config.gemini.chat_model,
        google_api_key=config.gemini.api_key,
        temperature=0.7,
        convert_system_message_to_human=True  # Gemini doesn't support system messages
    )
    
    logger.info(f"✅ Gemini LLM initialized: {config.gemini.chat_model}")
    
    # Collect all tools
    tools = []
    
    # Add Slack tools
    tools.extend(SLACK_TOOLS)
    logger.info(f"Added {len(SLACK_TOOLS)} Slack tools")
    
    # Add RAG tools (if enabled)
    if config.rag.enabled:
        try:
            from src.rag.retriever import RAG_TOOLS
            tools.extend(RAG_TOOLS)
            logger.info(f"Added {len(RAG_TOOLS)} RAG tools")
        except Exception as e:
            logger.warning(f"Could not load RAG tools: {e}")
    
    # Add Memory tools (if enabled)
    if config.memory.enabled:
        try:
            from src.memory.mem0_client import MEMORY_TOOLS
            tools.extend(MEMORY_TOOLS)
            logger.info(f"Added {len(MEMORY_TOOLS)} Memory tools")
        except Exception as e:
            logger.warning(f"Could not load Memory tools: {e}")
    
    # Add MCP tools (if enabled)
    if config.mcp.enabled:
        try:
            from src.mcp.registry import get_mcp_tools
            mcp_tools = await get_mcp_tools()
            tools.extend(mcp_tools)
            logger.info(f"Added {len(mcp_tools)} MCP tools")
        except Exception as e:
            logger.warning(f"Could not load MCP tools: {e}")
    
    # Add Scheduler tools
    try:
        from src.scheduler.tasks import SCHEDULER_TOOLS
        tools.extend(SCHEDULER_TOOLS)
        logger.info(f"Added {len(SCHEDULER_TOOLS)} Scheduler tools")
    except Exception as e:
        logger.warning(f"Could not load Scheduler tools: {e}")
    
    logger.info(f"Total tools available: {len(tools)}")
    logger.info(f"Tool names: {[tool.name for tool in tools]}")
    
    # Create system prompt
    system_prompt = """You are a Slack AI Assistant - an intelligent bot integrated directly into this Slack workspace.

🔍 YOUR SLACK SUPERPOWERS:

**Search & Memory:**
- Search through ALL Slack message history across channels (use RAG search tool)
- Remember user preferences and team context across conversations
- Recall past discussions and decisions

**Slack Actions:**
- Send messages to any channel for you
- Get channel information and member lists
- Check conversation history
- Add reactions to messages
- Join channels automatically

**Email & Calendar (Gmail):**
- List and search Gmail emails (filter by sender, subject, date)
- Read full email content and threads
- Send emails directly from Slack
- Create email drafts
- Summarize email threads
- List calendar events (Google Calendar)
- Create calendar events and meetings

**Productivity:**
- Set reminders and schedule messages in Slack
- Create GitHub issues from Slack conversations
- Create/update Notion pages from Slack threads
- Automate repetitive Slack tasks

**Intelligence:**
- Answer questions using your Slack workspace's knowledge
- Summarize long Slack threads
- Find who said what and when
- Connect information across different channels

🎯 WHEN INTRODUCING YOURSELF:
Always mention you can:
1. Search Slack history ("I can search through all your Slack messages")
2. Send messages to channels ("I can post messages to any channel you specify")
3. Remember preferences ("I'll remember your preferences across conversations")
4. Set reminders ("I can remind you about things at specific times")
5. Integrate with GitHub and Notion
6. Manage emails and calendar ("I can check your emails and schedule meetings")

💡 GUIDELINES:
- Lead with Slack capabilities, not generic AI features
- Proactively suggest Slack-specific actions (e.g., "Would you like me to search your Slack history?" or "Should I post this to #general?")
- Use tools frequently - you're here to DO things in Slack, not just chat
- Always confirm before sending messages to channels
- Search Slack history when users ask about past conversations
- Use markdown in responses for better Slack formatting

🚨 CRITICAL - YOU MUST USE TOOLS:
- You have direct access to Slack via tools - NEVER say you can't access Slack or that you're "just a chat interface"
- When a user asks you to post a message, list channels, search history, etc. - USE THE APPROPRIATE TOOL
- You ARE integrated into Slack and you CAN perform actions
- NEVER tell users to do things manually that you can do with tools
- Example: If user says "Post this to #general", use the send_message tool - don't tell them to do it themselves

Available tools you MUST use when appropriate:
- send_message: Post messages to Slack channels
- list_channels: Get list of all channels
- get_channel_history: Read messages from a channel
- rag_search: Search through ALL Slack message history
- set_reminder: Create scheduled reminders
- And more - check your tools list


Remember: You're not just answering questions - you're actively helping manage their Slack workspace!
"""

    
    # Create middleware pipeline
    middleware = []
    
    # Add RAG middleware (if enabled)
    if config.rag.enabled:
        try:
            rag_middleware = RAGMiddleware()
            middleware.append(rag_middleware)
            logger.info("Added RAG middleware")
        except Exception as e:
            logger.warning(f"Could not create RAG middleware: {e}")
    
    # Add Memory middleware (if enabled)
    if config.memory.enabled:
        try:
            memory_middleware = MemoryMiddleware()
            middleware.append(memory_middleware)
            logger.info("Added Memory middleware")
        except Exception as e:
            logger.warning(f"Could not create Memory middleware: {e}")
    
    # Add Slack context middleware (always)
    slack_middleware = SlackContextMiddleware()
    middleware.append(slack_middleware)
    logger.info("Added Slack context middleware")
    
    # Bind tools to the LLM
    # In LangChain v1, we use .bind_tools() to give the model access to tools
    # Gemini will then decide when to call tools vs just respond
    llm_with_tools = llm.bind_tools(tools)
    
    logger.info(f"✅ Bound {len(tools)} tools to LLM")
    
    # Store agent components
    agent = {
        "llm": llm_with_tools,
        "llm_base": llm,  # Keep base LLM without tools for fallback
        "tools": tools,
        "system_prompt": system_prompt,
        "middleware": middleware
    }
    
    logger.info("✅ AI agent fully initialized")
    
    return agent


async def process_message(
    user_message: str,
    session_id: str,
    user_id: str,
    channel_id: str,
    history: list[dict]
) -> str:
    """
    Process a user message with the AI agent.
    
    This function:
    1. Applies middleware to inject context (RAG, Memory, etc.)
    2. Builds the message history
    3. Calls the agent
    4. Returns the response
    
    Args:
        user_message: The user's message text
        session_id: Session ID for this conversation
        user_id: Slack user ID
        channel_id: Slack channel ID
        history: Previous conversation history
        
    Returns:
        str: Agent's response
    """
    if not agent:
        return "Error: Agent not initialized. Please check the logs."
    
    try:
        logger.info(f"Processing message for session {session_id}")
        
        # Build context from middleware
        context_parts = []
        
        # Apply middleware if we have it
        if isinstance(agent, dict) and "middleware" in agent:
            for mw in agent["middleware"]:
                try:
                    context = await mw.process(
                        user_message=user_message,
                        user_id=user_id,
                        channel_id=channel_id,
                        session_id=session_id
                    )
                    if context:
                        context_parts.append(context)
                except Exception as e:
                    logger.error(f"Middleware error: {e}", exc_info=True)
        
        # Build messages for the LLM
        messages = []
        
        # Add system prompt
        if isinstance(agent, dict):
            system_prompt = agent["system_prompt"]
        else:
            system_prompt = "You are a helpful AI assistant."
        
        # Add context from middleware
        if context_parts:
            system_prompt += "\n\n" + "\n\n".join(context_parts)
        
        messages.append(SystemMessage(content=system_prompt))
        
        # Add conversation history
        for msg in history[-10:]:  # Last 10 messages for context
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        # Get LLM instance with tools bound
        if isinstance(agent, dict):
            llm_instance = agent["llm"]
            tools_map = {tool.name: tool for tool in agent["tools"]}
        else:
            llm_instance = llm
            tools_map = {}
        
        # Call the LLM (with tools)
        logger.debug(f"Calling LLM with {len(messages)} messages")
        response = await llm_instance.ainvoke(messages)
        
        # Check if the model wants to use tools
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"Model requested {len(response.tool_calls)} tool call(s)")
            
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                if tool_name in tools_map:
                    try:
                        # Execute the tool
                        tool = tools_map[tool_name]
                        tool_result = await tool.ainvoke(tool_args)
                        logger.info(f"Tool {tool_name} returned: {str(tool_result)[:100]}...")
                        
                        # Add tool result to messages and get final response
                        from langchain_core.messages import ToolMessage
                        messages.append(response)  # Add AI's tool call request
                        messages.append(ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call["id"]
                        ))
                        
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                        # Continue with other tools
                else:
                    logger.warning(f"Tool {tool_name} not found in tools_map")
            
            # Get final response after tool execution
            response = await llm_instance.ainvoke(messages)
        
        # Extract response text
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
        
        logger.info(f"Generated response: {response_text[:100]}...")
        
        return response_text

        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return (
            "I apologize, but I encountered an error processing your message. "
            "Please try again or rephrase your question."
        )


if __name__ == "__main__":
    # Test agent initialization
    import asyncio
    
    async def test():
        await initialize_agent()
        
        # Test message processing
        response = await process_message(
            user_message="Hello! What can you help me with?",
            session_id="test_session",
            user_id="U123456",
            channel_id="C789012",
            history=[]
        )
        
        print(f"Response: {response}")
    
    asyncio.run(test())
