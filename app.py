from flask import Flask, render_template, request, redirect, session, flash, url_for
import mysql.connector
import hashlib, random, base64
from datetime import datetime, date
from flask_mail import Mail, Message
import face_recognition
import numpy as np
from io import BytesIO
from PIL import Image
import cv2
import dlib

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- EMAIL CONFIGURATION ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'voteshieldindia@gmail.com'
app.config['MAIL_PASSWORD'] = 'lqnb uvvd uxtg vxks'
mail = Mail(app)

# ---------------- ADMIN CREDENTIALS ----------------
ADMIN_EMAIL = "admin@voteshield.com"
ADMIN_PASSWORD = hashlib.sha256("admin123".encode()).hexdigest()

# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sahil5084@",
        database="pbldatabase"
    )

# ---------------- HELPER FUNCTIONS ----------------
def generate_code():
    """Generate a 6-digit random verification code"""
    return str(random.randint(100000, 999999))

def send_verification_email(name, email, verification_code):
    """Send verification email"""
    try:
        msg = Message('VoteShield Email Verification',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        
        msg.body = f"""
Dear {name},

Your verification code is: {verification_code}

Please enter this code on the verification page to complete your registration.

This code is valid for a short period.

If you did not register for an account, please ignore this email.

- VoteShield Team
"""
        
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background-color: #2c3e50;
            color: #ffffff;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .content p {{
            margin: 0 0 15px 0;
            color: #333;
        }}
        .code-container {{
            background-color: #f0f0f0;
            border-radius: 6px;
            padding: 25px;
            text-align: center;
            margin: 30px 0;
        }}
        .verification-code {{
            font-size: 42px;
            font-weight: bold;
            color: #16a085;
            letter-spacing: 8px;
            margin: 0;
        }}
        .instructions {{
            color: #555;
            font-size: 14px;
            margin-top: 15px;
        }}
        .note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .note p {{
            margin: 0;
            color: #856404;
            font-size: 14px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 13px;
            border-top: 1px solid #e0e0e0;
        }}
        .footer p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to VoteShield!</h1>
        </div>
        
        <div class="content">
            <p>Thank you for registering, <strong>{name}</strong>. Please use the verification code below to activate your account:</p>
            
            <div class="code-container">
                <p class="verification-code">{verification_code}</p>
                <p class="instructions">Enter this code on the verification page in your browser to complete your registration.</p>
            </div>
            
            <div class="note">
                <p><strong>Note:</strong> This code is valid for a short period.</p>
            </div>
            
            <p>If you did not register for an account, please ignore this email.</p>
        </div>
        
        <div class="footer">
            <p><strong>VoteShield Team</strong></p>
            <p>Secure • Transparent • Democratic</p>
        </div>
    </div>
