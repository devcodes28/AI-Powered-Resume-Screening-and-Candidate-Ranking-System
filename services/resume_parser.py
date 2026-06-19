import re

def extract_resume_text(file_path):
    """
    Extracts raw text content from an uploaded resume file path.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file path {file_path}: {str(e)}")
        return ""

def parse_resume_fields(text):
    """
    Extracts structured fields like email and phone numbers from raw resume text matrices.
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\b\d{10}\b|\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
    
    email = re.search(email_pattern, text)
    phone = re.search(phone_pattern, text)
    
    return {
        "email": email.group(0) if email else "Not Found",
        "phone": phone.group(0) if phone else "Not Found"
    }
