import os
import json
import requests
from typing import Dict, Any

try:
    from . import llm_config
except ImportError:
    import llm_config

# Import LangChain components
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    from langchain_community.chat_message_histories import FileChatMessageHistory
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.runnables.history import RunnableWithMessageHistory
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"LangChain Import Error: {e}")
    LANGCHAIN_AVAILABLE = False

class ChatEngine:
    def __init__(self):
        # Stateless now. We init LLM per request.
        pass
        
    def generate_response(self, query: str, context: dict = None, project_id: str = None, history: list = None, project_path: str = None, api_key: str = None):
        """
        Generates a response using LangChain (if available) or falls back to legacy.
        
        Args:
            query (str): The user's question or command.
            context (dict): Optional. Valid analysis/EDL data from the project.
            project_id (str): Optional. Used to track conversation history per project.
            history (list): Legacy list of previous messages (Not used if LangChain is active).
            project_path (str): Path to the project directory for storing history files.
            api_key (str): Optional. User provided API key.
        """
        
        # 1. Build System Prompt
        system_prompt_content = self._build_system_prompt(context)
        
        # 2. Use LangChain if applicable
        if LANGCHAIN_AVAILABLE and project_path and llm_config.LLM_PROVIDER == "gemini":
            return self._generate_with_langchain(query, system_prompt_content, project_path, api_key)
            
        # 3. Fallback to Legacy (Ollama or Manual History)
        # Construct messages manually
        messages = [{"role": "system", "content": system_prompt_content}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})
        
        return self._call_legacy_llm(messages)

    def _generate_with_langchain(self, query, system_prompt_content, project_path, api_key=None):
        try:
            # Determine Key
            key_to_use = api_key if api_key else llm_config.GEMINI_API_KEY
            if not key_to_use:
                return "Error: No API Key provided. Please set your Gemini API Key in settings."

            # Init LLM Just-In-Time
            llm = ChatGoogleGenerativeAI(
                model=llm_config.LLM_MODEL,
                google_api_key=key_to_use,
                temperature=llm_config.DEFAULT_TEMPERATURE
            )
            
            # Ensure history file exists
            if not os.path.exists(project_path):
                os.makedirs(project_path, exist_ok=True)
            
            history_file = os.path.join(project_path, "chat_history.json")
            
            # Initialize FileChatMessageHistory
            # We use the project directory to scope history
            history_store = FileChatMessageHistory(history_file)
            
            # Define Prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ])
            
            # Create Chain
            chain = prompt | llm
            
            # Retrieve previous messages
            previous_messages = history_store.messages
            
            # Invoke Chain
            response = chain.invoke({
                "system_prompt": system_prompt_content,
                "history": previous_messages,
                "input": query
            })
            
            # Update History Logic
            # LangChain's FileChatMessageHistory doesn't auto-update from the chain unless using RunnableWithMessageHistory
            # We will manually update it for simplicity and explicit control
            history_store.add_user_message(query)
            history_store.add_ai_message(response.content)
            
            return response.content
            
        except Exception as e:
            print(f"LangChain Execution Error: {e}")
            return f"Error using LangChain: {str(e)}"

    def _build_system_prompt(self, context):
        base_prompt = (
            "You are Gravity AI, an advanced video editing assistant. "
            "You help users edit videos, understand their footage, and make creative decisions.\n"
        )
        
        if context:
            project_name = context.get("project_name", "Untitled")
            clips_count = context.get("total_clips", 0)
            
            timeline_summary = ""
            clips = context.get("timeline", [])
            for clip in clips[:50]: 
                timeline_summary += f"- ID {clip.get('id')}: {clip.get('source_video')} ({clip.get('start')}-{clip.get('end')}s). Visuals: {json.dumps(clip.get('visual_data'))}. Status: {'Kept' if clip.get('keep')=='true' else 'Rejected'}.\n"
            
            memory_prompt = f"""
            \n[MEMORY ACTIVE: PROJECT ANALYZED DATA]
            You are currently assisting with project: '{project_name}'.
            Total Clips: {clips_count}
            
            TIMELINE CONTEXT:
            {timeline_summary}
            
            INSTRUCTIONS:
            - You have full knowledge of the analyzed footage above.
            - If the user asks about specific shots (e.g. "drone shots", "happy moments"), search the Visuals data in your memory.
            - If the user asks "why did you cut this?", refer to the 'Status' and visual data.
            - Be concise and professional.
            """
            return base_prompt + memory_prompt
        else:
            manual_prompt = (
                "\n[MODE: MANUAL CONVERSATION]\n"
                "The user is editing manually or hasn't run AI analysis yet. "
                "Answer general video editing questions, provide creative tips, or guide them on how to use the editor. "
                "Do not hallucinate specific file details unless provided."
            )
            return base_prompt + manual_prompt

    def _call_legacy_llm(self, messages):
        if llm_config.LLM_PROVIDER == "ollama":
            url = f"{llm_config.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": llm_config.LLM_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": llm_config.DEFAULT_TEMPERATURE
                }
            }
            try:
                response = requests.post(url, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "I couldn't generate a response.")
                else:
                    return f"Error from AI: {response.text}"
            except Exception as e:
                return f"Failed to connect to AI Service: {str(e)}"
        else:
            return "Legacy provider not supported or configured."

# Singleton instance
engine = ChatEngine()

def chat(query, context=None, history=None, project_path=None, api_key=None):
    return engine.generate_response(query, context, history=history, project_path=project_path, api_key=api_key)
