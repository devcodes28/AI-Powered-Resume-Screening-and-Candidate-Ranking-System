import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Quietly ensure the required NLTK tokenization packages are present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

def preprocess_text(text):
    """
    Standardizes input strings by stripping special characters, numbers, 
    and common English stopwords for clean vector text analysis.
    """
    if not text or not isinstance(text, str):
        return ""
        
    # Convert text to lowercase structure
    text = text.lower()
    
    # Remove alphanumeric punctuation symbols and digits
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # Tokenize text string into separate terms
    words = word_tokenize(text)
    
    # Filter out common English stop words
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words]
    
    return " ".join(filtered_words)

# Alias definition to cover legacy structural imports if needed
clean_text = preprocess_text