from processors.rc_prompt import ROOTCAUSE_PROMPT
import re
from baml_client import b
from baml_client.types import RootCauseAnalysis
import logging
from datetime import datetime

class LLMProcessor:
    def __init__(self):
        # The BAML client is initialized automatically                                                     
        # and retrieves the API key from the environment.                                                  
        pass

    def get_llm_response(self, query: str, incident_texts: list[str]) -> str:
        """
        Generate a response from the LLM based on the new incident and similar past incidents.

        :param query: The new incident description.
        :param incident_texts: List of similar past incidents.
        :return: LLM's response containing root cause summary and troubleshooting steps.
        """
        # add <incident> tags to each incident text
        similar_incidents_str = "\n\n".join(
            [f"<incident>{text}</incident>" for text in incident_texts]
        )

        baml_response = b.AnalyzeIncident(
            query=query,
            similar_incidents_str=similar_incidents_str
        )
        
        # Log the reasoning using the BAML-specific function                                           
        self._log_reasoning_baml(baml_response, query)
        
        # Construct the response string from the BAML object                
        # Join troubleshooting steps with newlines to preserve their original formatting
        troubleshooting_steps_formatted = "\n".join(baml_response.troubleshooting_steps)
        
        raw_response = f"""<root_cause_summary>
{baml_response.root_cause_summary}
</root_cause_summary>

<troubleshooting_steps>
{troubleshooting_steps_formatted}
</troubleshooting_steps>"""
        
        return self.format_llm_response(raw_response)
    
    def _log_reasoning_baml(self, response: RootCauseAnalysis, query: str) -> None:                        
        """Extract and log the reasoning from the BAML object for debugging purposes."""                   
        logging.basicConfig(                                                                               
            filename='llm_reasoning.log',                                                                  
            level=logging.INFO,                                                                            
            format='%(asctime)s - %(levelname)s - %(message)s'                                             
        )

        reasoning = response.reasoning.strip()                                                             
        logging.info(f"""=== BAML LLM REASONING DEBUG ===
QUERY: {query[:100]}{'...' if len(query) > 100 else ''}
REASONING:
{reasoning}
=============================""") 

    def format_llm_response(self, raw_response: str) -> str:
        """
        Format the response for display in Streamlit with proper markdown
        """
        # Clean up any stray XML tags except the ones we want to process
        formatted_response = re.sub(r"</?(?:response|task|instruction)[^>]*>", "", raw_response, flags=re.IGNORECASE)
        
        # Convert XML tags to markdown
        # Root cause summary
        formatted_response = re.sub(
            r"<root_cause_summary>\s*(.*?)\s*</root_cause_summary>", 
            r"### 🎯 Root Cause Analysis\n\n\1\n", 
            formatted_response, 
            flags=re.DOTALL
        )
        
        # Troubleshooting steps - format as a numbered list
        def format_steps(match):
            steps_content = match.group(1).strip()
            # Ensure each step is correctly formatted as a numbered list item
            steps = steps_content.split('\n')
            formatted_steps = []
            for i, step in enumerate(steps):
                # Remove any existing numbering
                step = re.sub(r'^\d+\.\s*', '', step).strip()
                formatted_steps.append(f"{i+1}. {step}")
            steps_str = "\n".join(formatted_steps)
            heading = "### 🔧 Recommended Troubleshooting Steps\n\n"
            return heading + steps_str

        formatted_response = re.sub(
            r"<troubleshooting_steps>\s*(.*?)\s*</troubleshooting_steps>",
            format_steps,
            formatted_response,
            flags=re.DOTALL
        )
        
        # Clean up multiple newlines
        formatted_response = re.sub(r"\n{3,}", "\n\n", formatted_response)
        
        return formatted_response.strip()