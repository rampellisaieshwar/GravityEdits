
import requests
import requests
import json
try:
    from . import llm_config
except ImportError:
    import llm_config

class ChatEngine:
    def __init__(self):
        self.history = []
        
    def generate_response(self, query: str, context: dict = None, project_id: str = None):
        """
        Generates a response using the configured LLM.
        
        Args:
            query (str): The user's question or command.
            context (dict): Optional. Valid analysis/EDL data from the project.
            project_id (str): Optional. Used to track conversation history per project.
        """
        
        # 1. Build System Prompt based on Mode
        system_prompt = self._build_system_prompt(context)
        
        # 2. construct messages list (simulating chat history)
        # In a real app, we'd fetch history from DB using project_id
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        # 3. Call LLM
        return self._call_llm(messages)

    def _build_system_prompt(self, context):
        base_prompt = (
            "You are Gravity AI, an advanced video editing assistant. "
            "You help users edit videos, understand their footage, and make creative decisions.\n"
        )
        
        if context:
            # AI ANALYZED MODE
            # We "stringify" the context carefully to avoid token overflow
            # We focus on the EDL and Visual Data summary
            
            # Extract high-level summary if possible
            project_name = context.get("project_name", "Untitled")
            clips_count = context.get("total_clips", 0)
            
            # Create a compact textual representation of top clips
            timeline_summary = ""
            clips = context.get("timeline", [])
            # Limit to first 20 clips to save context or simplify
            for clip in clips[:30]: 
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
            # MANUAL MODE
            manual_prompt = (
                "\n[MODE: MANUAL CONVERSATION]\n"
                "The user is editing manually or hasn't run AI analysis yet. "
                "Answer general video editing questions, provide creative tips, or guide them on how to use the editor. "
                "Do not hallucinate specific file details unless provided."
            )
            return base_prompt + manual_prompt

    def _call_llm(self, messages):
        if llm_config.LLM_PROVIDER == "ollama":
            return self._call_ollama(messages)
        elif llm_config.LLM_PROVIDER == "openai":
            # flexible extension point
            return "OpenAI implementation not yet active."
        else:
            return "Unknown LLM Provider."

    def _call_ollama(self, messages):
        try:
            # Ollama standard chat endpoint
            url = f"{llm_config.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": llm_config.LLM_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": llm_config.DEFAULT_TEMPERATURE
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "I couldn't generate a response.")
            else:
                return f"Error from AI: {response.text}"
        except Exception as e:
            return f"Failed to connect to AI Service: {str(e)}"

# Singleton instance
engine = ChatEngine()

def chat(query, context=None):
    return engine.generate_response(query, context)
