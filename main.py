import streamlit as st
import base64
import openai
import requests
from pdf2image import convert_from_bytes
from io import BytesIO

st.set_page_config(layout="wide")

# Use Streamlit's secret management to safely store and access your API key
api_key = st.secrets["OPENAI_API_KEY"]

# Function to encode the image
def encode_image(image):
   buffered = BytesIO()
   image.save(buffered, format="PNG")
   base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
   return base64_image

# Add your main component
st.header('Upload a PDF below, and ask ChatGPT a question about it:')
# File uploader
uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

# Check if a file was uploaded
if uploaded_file is not None:
   # Convert PDF to images
   pdf_images = convert_from_bytes(uploaded_file.read())
   
   # Display each page of the PDF as an image
   for page_num, pdf_image in enumerate(pdf_images, start=1):
       st.image(pdf_image, use_column_width=True, caption=f"Page {page_num}")
       
       # Request input
       request = st.text_input(f"Type your question for page {page_num} here:")
       
       # Submit button
       if st.button(f"Submit for page {page_num}"):
           # Encode the PDF image
           base64_image = encode_image(pdf_image)
           
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
