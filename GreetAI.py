from flask import Flask, render_template, request, session
from flask_wtf import FlaskForm

from wtforms import SelectField
from wtforms import StringField, SelectField

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import utils
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from pprint import pprint

from dropbox_sign import \
    ApiClient, ApiException, Configuration, apis, models

import openai
from PIL import Image

import requests 

#add your openai api key
api_key = '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'


configuration = Configuration(
    # Configure HTTP basic authorization: api_key
    username="086d082524f570dcc388273267a37577fe96e122148a25baa52acdfa8bfacb78",

    # or, configure Bearer (JWT) authorization: oauth2
    # access_token="YOUR_ACCESS_TOKEN",
)

app = Flask(__name__)
app.secret_key = 'b10e5928d7f81eba2c6368cd963a5f6d'

# receiver_name = "Unknown"
# receiver_occassion = "Unknown"

@app.route('/')
def hello_world():
    return 'Welcome to GreetAI'

# Create a form with a textbox and a dropdown
class MyForm(FlaskForm):
    text_input_name = StringField('Name of card receiver')
    dropdown_occassion = SelectField('Occassion : ', choices=[('Birthday', 'Birthday'), ('graduation', 'Graduation'), ('Wedding Anniversary', 'Wedding Anniversary')])
    text_input_age = StringField('Age')
    dropdown_season = SelectField('Favourite Season : ', choices=[('spring', 'Spring'), ('autumn', 'Autumn'), ('summer', 'Summer')])
    dropdown_specials = SelectField('Special gift : ', choices=[('Baloon', 'Baloons'), ('Bandle', 'Candles'), ('Bhocolate', 'Chocolates')])

@app.route('/details_form', methods=['GET', 'POST'])
def details_form():
    form = MyForm()

    if form.validate_on_submit():
        session['receiver_name'] = form.text_input_name.data
        session['receiver_occassion'] = form.dropdown_occassion.data

        prompt = form.dropdown_occassion.data + "card for a " + form.text_input_age.data + "years old"
        prompt += form.dropdown_season.data + "theme and colors and lots of" + form.dropdown_specials.data + "."
        process_text(prompt)
        return f"Success !!"

    return render_template('details_form.html', form=form)

class MyFormSigners(FlaskForm):
    text_input_name1 = StringField('Name of signer 1')
    text_input_email1 = StringField('Email of signer 1')    
    text_input_name2 = StringField('Name of signer 2')
    text_input_email2 = StringField('Email of signer 2')

@app.route('/signers_details', methods=['GET', 'POST'])
def signers_details():
    form = MyFormSigners()

    if form.validate_on_submit():
        process_upload_to_sign (form.text_input_name1.data, form.text_input_email1.data, form.text_input_name2.data, form.text_input_email2.data)
        return f"Success !"

    return render_template('signers_details.html', form=form)

@app.route('/text_box_form', methods=['GET'])
def text_box_form():
    return render_template('text_box.html')

#@app.route('/process_text', methods=['POST'])
def process_text(prompt):
    user_input = request.form.get('user_input')
    # Do something with the user_input, e.g., process it or display it
    
    pdf_file = "D:/GreetAI/Greetings.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)

    generate_and_save_image(prompt, 'D:/GreetAI/generated.png')

    image_path = "D:/GreetAI/generated.png"  # Replace with the path to your image file
    img = utils.ImageReader(image_path)
    c.drawImage(img, 200, 400, 256, 256)  # Adjust coordinates and dimensions as needed

    birthday_prompt = "Generate a " + session['receiver_occassion'] + " quote: May your day be filled with joy and laughter, as bright as the candles on your cake."
    generated_quote = generate_quote(birthday_prompt)
    #generated_quote = birthday_prompt

    #c.drawString(100, 750, user_input)
    TitleText = "Happy " + session['receiver_occassion'] + " " + session['receiver_name'] + " !!"
    #c.drawCentredString(200, 400 - inch, TitleText)
    textobject = c.beginText(200, 400 - inch) 
    textobject.setFont("Helvetica-Bold", 12)
    textobject.textOut(TitleText)
    c.drawText(textobject)

    textbox_text = generated_quote
    width, height = letter
    textbox_width = 6 * inch
    textbox_height = 3 * inch
    x = (width - textbox_width) / 2
    y = inch #height - 2 * inch
    #c.drawString(x, y + textbox_height + 12, "Text Box:")
    #c.rect(x, y, textbox_width, textbox_height)
    textbox_style = getSampleStyleSheet()['Normal']
    textbox_style.fontSize = 14
    textbox_style.leading = 18
    textbox_style.backColor = '#FFFF00'
    textbox = Paragraph(textbox_text, textbox_style)
    textbox.wrap(textbox_width, textbox_height)
    textbox.drawOn(c, x, y + 2*inch)
    
    c.showPage()
    c.save()


    return f'You entered: {user_input}'

