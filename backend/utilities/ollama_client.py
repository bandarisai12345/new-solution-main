"""
Ollama client wrapper with streaming support
"""

import ollama

from .config import OLLAMA_MODEL


class OllamaClient:
    """Wrapper for Ollama API calls with streaming support"""
    
    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
    
    def chat(self, messages, stream=False):
        """Send chat request to Ollama"""
        if stream:
            return ollama.chat(model=self.model, messages=messages, stream=True)
        else:
            response = ollama.chat(model=self.model, messages=messages, stream=False)
            return response['message']['content']
    
    def generate_from_prompt(self, system_prompt, user_prompt, stream=False):
        """Generate response with system and user prompts"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages, stream=stream)
    
    def stream_and_collect(self, system_prompt, user_prompt, prefix="", suppress_debug=False):
        """Stream response and collect full text"""
        if prefix and not suppress_debug:
            print(prefix, end='', flush=True)
        
        full_response = ""
        for chunk in self.generate_from_prompt(system_prompt, user_prompt, stream=True):
            if 'message' in chunk and 'content' in chunk['message']:
                content = chunk['message']['content']
                if not suppress_debug:
                    print(content, end='', flush=True)
                full_response += content
        
        print("\n")  # New lines after streaming
        return full_response
