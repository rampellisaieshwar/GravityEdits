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
        
    def generate_response(self, query: str, context: dict = None, project_id: str = None, history: list = None, project_path: str = None, api_key: str = None, current_state: dict = None):
        """
        Generates a response using LangChain (if available) or falls back to legacy.
        
        Args:
            query (str): The user's question or command.
            context (dict): Optional. Valid analysis/EDL data from the project.
            project_id (str): Optional. Used to track conversation history per project.
            history (list): Legacy list of previous messages (Not used if LangChain is active).
            project_path (str): Path to the project directory for storing history files.
            api_key (str): Optional. User provided API key.
            current_state (dict): Optional. LIVE State from frontend.
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

    def _build_system_prompt(self, context, current_state=None):
        base_prompt = (
            "You are Gravity AI, an advanced video editing assistant. "
            "You help users edit videos, understand their footage, and make creative decisions.\n"
        )
        
        # Determine Context Source (Live vs Disk)
        timeline_source = []
        project_name = "Untitled"
        overlays = []
        viral_shorts = []
        
        if current_state and 'edl' in current_state:
             # LIVE STATE from Frontend (Preferred)
             timeline_source = current_state['edl']
             project_name = current_state.get('name', 'Project')
             overlays = current_state.get('overlays', [])
             viral_shorts = current_state.get('viralShorts', [])
        elif context:
             # Fallback to DISK STATE
             timeline_source = context.get("timeline", [])
             project_name = context.get("project_name", "Untitled")
             overlays = context.get("overlays", [])
             viral_shorts = context.get("viral_shorts", [])
             
        if timeline_source or context:
            # Prepare a rich but clean summary for the AI
            full_timeline_data = []
            
            # Optimization: Limit context size
            MAX_CHARS = 100000 
            curr_chars = 0
            
            for clip in timeline_source:
                # Include TEXT so the AI knows what was said!
                # Truncate text if individual clip is huge (rare)
                raw_text = clip.get('text', '') or ''
                
                clip_info = {
                    "id": clip.get('id'),
                    "t": f"{clip.get('start', 0):.2f}-{clip.get('end', 0):.2f}",
                    "text": raw_text[:300], # Trucate super long single clips to save token space
                    "st": "K" if (str(clip.get('keep', 'true')).lower() != 'false') else "X"
                }
                
                # Check size
                json_part = json.dumps(clip_info)
                if curr_chars + len(json_part) > MAX_CHARS:
                    full_timeline_data.append({"info": "...TRUNCATED..."})
                    break
                
                full_timeline_data.append(clip_info)
                curr_chars += len(json_part)

            memory_prompt = f"""
            \n[MEMORY ACTIVE: PROJECT CONTEXT]
            Project: '{project_name}'
            
            TIMELINE (id, time, text, status[K=Keep, X=Cut]):
            {json.dumps(full_timeline_data, separators=(',', ':'))}
            
            OVERLAYS:
            {json.dumps(overlays, indent=1)}
            
            VIRAL SHORTS:
            {json.dumps(viral_shorts, indent=1)}
            --------------------
            
            USER INSTRUCTION:
            - You have access to the TRANSCRIPT above.
            - SEARCH the 'text' fields for queries.
            
            [AVAILABLE TOOLS - EXECUTABLE COMMANDS]
            To take action, output a code block with language `tool_code`.
            
            1. CUT A CLIP (Reject/Delete):
            ```tool_code
            gravity_ai.cut_clip(clip_id="1")
            ```
            
            2. SPLIT A CLIP (Precision Cut):
            ```tool_code
            gravity_ai.split_clip(clip_id="1", time=15.5)
            ```
            
            3. REMOVE A WORD (Best for single words):
            - The most precise way to remove a specific word.
            - Provide the exact word(s) and the target clip ID.
            ```tool_code
            gravity_ai.remove_word(clip_id="1", word="banana")
            ```
            
            4. REMOVE A SEGMENT (Manual Surgery):
            - Use this ONLY if you know exact timestamps.
            ```tool_code
            gravity_ai.remove_segment(clip_id="1", start=10.5, end=11.2)
            ```
            
            4. KEEP A CLIP (Restore):
            ```tool_code
            gravity_ai.keep_clip(clip_id="1")
            ```
            
            5. ADD TEXT OVERLAY:
            ```tool_code
            gravity_ai.add_text(content="HELLO WORLD", start_time=5.5, duration=2.0, style="pop")
            ```
            
            6. UPDATE TRANSCRIPT (Fix typos):
            ```tool_code
            gravity_ai.edit_transcript(clip_id="2", new_transcript="Fixed text here")
            ```
            
            7. UNDO LAST ACTION:
            - Use this if the user asks to "undo", "go back", or "revert".
            ```tool_code
            gravity_ai.undo_action()
            ```

            8. REGENERATE PROJECT (Re-Edit):
            - Use this if the user asks to "re-analyze", "re-edit", "remake", or "start over with instruction".
            - useful for broad style changes like "make it faster", "focus on X", "remove bad clips".
            ```tool_code
            gravity_ai.regenerate_project(instruction="Make it fast paced and focus on the dog")
            ```
            
            PERMISSIONS & TERMINOLOGY:
            - **YOU HAVE FULL PERMISSION TO EDIT.**
            - **"Make it False" / "Reject" / "Red"** = Use `cut_clip(clip_id)`.
            - **"Make it True" / "Approve" / "Green"** = Use `keep_clip(clip_id)`.
            
            INTELLIGENT ID RESOLUTION:
            - If the user says "Reject the banana clip", you MUST:
              1. Search transcripts for "banana".
              2. Find the Clip ID.
              3. Execute `gravity_ai.remove_word` or `gravity_ai.cut_clip`.
            - Do NOT ask for the ID. Find it yourself.
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

def chat(query, context=None, history=None, project_path=None, api_key=None, current_state=None):
    return engine.generate_response(query, context, history=history, project_path=project_path, api_key=api_key, current_state=current_state)
