import streamlit as st
import base64
import requests
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(layout="wide")

api_key = st.secrets["OPENAI_API_KEY"]

# Function to convert PDF file to images
def convert_pdf_to_images(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    images = []
    for page in doc:
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)
    return images

# Function to encode the image
def encode_image(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    return base64_image

st.header('Upload a PDF below, and ask ChatGPT a question about it:')

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    images = convert_pdf_to_images(uploaded_file)
    
    for i, image in enumerate(images, start=1):
        st.image(image, use_column_width=True, caption=f"Page {i}")
    
    request = st.text_input("Type your question here:")
    
    if st.button("Submit"):
        image_urls = []
        for image in images:
            base64_image = encode_image(image)
            image_urls.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
            })
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": request
                        }
                    ] + image_urls
                }
            ],
            "max_tokens": 4000
        }
        
        with st.spinner("Processing your request..."):
            try:
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                
                if response.status_code == 200:
                    response_json = response.json()
                    output = response_json["choices"][0]["message"]["content"]
                    st.markdown(output, unsafe_allow_html=True)
                else:
                    error_message = f"An error occurred while processing the request. Status code: {response.status_code}"
                    error_details = response.text
                    st.error(error_message)
                    st.error(f"Error details: {error_details}")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred while making the request: {str(e)}")