def generate_quote(prompt):
    openai.api_key = api_key

    # Generate a birthday quote using the GPT-3 model
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    #print(response)
    # Extract the generated quote from the response
    quote = completion.choices[0].message.content
    print(completion.choices[0].message.content)
    return quote

def generate_and_save_image(prompt, filename):
    # Make the API request to generate an image
    response = openai.Image.create(
        #model="image-alpha-001",  # Choose the DALL·E model you want to use
        prompt=prompt,
        n=1,  # Number of images to generate
        size="256x256",  # Size of the generated image
        api_key=api_key
    )
    #print(response)
    # Extract the image data from the response's 'data' attribute
    image_url = response["data"][0]["url"]

    image_data = requests.get(image_url, stream=True) 

    with open("D:/GreetAI/generated.png", "wb") as f: 
        f.write(image_data.content)

@app.route('/upload_to_sign')
def upload_to_sign():
    return render_template('upload_to_sign.html')

@app.route('/process_upload_to_sign', methods=['POST'])
def process_upload_to_sign(name1, email1, name2, email2):

    # with ApiClient(configuration) as api_client:
    #     signature_request_api = apis.SignatureRequestApi(api_client)

    signer_1 = models.SubSignatureRequestSigner(
        email_address=email1,
        name=name1,
        order=0,
    )

    # signer_2 = models.SubSignatureRequestSigner(
    #     email_address=email2,
    #     name=name2,
    #     order=1,
    # )

    signing_options = models.SubSigningOptions(
        draw=True,
        type=True,
        upload=True,
        phone=True,
        default_type="draw",
    )

    # field_options = models.SubFieldOptions(
    #     date_format="DD - MM - YYYY",
    # )
    data = models.SignatureRequestSendRequest(
        title="Happy " + session['receiver_occassion'] + " " + session['receiver_name'],
        subject="Sign " + session['receiver_occassion'] + " Card",
        message="Please sign this " + session['receiver_occassion'] + " card with best wishes",
        #signers=[signer_1, signer_2],
        signers=[signer_1],
        # cc_email_addresses=[
        #     "lawyer1@dropboxsign.com",
        #     "lawyer2@dropboxsign.com",
        # ],
        files=[open("D:/GreetAI/Greetings.pdf", "rb")],
        metadata={
            "custom_id": 1234,
            "custom_text": "NDA #9",
        },
        signing_options=signing_options,
        #field_options=field_options,
        test_mode=True,
    )

    global signature_request_id

    try:
        response = signature_request_api.signature_request_send(data)
        signature_request_id = response["signature_request"]["signature_request_id"]
        pprint(response)
    except ApiException as e:
        print("Exception when calling Dropbox Sign API: %s\n" % e)

    #return f'Response for Dropbox Signature request API: {signature_request_id}'

@app.route('/download_from_sign')
def download_from_sign():
    return render_template('download_from_sign.html')

@app.route('/process_download_from_sign', methods=['POST'])
def process_download_from_sign():
    try:
        signature_request_id = '243c1ae3d46d3d81e0568ec6d76c0a186d2ad5c9'
        response = signature_request_api.signature_request_files(signature_request_id, file_type="pdf")
        open('D:/GreetAI/signed-Greetings.pdf', 'wb').write(response.read())
    except ApiException as e:
        print("Exception when calling Dropbox Sign API: %s\n" % e)
    return f"Success !"

if __name__ == '__main__':

    with ApiClient(configuration) as api_client:
        signature_request_api = apis.SignatureRequestApi(api_client)
        app.run()