</body>
</html>
"""
        
        mail.send(msg)
        print(f"✅ Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def process_face_image(base64_image):
    """Process base64 image and extract face encoding"""
    try:
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_array = np.array(image)
        face_locations = face_recognition.face_locations(image_array)
        
        if len(face_locations) == 0:
            return None, "No face detected in the image"
        
        if len(face_locations) > 1:
            return None, "Multiple faces detected. Please ensure only your face is visible"
        
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if len(face_encodings) == 0:
            return None, "Could not encode face. Please try again with better lighting"
        
        encoding_str = ','.join(map(str, face_encodings[0]))
        
        return encoding_str, None
    
    except Exception as e:
        print(f"Error processing face image: {e}")
        return None, f"Error processing image: {str(e)}"

def verify_face_match(stored_encoding_str, captured_image_base64):
    """Verify if captured image matches stored face encoding"""
    try:
        stored_encoding = np.array([float(x) for x in stored_encoding_str.split(',')])
        
        if ',' in captured_image_base64:
            captured_image_base64 = captured_image_base64.split(',')[1]
        
        image_data = base64.b64decode(captured_image_base64)
        image = Image.open(BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_array = np.array(image)
        face_locations = face_recognition.face_locations(image_array)
        
        if len(face_locations) == 0:
            return False, "No face detected in the image"
        
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if len(face_encodings) == 0:
            return False, "Could not encode face"
        
        matches = face_recognition.compare_faces([stored_encoding], face_encodings[0], tolerance=0.6)
        
        if matches[0]:
            return True, "Face verified successfully"
        else:
            return False, "Face does not match. Please try again"
    
    except Exception as e:
        print(f"Error verifying face: {e}")
        return False, f"Verification error: {str(e)}"

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    print(f"📍 Register route accessed - Method: {request.method}")
    
    if request.method == "POST":
        print("📝 Processing registration form...")
        
        name = request.form.get("name")
        email = request.form.get("email")
        voter_id_number = request.form.get("voter_id_number")
        date_of_birth = request.form.get("date_of_birth")
        password_input = request.form.get("password")
        
        print(f"Form data - Name: {name}, Email: {email}, Voter ID: {voter_id_number}, DOB: {date_of_birth}")

        if not all([name, email, voter_id_number, date_of_birth, password_input]):
            print("❌ Missing required fields")
            flash("All fields are required!", "danger")
            return render_template("register.html")

        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 18:
                print(f"❌ User is under 18 (Age: {age})")
                flash("You must be at least 18 years old to register.", "danger")
                return render_template("register.html")
            
            print(f"✅ Age validation passed (Age: {age})")
        except ValueError:
            print("❌ Invalid date format")
            flash("Invalid date of birth format.", "danger")
            return render_template("register.html")

        password = hashlib.sha256(password_input.encode()).hexdigest()
        verification_code = generate_code()
        print(f"Generated verification code: {verification_code}")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            print("✅ Database connected")

            cur.execute("SELECT email FROM voters WHERE email=%s AND email_verified=1", (email,))
            if cur.fetchone():
                print(f"❌ Email {email} already exists and is verified")
                cur.close()
                conn.close()
                flash("Email already registered!", "danger")
                return render_template("register.html")

            cur.execute("SELECT voter_id_number FROM voters WHERE voter_id_number=%s AND email_verified=1", (voter_id_number,))
            if cur.fetchone():
                print(f"❌ Voter ID {voter_id_number} already exists and is verified")
                cur.close()
                conn.close()
                flash("Voter ID already registered!", "danger")
                return render_template("register.html")

            cur.close()
            conn.close()

            session["pending_registration"] = {
                "name": name,
                "email": email,
                "voter_id_number": voter_id_number,
                "date_of_birth": date_of_birth,
                "password": password,
                "verification_code": verification_code
            }
            
            print(f"✅ Registration data stored in session")

            print("📧 Attempting to send verification email...")
            email_sent = send_verification_email(name, email, verification_code)
            
            if email_sent:
                flash("Registration initiated! Please check your email for the verification code.", "success")
            else:
                flash("Failed to send email. Your verification code is displayed in console.", "warning")
                print(f"⚠️ VERIFICATION CODE FOR {email}: {verification_code}")
            
            print(f"🔄 Redirecting to verify page...")
            return redirect(url_for("verify"))

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            flash(f"Registration failed: {str(e)}", "danger")
            return render_template("register.html")

    print("📄 Showing registration form")
    return render_template("register.html")

@app.route('/verify', methods=["GET", "POST"])
def verify():
    print(f"📍 Verify route accessed - Method: {request.method}")
    
    if "pending_registration" not in session:
        print("❌ No pending_registration in session")
        flash("No pending registration found. Please register again.", "danger")
        return redirect(url_for('register'))

    registration_data = session["pending_registration"]
    email = registration_data["email"]
    print(f"✅ Verifying email: {email}")

    if request.method == "POST":
        code = request.form.get("verification_code")
        print(f"🔍 Checking code: {code}")

        if not code:
            flash("Please enter the verification code.", "danger")
            return render_template("verify.html", email=email)

        stored_code = registration_data["verification_code"]
        print(f"Stored code: {stored_code}, Entered code: {code}")
        
        if code == stored_code:
            print("✅ Code matches! Redirecting to image capture...")
            flash("Email verified! Please capture your face image for verification.", "success")
            return redirect(url_for('capture_image'))
        else:
            print("❌ Code does not match")
            flash("Incorrect verification code. Please try again.", "danger")

    return render_template("verify.html", email=email)

@app.route('/capture-image', methods=["GET", "POST"])
def capture_image():
    print(f"📍 Capture image route accessed - Method: {request.method}")
    
    if "pending_registration" not in session:
        print("❌ No pending_registration in session")
        flash("No pending registration found. Please register again.", "danger")
        return redirect(url_for('register'))

    if request.method == "POST":
        image_data = request.form.get("image_data")
        
        if not image_data:
            flash("Please capture your image.", "danger")
            return render_template("capture_image.html")
        
        print("📸 Processing captured image...")
        
        face_encoding, error = process_face_image(image_data)
        
        if error:
            print(f"❌ Face processing error: {error}")
            flash(error, "danger")
            return render_template("capture_image.html")
        
        print("✅ Face encoding successful!")
        
        registration_data = session["pending_registration"]
        registration_data["face_encoding"] = face_encoding
        session["pending_registration"] = registration_data
        session.modified = True
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO voters (name, email, password, voter_id_number, date_of_birth, 
                                    has_voted, email_verified, verification_code, face_encoding)
                VALUES (%s, %s, %s, %s, %s, 0, 1, %s, %s)
            """, (
                registration_data["name"],
                registration_data["email"],
                registration_data["password"],
                registration_data["voter_id_number"],
                registration_data["date_of_birth"],
                registration_data["verification_code"],
                face_encoding
            ))
            conn.commit()
            cur.close()
            conn.close()
            
            print("✅ User successfully registered in database with face encoding and date of birth")
            
            session.pop("pending_registration", None)
            
            flash("Registration complete! Your face has been registered. You can now log in.", "success")
            return redirect(url_for('login'))
            
        except mysql.connector.IntegrityError as e:
            print(f"❌ Database integrity error: {e}")
            flash("Email or Voter ID already registered!", "danger")
            session.pop("pending_registration", None)
            return redirect(url_for('register'))
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            import traceback
            traceback.print_exc()
            flash(f"Failed to complete registration: {str(e)}", "danger")
            return render_template("capture_image.html")
    
    return render_template("capture_image.html")

