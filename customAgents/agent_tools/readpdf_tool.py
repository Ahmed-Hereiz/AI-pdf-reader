import re
import PyPDF2
from customAgents.agent_tools import BaseTool


class PDFDocReaderTool(BaseTool):
    def __init__(
            self,
            description: str = "Tool used to read data in pdf",
            tool_name: str = None,
            ):
        
        super().__init__(description, tool_name)
    
    
    def execute_func(self, pdf_path) -> str:
        
        text = ""
        pdf_path = self._clean_path(pdf_path)
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text 
    

    def _clean_path(self, text: str) -> str:
        cleaned_text = re.sub(r'(?<=\.pdf)\n', '', text)
        return cleaned_text