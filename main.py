import streamlit as st
import base64
import openai
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
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

# Function to encode the image
def encode_image(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    return base64_image

# Set up the columns
left_column, main_column, right_column = st.columns([1, 2, 1])

# Add content to the left column
with left_column:
    st.write("""
    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    <h2 style="color: #1a1a1a; font-size: 32px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px;">Unleash the Power of GPT Vision</h2>
    <p style="color: #4c4c4c; text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
    Unlock the secrets hidden within your images with <strong style="color: #007bff;">GPT Vision</strong>. This cutting-edge technology harnesses the power of OpenAI's language models to analyze and interpret visual data like never before.
    </p>
    <p style="color: #4c4c4c; text-align: justify; font-size: 18px; line-height: 1.6;">
    From extracting tabular data to identifying locations, GPT Vision is your gateway to a world of visual insights. Experience the future of image analysis today!
    </p>
    </div>
    """, unsafe_allow_html=True)

# Add your main component to the middle column
with main_column:
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

# Add content to the right column
with right_column:
    st.write("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    <p style="color: #333333; font-family: 'Arial', serif; font-size: 16px; line-height: 1.5;"><strong>Extract the table from this image:</strong> Effortlessly extract tabular data from any image, making data analysis a breeze.</p>
    
    <p style="color: #333333; font-family: 'Arial', serif; font-size: 16px; line-height: 1.5;"><strong>Tell me where this photo was taken:</strong> Uncover the location depicted in your photos, unlocking a world of geographical context.</p>

    <p style="color: #333333; font-family: 'Arial', serif; font-size: 16px; line-height: 1.5;"><strong>Extract the writing from this whiteboard:</strong> Capture your notes and turn them into structured text.</p>
    
    <p style="color: #333333; font-family: 'Arial', serif; font-size: 16px; line-height: 1.5;"><strong>Describe the objects in this scene:</strong> Get detailed descriptions of the objects, people, and elements present in your images.</p>
    </div>
    """, unsafe_allow_html=True)