@app.route('/resend-code', methods=["POST"])
def resend_code():
    print("🔄 Resend code requested")
    
    if "pending_registration" not in session:
        print("❌ No pending_registration in session")
        flash("No pending registration found. Please register again.", "danger")
        return redirect(url_for('register'))

    registration_data = session["pending_registration"]
    email = registration_data["email"]
    name = registration_data["name"]
    
    new_code = generate_code()
    print(f"New verification code for {email}: {new_code}")
    
    registration_data["verification_code"] = new_code
    session["pending_registration"] = registration_data
    session.modified = True
    
    if send_verification_email(name, email, new_code):
        flash("A new verification code has been sent to your email.", "success")
    else:
        flash(f"Failed to send email. Your new code is: {new_code}", "warning")
        print(f"⚠️ NEW VERIFICATION CODE FOR {email}: {new_code}")
    
    return redirect(url_for('verify'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password_input = request.form.get("password")

        if not email or not password_input:
            flash("Email and password are required!", "danger")
            return redirect(url_for('login'))

        password = hashlib.sha256(password_input.encode()).hexdigest()

        # Check if admin credentials
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin"] = True
            session["admin_name"] = "Administrator"
            flash("Welcome Admin!", "success")
            return redirect(url_for('admin_panel'))

        # Regular voter login
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM voters WHERE email=%s AND password=%s AND email_verified=1", (email, password))
            voter = cur.fetchone()
            cur.close()
            conn.close()

            if voter:
                if voter[9] and voter[9].strip():
                    session["temp_voter_id"] = voter[0]
                    session["temp_voter_name"] = voter[1]
                    session["temp_voter_face_encoding"] = voter[9]
                    
                    flash("Credentials verified! Please verify your face to complete login.", "success")
                    return redirect(url_for('verify_face'))
                else:
                    session["voter_id"] = voter[0]
                    session["voter_name"] = voter[1]
                    flash(f"Welcome back, {voter[1]}!", "success")
                    return redirect(url_for('vote'))
            else:
                flash("Invalid credentials or unverified email.", "danger")
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            flash(f"Login error: {str(e)}", "danger")

    return render_template("login.html")

@app.route('/verify-face', methods=["GET", "POST"])
def verify_face():
    print(f"📍 Face verification route accessed - Method: {request.method}")
    
    if "temp_voter_id" not in session:
        print("❌ No temp voter session found")
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    
    if request.method == "POST":
        image_data = request.form.get("image_data")
        
        if not image_data:
            flash("Please capture your image.", "danger")
            return render_template("verify_face.html")
        
        print("📸 Verifying captured face...")
        
        stored_encoding = session.get("temp_voter_face_encoding")
        
        if not stored_encoding:
            flash("No face data found. Please contact support.", "danger")
            return redirect(url_for('login'))
        
        match, message = verify_face_match(stored_encoding, image_data)
        
        if match:
            print("✅ Face verification successful!")
            
            session["voter_id"] = session.pop("temp_voter_id")
            session["voter_name"] = session.pop("temp_voter_name")
            session.pop("temp_voter_face_encoding", None)
            
            flash(f"Welcome back, {session['voter_name']}! Face verified successfully.", "success")
            return redirect(url_for('vote'))
        else:
            print(f"❌ Face verification failed: {message}")
            flash(message, "danger")
            return render_template("verify_face.html")
    
    return render_template("verify_face.html")

# ----------- ADMIN PANEL -----------
@app.route('/admin')
def admin_panel():
    if "admin" not in session:
        flash("Unauthorized access. Admin login required.", "danger")
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch all candidates with vote count
        cur.execute("SELECT candidate_id, name, party, party_symbol, votes FROM candidates ORDER BY candidate_id")
        candidates = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("admin.html", candidates=candidates)
    except Exception as e:
        print(f"Admin panel error: {e}")
        flash(f"Error loading admin panel: {str(e)}", "danger")
        return redirect(url_for('login'))

@app.route('/admin/add-candidate', methods=["POST"])
def add_candidate():
    if "admin" not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))
    
    candidate_name = request.form.get("name")
    party_name = request.form.get("party")
    party_symbol = request.form.get("party_symbol")
    
    print(f"📝 Add Candidate Request:")
    print(f"   Name: {candidate_name}")
    print(f"   Party: {party_name}")
    print(f"   Symbol: {party_symbol}")
    
    if not candidate_name or not party_name:
        print("❌ Missing required fields")
        flash("Candidate name and party are required!", "danger")
        return redirect(url_for('admin_panel'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"✅ Inserting into database...")
        cur.execute("""
            INSERT INTO candidates (name, party, party_symbol, votes)
            VALUES (%s, %s, %s, 0)
        """, (candidate_name, party_name, party_symbol if party_symbol else None))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Candidate '{candidate_name}' added successfully!")
        flash(f"Candidate '{candidate_name}' added successfully!", "success")
    except Exception as e:
        print(f"❌ Error adding candidate: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error adding candidate: {str(e)}", "danger")
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-candidate/<int:candidate_id>', methods=["POST"])
def delete_candidate(candidate_id):
    if "admin" not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM candidates WHERE candidate_id=%s", (candidate_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Candidate deleted successfully!", "success")
    except Exception as e:
        print(f"Error deleting candidate: {e}")
        flash(f"Error deleting candidate: {str(e)}", "danger")
    
    return redirect(url_for('admin_panel'))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/terms')
