from customAgents.agent_llm import SimpleMultiModal, SimpleStreamLLM
from customAgents.agent_prompt import SimplePrompt
from customAgents.runtime import SimpleRuntime
import json

with open("llm.json", "r") as f:
    config = json.load(f)


def translate_ai(target_language, image):
    translate_text_prompt = f"Translate the following text in the image to {target_language}: (if the image is already on the target language, do not translate just clarify so then extract the text inside the image) JUST OUTPUT the translation directly without saying this is the translation of the text"
    translate_llm = SimpleMultiModal(api_key=config["api_key"], model=config["model"], temperature=0.5)
    translate_prompt = SimplePrompt(text=translate_text_prompt, image=image)
    translate_prompt.construct_prompt()
    translate_agent = SimpleRuntime(llm=translate_llm, prompt=translate_prompt)
    
    for output in translate_agent.loop():
        yield output


def explain_ai(full_page_text, image):
    explain_text_prompt = f"Explain and illustrate for the user the image he sent, try to explain the visuals or the text with better illustrations to help the user understand the context he passed to you, given this is the full page's context if it is gonna help, make sure to explain the part he gave to you in the image {full_page_text}"
    explain_llm = SimpleMultiModal(api_key=config["api_key"], model=config["model"], temperature=0.5)
    explain_prompt = SimplePrompt(text=explain_text_prompt, image=image)
    explain_prompt.construct_prompt()
    translate_agent = SimpleRuntime(llm=explain_llm, prompt=explain_prompt)
    
    for output in translate_agent.loop():
        yield output


def ask_ai(question, full_page_text, image):
    ask_text_prompt = f"Please provide a detailed answer to the following question based on the context provided in the image: '{question}'. Additionally, consider the full page context: '{full_page_text}'."
    ask_llm = SimpleMultiModal(api_key=config["api_key"], model=config["model"], temperature=0.5)
    ask_prompt = SimplePrompt(text=ask_text_prompt, image=image)
    ask_prompt.construct_prompt()
    ask_agent = SimpleRuntime(llm=ask_llm, prompt=ask_prompt)
    
    for output in ask_agent.loop():
        yield output


def chat_ai(message):
    chat_text_prompt = f"User said: '{message}'. Please respond in a conversational manner."
    chat_llm = SimpleStreamLLM(api_key=config["api_key"], model=config["model"], temperature=0.5)
    chat_prompt = SimplePrompt(text=chat_text_prompt)
    chat_prompt.construct_prompt()
    chat_agent = SimpleRuntime(llm=chat_llm, prompt=chat_prompt)
    
    for output in chat_agent.loop():
        yield output


def notes_ai(full_page_text, image):
    notes_text_prompt = f"Please provide a detailed summary of the following text: '{full_page_text}'. Additionally, consider the full page context: '{full_page_text}' Make sure to return the output as md and lines seperated by <br> tags for good view. preferred to make the notes as bullet points try to make 5 to 8 points max, don't write explainations just the notes directly as bullet points only"
    notes_llm = SimpleMultiModal(api_key=config["api_key"], model=config["model"], temperature=0.5)
    notes_prompt = SimplePrompt(text=notes_text_prompt, image=image)
    notes_prompt.construct_prompt()
    notes_agent = SimpleRuntime(llm=notes_llm, prompt=notes_prompt)
    
    return notes_agent.loop()

# def test_functions():
#     # Test data
#     test_image = "/home/ahmed-hereiz/self/pdf-AI-reader/tmp/pdf_ai_tmp_image_.png"
#     test_language = "Spanish"
#     test_question = "What is the main idea of the image?"
#     test_full_page_text = "This is the full context of the page."

#     # Test translate_ai function
#     print("Testing translate_ai...")
#     for output in translate_ai(test_language, test_image):
#         print("Translate Output:", output)

#     # Test explain_ai function
#     print("Testing explain_ai...")
#     for output in explain_ai(test_full_page_text, test_image):
#         print("Explain Output:", output)

#     # Test ask_ai function
#     print("Testing ask_ai...")
#     for output in ask_ai(test_question, test_full_page_text, test_image):
#         print("Ask Output:", output)

#     # Test chat_ai function
#     print("Testing chat_ai...")
#     for output in chat_ai("Hello, how are you?"):
#         print("Chat Output:", output)

# test_functions()