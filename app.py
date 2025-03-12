from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
import random, string
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure MySQL connection using environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure email settings using environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
mail = Mail(app)

# Define MySQL table structure
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    complaint = db.Column(db.Text, nullable=False)
    ticket_number = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(10), default="pending")  # 'pending' or 'ok'

# Initialize MySQL tables
with app.app_context():
    db.create_all()

# Function to generate ticket numbers
def generate_ticket():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Endpoint to submit a complaint
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    data = request.json
    ticket = generate_ticket()
    new_complaint = Complaint(email=data['email'], complaint=data['complaint'], ticket_number=ticket)
    db.session.add(new_complaint)
    db.session.commit()

    # Send confirmation email
    msg = Message("Complaint Received", sender=app.config['MAIL_USERNAME'], recipients=[data['email']])
    msg.body = f"Your complaint has been received.\nTicket Number: {ticket}"
    mail.send(msg)

    return jsonify({"message": "Complaint submitted", "ticket_number": ticket})

# Endpoint to mark a complaint as resolved
@app.route('/resolve_complaint/<ticket>', methods=['PUT'])
def resolve_complaint(ticket):
    complaint = Complaint.query.filter_by(ticket_number=ticket).first()
    if not complaint:
        return jsonify({"message": "Complaint not found"}), 404

    complaint.status = "ok"
    db.session.commit()

    # Send resolution email
    msg = Message("Complaint Resolved", sender=app.config['MAIL_USERNAME'], recipients=[complaint.email])
    msg.body = f"Your complaint with Ticket Number {ticket} has been resolved."
    mail.send(msg)

    return jsonify({"message": "Complaint resolved"})

# Endpoint to check complaint status
@app.route('/check_status/<ticket>', methods=['GET'])
def check_status(ticket):
    complaint = Complaint.query.filter_by(ticket_number=ticket).first()
    if not complaint:
        return jsonify({"message": "Ticket not found"}), 404

    return jsonify({"message": f"Status: {complaint.status}"})

if __name__ == '__main__':
    app.run(debug=True)
