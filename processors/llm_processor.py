from google import genai
from processors.rc_prompt import ROOTCAUSE_PROMPT
import re
from google.genai.types import GenerateContentConfig
from utils.secrets_helper import get_secret

class LLMProcessor:
    def __init__(self):
        GOOGLE_API_KEY = get_secret("google-api-key", "GOOGLE_API_KEY")
        self.client = genai.Client(api_key=GOOGLE_API_KEY)

    def get_response(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.1,  # Low temperature for more focused, less chatty responses
                max_output_tokens=2048,
                top_p=0.8,
                top_k=20
            ))
        return response.text

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

        prompt = ROOTCAUSE_PROMPT.format(
            query=query,
            similar_incidents_str=similar_incidents_str
        )

        response = self.get_response(prompt.strip())
        
        # Extract and log reasoning for debugging
        self._log_reasoning(response, query)
        
        return response

    def _log_reasoning(self, raw_response: str, query: str) -> None:
        """Extract and log the reasoning section for debugging purposes."""
        import logging
        from datetime import datetime
        
        # Set up logging if not already configured
        logging.basicConfig(
            filename='llm_reasoning.log', 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Extract reasoning section
        reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", raw_response, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
            
            # Log the reasoning with query context
            logging.info(f"""
=== LLM REASONING DEBUG ===
QUERY: {query[:100]}{'...' if len(query) > 100 else ''}
REASONING:
{reasoning}
=========================""")
        else:
            logging.warning(f"No reasoning section found for query: {query[:50]}...")

    def format_llm_response(self, raw_response: str) -> str:
        formatted_response = raw_response
        
        # Remove reasoning section from user-facing output
        formatted_response = re.sub(r"<reasoning>.*?</reasoning>\s*", "", formatted_response, flags=re.DOTALL)
        
        # Try XML tag-based formatting first
        if "<root_cause_summary>" in formatted_response and "<troubleshooting_steps>" in formatted_response:
            # Replace opening tags with markdown headers
            formatted_response = re.sub(r"<root_cause_summary>\s*", "### 🧩 Root Cause Summary\n\n", formatted_response)
            formatted_response = re.sub(r"<troubleshooting_steps>\s*", "\n\n### 🛠️ Troubleshooting Steps\n\n", formatted_response)
            
            # Remove closing tags
            formatted_response = re.sub(r"\s*</root_cause_summary>\s*", "\n", formatted_response)
            formatted_response = re.sub(r"\s*</troubleshooting_steps>\s*", "\n", formatted_response)
            
        else:
            # Fallback if unstructured - look for common patterns
            formatted_response = re.sub(r"(?i)^Root Cause(?: Summary)?:?\s*", "### 🧩 Root Cause Summary\n\n", formatted_response, flags=re.MULTILINE)
            formatted_response = re.sub(r"(?i)^Troubleshooting Steps?:?\s*", "\n\n### 🛠️ Troubleshooting Steps\n\n", formatted_response, flags=re.MULTILINE)

        # Clean up any remaining XML tags (including stray response tags)
        formatted_response = re.sub(r"</?(?:response|task|instruction)[^>]*>", "", formatted_response, flags=re.IGNORECASE)
        formatted_response = re.sub(r"<[^>]+>", "", formatted_response)
        
        # Clean up multiple newlines
        formatted_response = re.sub(r"\n{3,}", "\n\n", formatted_response)
        
        # Add spacing after numbered list items for better readability
        formatted_response = re.sub(r"(\n\d+\.\s)", r"\n\1", formatted_response)

        return formatted_response.strip()

    def format_judge_score(self, judge_text: str) -> str:
        # Clean up any XML tags first
        cleaned_text = re.sub(r"</?(?:rating|score|explanation|model)[^>]*>", "", judge_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"<[^>]+>", "", cleaned_text)
        
        # Look for XML-style score pattern first
        xml_match = re.search(r"(\d(?:\.\d)?)\s*</score>\s*<explanation>(.*?)</explanation>", cleaned_text, re.DOTALL)
        if xml_match:
            score = xml_match.group(1)
            justification = xml_match.group(2).strip()
            return f"### Score: {score}/5\n\n### Justification:\n{justification}"
        
        # Look for score at the beginning of the text
        match = re.match(r"^\s*(\d(?:\.\d)?)[\.\s\-:]*(.*)", cleaned_text, re.DOTALL)
        if match:
            score = match.group(1)
            justification = match.group(2).strip()
            return f"### Score: {score}/5\n\n### Justification:\n{justification}"
        
        # Alternative pattern - look for "Score: X" anywhere in text
        score_match = re.search(r"(?i)score:?\s*(\d(?:\.\d)?)", cleaned_text)
        if score_match:
            score = score_match.group(1)
            # Remove the score line and use the rest as justification
            justification = re.sub(r"(?i)score:?\s*\d(?:\.\d)?\s*", "", cleaned_text).strip()
            return f"### Score: {score}/5\n\n### Justification:\n{justification}"        
            
        return cleaned_text.strip()