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
main_column, right_column = st.columns([2, 1])

# Add your main component to the middle column
with main_column:
    st.title('Upload PDF')
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        images = convert_pdf_to_images(uploaded_file)
        
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
            
            prompt = """
            Please analyze the attached form image based on the following criteria:
            
            1. Identify the type of form being sent (e.g., Travel Questionnaire, Diving, Aviation, Sailing, Motorsport, or Mountaineering).
            
            2. Apply the appropriate criteria for the identified form type:
            
            Travel Questionnaire:
            - Check for medical requirements, especially for foreign residence. Note to check with insurers for any overseas residence.
            - Europe and Russia: Typically no issues medically in western parts, but eastern Europe may require HIV and/or Hep screening. Travel is normally fine for western Europe, but eastern areas require some diligence.
            - North America: Typically no issues medically or travel-related.
            - Middle East: Countries require individual consideration both medically and travel risk.
            - Central America: Typically no extra meds other than Belize and Panama, which need HIV and Hep screening. Travel needs to be considered due to risk.
            - South America: More developed countries usually okay for meds, but poorer countries will need HIV/Hep screening. Some countries will need review on travel due to risks.
            - Asia: High chance of HIV requirement, and some countries also need Hep B. Travel will need to be assessed as well.
            - Australasia: Largely fine for HIV and Hep, but Papua New Guinea needs both testing. Travel usually fine but will need reviewing for Papua New Guinea.
            - Antarctica: Medically fine, but travel needs to be reviewed.
            - Caribbean: Review meds, as HIV and Hep are likely. Travel to be considered in some areas.
            - Africa: Review meds, as HIV and Hep are likely. Travel to be considered in most areas.
            
            Diving:
            - Leisure diving up to 30ms is typically fine when the individual is qualified. Anything above that could become ratable.
            - If the number of dives is above 9, provide a trigger to review.
            - If any of the tick boxes in diving activities are positively answered, generate a trigger to review.
            - The same applies to free diving.
            
            Aviation:
            - Trigger a check on all cases, as most are likely to be ratable.
            
            Sailing:
            - Trigger if sailing over 15 days.
            - Trigger if racing is ticked.
            - Trigger if anything above inland and enclosed tidal waters is ticked, as it starts to run the risk of ratings.
            
            Motorsport:
            - Trigger all cases, as they are likely to be very complex due to the vast amount of variation.
            
            Mountaineering:
            - Trigger for anything above amateur level.
            - Trigger for anything other than Indoor, Climbing park, Hiking, or Trekking (unless over 3000ms).
            - Trigger for anything over 3000ms, solo, or Frequency over 1.
            - Trigger for anything over UIAA IV+, British Technical grade greater than 4a, and Yosemite decimal system YDS over 5.5.
            - Any other entry should be referred.
            
            Do not provide an in depth analysis of the form! Only reply with information related to the criteria above, and what information is relevant.
            """
            
            payload = {
                "model": "gpt-4-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
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
    if uploaded_file is not None:
        for i, image in enumerate(images, start=1):
            st.image(image, use_column_width=True, caption=f"Page {i}")
