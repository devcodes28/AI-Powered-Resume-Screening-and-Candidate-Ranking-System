import pdfplumber
import docx
import os
import re

def extract_text_from_pdf(file_path):
    """Extracts raw text data line-by-line from a PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_path):
    """Extracts raw text fields sequentially from a Microsoft Word Document."""
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def parse_resume(file_path):
    """Factory parser to funnel documents based on file type extensions."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported File Extension Format Passed")

def extract_contact_info(text):
    """Basic regex engine to capture metrics like Email and Phone from resume text."""
    email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'
    phone_regex = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    
    email_match = re.search(email_regex, text)
    phone_match = re.search(phone_regex, text)
    
    email = email_match.group(0) if email_match else "Unknown"
    phone = phone_match.group(0) if phone_match else "Unknown"
    
    return email, phone