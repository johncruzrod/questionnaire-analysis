import streamlit as st
import base64
import requests
import pdf2image
from PIL import Image
import io

st.set_page_config(layout="wide")

# Use Streamlit's secret management to safely store and access your API key
api_key = st.secrets["OPENAI_API_KEY"]

# Function to convert PDF file to images
def convert_pdf_to_images(pdf_file):
    images = pdf2image.convert_from_bytes(pdf_file.read())
    return images

# Function to encode the image
def encode_image(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    return base64_image

st.header('Upload a PDF below, and ask ChatGPT a question about it:')

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

# Display the uploaded PDF as images
if uploaded_file is not None:
    images = convert_pdf_to_images(uploaded_file)
    for image in images:
        st.image(image, use_column_width=True)

# Request input
request = st.text_input("Type your question here:")

# Submit button
if st.button("Submit"):
    if uploaded_file is not None:
        # Process each page/image in the PDF
        for image in images:
            # Encode the image
            base64_image = encode_image(image)
            # Prepare the headers for the HTTP request to OpenAI API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            # Prepare the payload with the encoded image and the user's request
            payload = {
                "model": "gpt-4-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": request
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4000
            }
            # Show the loading wheel
            with st.spinner("Processing your request..."):
                try:
                    # Make the HTTP request to the OpenAI API
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    # Check the response status and display the output or an error message
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
    else:
        st.warning("Please upload a PDF file.")

