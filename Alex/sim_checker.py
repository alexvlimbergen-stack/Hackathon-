import difflib #lett checks 
from pypdf import PdfReader
import os #voor title van file als metadata leeg is
import re
from ollama import chat
from collections import Counter
import math
import PyPDF2


class File(): #class name is hash
    def __init__(self,title,txt,file_type):
        self.title = title
        self.txt = txt #de txt moet gescraped worden van de file 
        self.type = file_type

    def is_exact_match(self,other_file):
        return (self.title==other_file.title) and (self.txt==other_file.txt)

    def title_match(self,other_file):
        return (self.title==other_file.title)

    def txt_match(self,other_file):
        return  (self.txt==other_file.txt)

    #dit is voor pdf's kan ook nog geimplementeerd worden voor andere types
    @classmethod 
    def from_pdf(cls,file_path): 
        reader = PdfReader(file_path)

        #voor title
        bestandsnaam = os.path.basename(file_path) 
        metadata = reader.metadata
        pdf_title = metadata.title if metadata and metadata.title else os.path.splitext(bestandsnaam)[0]

        

        #voor inhoud
        complete_txt = ""
        for page in reader.pages:
            txt_page = page.extract_text()
            if txt_page:
                complete_txt += txt_page + "\n"

        return cls(pdf_title,complete_txt,"txt")

    def clean_and_tokenize(self):
        text = self.txt
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return words

    def calculate_cosine_similarity(self,other_file):
        words1 = self.clean_and_tokenize()
        words2 = other_file.clean_and_tokenize()
        
        if not words1 or not words2:
            return 0.0
            
        vec1 = Counter(words1)
        vec2 = Counter(words2)
        
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator








def main(path1,path2):

    #init files
    temphash_main_file = File.from_pdf(path1)
    temphash_file2 = File.from_pdf(path2)

    if (temphash_main_file.title_match(temphash_file2)):
        print("title bestaat al")

    if (temphash_main_file.txt_match(temphash_file2)):
        print("file heeft exacte match")
        return "exact copy found"

    #sim checker voor niet exacte 
    similarity = temphash_main_file.calculate_cosine_similarity(temphash_file2)*100
    print(similarity,'%')

    if 100>similarity>80:
        messages = [
    {
        'role': 'system',
        'content': (
            "You are a database gatekeeper. Your job is to compare two texts and decide if they should both exist in the database (COEXIST) or if they are redundant/conflicting.\n"
            "CRITICAL RULE: If the texts contain a DIFFERENT name or a DIFFERENT company, they MUST BOTH COEXIST in the database.\n"
            "Output your final decision strictly in this JSON format, with no other text, thinking, or introduction:\n"
            '{"decision": "COEXIST" or "REPLACE", "reason": "A short 1-sentence explanation in English"}'
        )
    },
    {
        'role': 'user',
        'content': (
            f"--- FIRST CONTENT (Most Recent) ---\n{temphash_main_file.txt}\n\n"
            f"--- SECOND CONTENT ---\n{temphash_file2.txt}"
        )
    }
]

    response = chat(model='qwen3:0.6B',messages=messages,think=False)
    print(response['message']['content'])
    return response['message']['content']