def terms():
    return render_template("terms.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        print(f"New message from {name} ({email}): {message}")
        flash("Message sent successfully!", "success")
    return render_template('contact.html')

@app.route('/vote')
def vote():
    if "voter_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user has already voted
        cur.execute("SELECT * FROM votes WHERE voter_id=%s", (session["voter_id"],))
        existing_vote = cur.fetchone()
        
        if existing_vote:
            cur.close()
            conn.close()
            flash("You have already cast your vote! Thank you for participating.", "info")
            return render_template("already_voted.html", voter_name=session.get("voter_name"))
        
        # Fetch candidates from database
        cur.execute("SELECT candidate_id, name, party, party_symbol FROM candidates ORDER BY candidate_id")
        candidates = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("vote.html", voter_name=session.get("voter_name"), candidates=candidates)
    except Exception as e:
        print(f"Error loading vote page: {e}")
        flash(f"Error loading candidates: {str(e)}", "danger")
        return redirect(url_for('login'))

@app.route('/submit-vote', methods=['POST'])
def submit_vote():
    if "voter_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    
    voter_id = session["voter_id"]
    candidate_id = request.form.get("candidate")
    
    if not candidate_id:
        flash("Please select a candidate.", "danger")
        return redirect(url_for("vote"))
    
    try:
        candidate_id = int(candidate_id)
    except ValueError:
        flash("Invalid candidate selection.", "danger")
        return redirect(url_for("vote"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Double-check if user has already voted
        cur.execute("SELECT * FROM votes WHERE voter_id=%s", (voter_id,))
        if cur.fetchone():
            flash("You have already cast your vote!", "warning")
            cur.close()
            conn.close()
            return redirect(url_for("vote"))
        
        # Get candidate name BEFORE inserting the vote
        cur.execute("SELECT name FROM candidates WHERE candidate_id = %s", (candidate_id,))
        candidate_result = cur.fetchone()
        candidate_name = candidate_result[0] if candidate_result else "your chosen candidate"
        
        # Insert the vote
        cur.execute("""
            INSERT INTO votes (voter_id, candidate_id, timestamp)
            VALUES (%s, %s, %s)
        """, (voter_id, candidate_id, datetime.now()))
        
        # Update candidate vote count
        cur.execute("""
            UPDATE candidates 
            SET votes = votes + 1 
            WHERE candidate_id = %s
        """, (candidate_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Your vote has been cast successfully! Thank you for participating in democracy.", "success")
        return render_template("vote_success.html", 
                             voter_name=session.get("voter_name"),
                             candidate_name=candidate_name)
        
    except Exception as e:
        print(f"Vote submission error: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error submitting vote: {str(e)}", "danger")
        return redirect(url_for("vote"))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    print("🚀 Starting Flask application...")
    print("📋 Make sure your database has these tables:")
    print("   - voters (voter_id, name, email, password, voter_id_number, date_of_birth, has_voted, email_verified, verification_code, face_encoding)")
    print("   - votes (id, voter_id, candidate_id, timestamp)")
    print("   - candidates (candidate_id, name, party, party_symbol, votes)")
    print("📦 Required: pip install face-recognition pillow numpy")
    print("\n🔐 ADMIN CREDENTIALS:")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: admin123")
    app.run(debug=True, port=5000)