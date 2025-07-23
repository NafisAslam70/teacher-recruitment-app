from flask import Flask, request, render_template, jsonify, send_from_directory, session, redirect, url_for
import os
import re
from werkzeug.utils import secure_filename
import PyPDF2
from urllib.parse import quote
from flask_session import Session

app = Flask(__name__)

# Configure session
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key in production
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
Session(app)

# Configure upload directory
UPLOAD_FOLDER = 'Uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}
YOUR_WHATSAPP_NUMBER = '+601112079684'

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Hardcoded credentials
HARDCODED_CREDENTIALS = {
    'username': 'admin',
    'password': 'adminnn123'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_phone_number(number):
    number = re.sub(r'[-.\s]', '', number)
    if not re.match(r'^\+?\d{10,12}$', number):
        return None
    return number if number.startswith('+') else f'+91{number}'

def extract_info(text):
    # Extract name
    name_match = re.search(r'Name\s*[:\-]?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r'^([A-Z][a-zA-Z]*\s+[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)', text, re.MULTILINE)
        if name_match:
            words = name_match.group(1).split()
            filtered_words = [word for word in words if not re.match(r'boond[A-Za-z]*', word, re.IGNORECASE)]
            name = ' '.join(filtered_words[:3])
        else:
            name = 'Candidate'
    else:
        name = name_match.group(1).strip()
    
    # Extract up to two phone numbers
    phone_pattern = r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\d{10}'
    phone_numbers = re.findall(phone_pattern, text)[:2]
    return name, phone_numbers

def generate_message(name):
    return (
        f"Dear {name},\n\n"
        f"We’re hiring at MEED Public School, a well-reputed institution near New Farakka!\n\n"
        f"🟢 Urgent Vacancies Available:\n"
        f"Teachers – Junior Section (All Subjects)\n"
        f"Teachers – Senior Section (All Subjects)\n"
        f"Office Manager – Male candidates only (Must be skilled in MS Word, Excel, Photoshop, etc.)\n"
        f"Hostel Warden / Helper\n\n"
        f"🏠 Free Fooding & Lodging Provided\n\n"
        f"If interested, kindly send your CV via WhatsApp or Email:\n"
        f"📲 +60 11-1207 9684 (Malaysia – Main Contact)\n"
        f"📲 +91 99233 14480 (School Office)\n"
        f"📧 mymeedpss@gmail.com\n\n"
        f"🌐 Visit: www.mymeedpss.com for more info\n"
        f"📞 Call us immediately at the school number: +91 99233 14480\n\n"
        f"Feel free to contact us anytime.\n"
        f"— Superintendent, MEED Public School"
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == HARDCODED_CREDENTIALS['username'] and 
            password == HARDCODED_CREDENTIALS['password']):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    
    return render_template('login.html', error='')

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    message = ''
    error = ''
    pdf_path = ''
    whatsapp_number = ''
    contact_link = ''
    source = ''

    if request.method == 'POST':
        name = 'Candidate'
        phone_numbers = []
        
        # Handle PDF upload
        if 'resume' in request.files:
            file = request.files['resume']
            source = 'pdf'
            
            if file.filename == '':
                error = 'No file selected'
                return render_template('index.html', error=error, message=message, pdf_path=pdf_path, 
                                    whatsapp_number=whatsapp_number, contact_link=contact_link, source=source)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                try:
                    file.save(filepath)
                    pdf_path = f"/Uploads/{filename}"
                    
                    with open(filepath, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = ''
                        for page in pdf_reader.pages:
                            text += page.extract_text() or ''
                    
                    name, phone_numbers = extract_info(text)
                    message = generate_message(name)
                    
                except Exception as e:
                    error = f"Failed to process PDF: {str(e)}"
        
        # Handle text input
        elif 'details' in request.form:
            source = 'text'
            text = request.form['details']
            name, phone_numbers = extract_info(text)
            message = generate_message(name)
        
        else:
            error = 'No valid input provided'
            return render_template('index.html', error=error, message=message, pdf_path=pdf_path, 
                                 whatsapp_number=whatsapp_number, contact_link=contact_link, source=source)
        
        # Process phone numbers
        whatsapp_number = None
        for number in phone_numbers:
            normalized_number = normalize_phone_number(number)
            if normalized_number:
                whatsapp_number = normalized_number
                break
        
        # Set contact link
        if whatsapp_number:
            contact_link = f"https://wa.me/{whatsapp_number}?text={quote(message)}"
        else:
            error = 'No valid phone number found' if phone_numbers else 'No phone number found'
            contact_link = f"mailto:mymeedpss@gmail.com?subject=Job%20Application%20-%20{name}&body=Please%20attach%20your%20CV"
        
        return render_template('index.html', error=error, message=message, pdf_path=pdf_path, 
                             whatsapp_number=whatsapp_number, contact_link=contact_link, source=source)
    
    return render_template('index.html', error=error, message=message, pdf_path=pdf_path, 
                         whatsapp_number=whatsapp_number, contact_link=contact_link, source=source)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/Uploads/<filename>')
def serve_uploaded_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/cleanup', methods=['GET'])
def cleanup():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    file_path = request.args.get('file')
    if file_path:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(file_path))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Failed to delete file: {str(e)}")
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)