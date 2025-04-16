from abc import ABC, abstractmethod
from typing import List
from functools import partial
from pr_agent.prompting.utils import parse_and_check_json

class PromptGenerator(ABC):
    fields: List[str] = []
    
    def get_field_parsing_prompt(self) -> str:
        return (
            f"Based on the above information, provide the correct values for the following fields strictly "
            f"in valid JSON format: {', '.join(self.fields)}.\n\n"
            "Important:\n"
            "1. Return only valid JSON. No extra explanations, text, or comments.\n"
            "2. Ensure that the output can be parsed by a JSON parser directly.\n"
            "3. Do not include any non-JSON text or formatting outside the JSON object."
            '4. An example is \{"<provided_field>": "<correct_value_for_the_field>"\}'
        )
    
    def generate_chat_prompt(self):
        chat_prompt = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": self.generate_prompt()
            }
        ]
        
        return chat_prompt
    
    def create_parser(self):
        return partial(parse_and_check_json, expected_keys=self.fields)
    

