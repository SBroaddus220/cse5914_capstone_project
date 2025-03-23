# -*- coding: utf-8 -*-

"""
Natural language generator for processing and generating tags from natural language.
"""

# **** LOGGING ****
import os
import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from tagsense.util import QueryValidator

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class NaturalLanguageGenerator:
    def generate_tags_from_text(self, text: str) -> List[str]:
        """Generate a list of tags from the given text."""
        raise NotImplementedError("This method must be implemented in a subclass.")
        
    def validate_tag_query(self, tag_query: str) -> bool:
        """
        Validates the format of the given tag query.
        
        Args:
            tag_query (str): The tag query to validate.
        
        Returns:
            bool: True if the tag query is valid, False otherwise.
        """
        return QueryValidator.validate_query(tag_query)

    def parse_tag_queries_from_query(self, text: str) -> List[str]:
        """
        Parses tag queries from the given text.
        
        Args:
            text (str): The text from which to extract tag queries.
        
        Returns:
            List[str]: A list of extracted tag queries.
        """
        return [match['query'] for match in QueryValidator.find_queries(text)]

    def parse_tags_from_query(self, tag_query: str) -> List[str]:
        """
        Parses tags from the given tag query.
        
        Args:
            tag_query (str): The tag query from which to extract tags.
        
        Returns:
            List[str]: A list of extracted tags.
        """
        matches = QueryValidator.find_queries(tag_query)
        if not matches:
            return []
        if len(matches) > 1:
            logger.warning("Multiple tag queries found in the text. Using the first one.")
        return matches[0]['tags']


class OpenAINaturalLanguageGenerator(NaturalLanguageGenerator):
    
    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4",
        openai_api_base: str = "https://api.openai.com/v1",
        max_tokens: int = 1024,
        temperature: float = 0.0
    ):
        self.chat_model = ChatOpenAI(
            model=model_name,
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            max_tokens=max_tokens
        )

    def _generate_prompt(self, text: str) -> str:
        self.tag_prompt_usage_instructions = r"""
# Searching
## Basic Search
```
tag1 tag2
```
Search for posts that contain both `tag1` and `tag2`.
```
tag1 and tag2
```
Same as above.
```
tag1 or tag2
```
Search for posts that contain either `tag1`, `tag2`, or both.
## Exclusion
```
-tag1 -tag2
```
Search for posts that do not contain `tag1` or `tag2`.
```
-(tag1 tag2)
```
Search for posts that do not contain both `tag1` and `tag2` together (but may contain either one individually or neither).
## Grouping and Combinations
```
(tag1 tag2) or (tag3 tag4)
```
Search for posts that contain either both `tag1` and `tag2` or both `tag3` and `tag4`.
"""

        # k-shot examples to guide the model
        self.k_shot_examples = [
            {
                "text": "A dog being walked outside.",
                "tag_query": "dog leash grass",
                "available_tags": "dog leash chair wheels grass airplane"
            },
            {
                "text": "Someone riding either a bike or a skateboard.",
                "tag_query": "bicycle or skateboard",
                "available_tags": "couch bicycle microscope skateboard plate"
            },
            {
                "text": "A street with no cars on it.",
                "tag_query": "-car street",
                "available_tags": "crab street mountain rug floor car"
            },
            {
                "text": "A cat alone in a room.",
                "tag_query": "cat -(couch person)",
                "available_tags": "person dog turtle cat sidewalk couch tree"
            },
            {
                "text": "Either a park bench under a tree or a streetlight next to a sidewalk.",
                "tag_query": "(tree bench) or (lamp sidewalk)",
                "available_tags": "hat tree jewelry horse bench fish laptop lamp pen sidewalk television"
            },
            {
                "text": "Curtains blowing near a window, with no people around.",
                "tag_query": "window or curtain -person",
                "available_tags": "curtain person fruit window apple pizza "
            },
            {
                "text": "Indoor furniture arrangements like a chair and table, or a bed and pillow, but without blankets.",
                "tag_query": "(chair table) or (bed pillow) -blanket",
                "available_tags": "flower chair cloud table pen television bed pillow blanket"
            },
            {
                "text": "An airplane taking off or landing on a runway.",
                "tag_query": "airplane runway",
                "available_tags": "coffee chair airplane runway car truck bicycle"
            },
            {
                "text": "A nest in a tree or a bird perched nearby.",
                "tag_query": "bird or nest",
                "available_tags": "bird nest tree sky airplane car"
            },
            {
                "text": "A setting with no visible phones or laptops.",
                "tag_query": "-phone -laptop",
                "available_tags": "phone tree sky laptop airplane car"
            },
            {
                "text": "A truck alone on a highway.",
                "tag_query": "truck highway -car",
                "available_tags": "highway car airplane truck tree"
            },
            {
                "text": "An image that shows either a book or a cup, but not both together.",
                "tag_query": "(book or cup) and -(book cup)",
                "available_tags": "book camera drone forest cup tree sky airplane car"
            }
        ]
 
        # Generate string for k-shot tags
        examples_string = ""
        for example in self.k_shot_examples:
            examples_string += f"""<user_request>
{example["text"]}
</user_request>
<tag_query>
{example["tag_query"]}
</tag_query>
"""

        # Create the template string
        template_string = f"""
<instructions>
You are a tag extraction system. Here are the guidelines for tag queries:
{self.tag_prompt_usage_instructions}
Please provide a response by completing the following tag query by providing a response.
</instructions>
{examples_string}
<user_request>
{text}
</user_request>
<tag_query>""" + "{text}\n</tag_query>"
        return template_string

    def generate_tags_from_text(self, text: str) -> List[str]:
        logger.info(f"Generating tags from text: {text}")
        self.template_string = self._generate_prompt(text)
        self.prompt_template = ChatPromptTemplate.from_template(self.template_string)

        # Format the prompt messages
        formatted_messages = self.prompt_template.format_messages(text=text)
        logger.debug(f"Formatted prompt messages: {formatted_messages}")
        
        # Call the LLM to generate tags from the text
        response = self.chat_model.invoke(formatted_messages, temperature=0.0)
        logger.debug(f"Raw model response: {response.content}")
        
        # Parse and extract tags
        tag_query = response.content.strip().split("<tag_query>")[-1].strip()
        tag_query = tag_query.split("</tag_query>")[0].strip()

        tag_queries = self.parse_tag_queries_from_query(tag_query)
        tags = self.parse_tags_from_query(tag_queries[0])
        
        return tags

# ****
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    open_ai_key = os.getenv("OPENAI_API_KEY")
    generator = OpenAINaturalLanguageGenerator(open_ai_key)
    text = "A cat sitting on a windowsill."
    tags = generator.generate_tags_from_text(text)
    print(tags)
