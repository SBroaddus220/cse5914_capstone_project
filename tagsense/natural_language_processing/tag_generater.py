from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List
import os




chat = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key= os.getenv("OPENAI_API_KEY"), 
    openai_api_base='https://tbnx.plus7.plus/v1',
    max_tokens=1024
)


template_string = """Extract keywords from the following sentence \
that is delimited by triple backticks \
into a style that is {style}. \
text: ```{text}```\
"""


prompt_template = ChatPromptTemplate.from_template(template_string)
customer_style = """tags \
tags can contain mutiple words seperated by '_'\
most meaingful combination\
seperated by comma\
don't show 'photos' or 'pictures' related tags unless it appears twice or more\
also generate 2 related tags\
no other words but tags\
"""
# customer_text = input("Write something here: ")
# customer_messages = prompt_template.format_messages(
#                     style=customer_style,
#                     text=customer_text)
# # Call the LLM to translate to the style of the customer message
# # Reference: chat = ChatOpenAI(temperature=0.0)
# customer_response = chat.invoke(customer_messages, temperature=0)
# print(customer_response.content)


def get_tags_from_text(text: str) -> List[str]:
    customer_messages = prompt_template.format_messages(
        style=customer_style,
        text=text
    )
    customer_response = chat.invoke(customer_messages, temperature=0)
    tags = customer_response.content.strip().split(', ')
    return tags