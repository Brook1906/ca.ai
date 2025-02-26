import requests
import fitz  # PyMuPDF
import re
import pandas as pd

pdf_url = "https://www.incometax.gov.in/iec/foportal/sites/default/files/2024-04/CBDT_e-Filing_ITR%201_Validation%20Rules_AY2024-25_V1.0..pdf"
response = requests.get(pdf_url)
if response.status_code == 200:
    with open("downloaded_pdf.pdf", 'wb') as pdf_file:
        pdf_file.write(response.content)
    print("PDF file downloaded successfully.")
else:
    print(f"Failed to download the PDF file. Status code: {response.status_code}")

# Main Extract Text idhar se from the PDF
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

pdf_file_path = "downloaded_pdf.pdf"
extracted_text = extract_text_from_pdf(pdf_file_path)
print("Text extracted from PDF.")

# OCR method durse code me karuga abhi ke liye Clean the Extracted Text
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    return text

cleaned_text = clean_text(extracted_text)
print("Text cleaned successfully.")

# Step 4: Save the Cleaned Data
with open("cleaned_text.txt", 'w', encoding='utf-8') as txt_file:
    txt_file.write(cleaned_text)
print("Cleaned text saved to cleaned_text.txt.")

# remove all unwanted data and  Prepare Data for Fine-Tuning
data = {
    'question': ["What are the validation rules for ITR 1?"],
    'answer': [cleaned_text]
}
df = pd.DataFrame(data)
df.to_csv("fine_tune_data.csv", index=False)
print("Data prepared for fine-tuning and saved to fine_tune_data.csv.")

