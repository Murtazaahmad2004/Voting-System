import random
from flask import Flask, Response, render_template, request, redirect, session, url_for, flash
from flask_cors import CORS
import mysql.connector
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import os
from email.message import EmailMessage
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

app.secret_key = '123789456'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'NHA@2004',
    'database': 'voting_system'
}

# HOME 
@app.route('/')
def home():
    return render_template('login.html')

# Start LOGIN 
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        idcard = request.form['idcard']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            # ✅ Check user in database
            cursor.execute("""
                SELECT * FROM signup 
                WHERE id_card = %s AND password = %s
            """, (idcard, password))
            user = cursor.fetchone()

            if user:
                # ✅ Log successful login
                cursor2 = conn.cursor()
                cursor2.execute(
                    "INSERT INTO login (id_card, password) VALUES (%s, %s)",
                    (idcard, password)
                )
                conn.commit()
                cursor2.close()

                # ✅ Redirect based on role
                if user.get("role") == "candidate":
                    return redirect(url_for('candidate_candidate_home_page'))
                elif user.get("role") == "voter":
                    return redirect(url_for('voter_voter_home_page'))
                elif user.get("role") == "admin":
                    return redirect(url_for('admin_page'))
                else:
                    error = "❌ Unknown role for this user!"

            else:
                error = "❌ Invalid idcard or password!"

            cursor.close()
            conn.close()

        except Exception as e:
            error = f"❌ Database error: {e}"

    return render_template('login.html', error=error)
# End LOGIN

# Start SIGNUP 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['firstname']
        gender = request.form['gender']
        idcard = request.form['idcard']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash("❌ Passwords do not match!", "error")
            return redirect(url_for('signup'))

        # ✅ Role safety check (admin cannot be chosen by normal signup)
        if role not in ['voter', 'candidate']:
            role = 'voter'  # fallback default role

        # generate OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['user_data'] = {
            'username': username,
            'gender': gender,
            'idcard': idcard,
            'email': email,
            'password': password,
            'confirm_password': confirm_password,
            'role': role
        }

        # send OTP via email
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Your OTP Verification Code'
            msg['From'] = "shmurtazaahmad334@gmail.com"
            msg['To'] = email
            msg.set_content(f"Your OTP code is: {otp}")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("shmurtazaahmad334@gmail.com", "lhmv zrnz ecqk ajke")  # apna Gmail App password
                smtp.send_message(msg)

            flash("📧 OTP sent to your email!", "info")
        except Exception as e:
            flash(f"❌ Error sending OTP: {e}", "error")

        return redirect(url_for('verify_otp'))

    return render_template('signup.html')

# verify otp signup
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            data = session.get('user_data')

            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()

                # ✅ Role again checked here for safety
                safe_role = data['role'] if data['role'] in ['voter', 'candidate'] else 'voter'

                cursor.execute("""
                    INSERT INTO signup (user_name, gender, id_card, email, password, confirm_password, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (data['username'], data['gender'], data['idcard'], data['email'],
                      data['password'], data['confirm_password'], safe_role))
                conn.commit()
                cursor.close()
                conn.close()

                session.pop('otp', None)
                session.pop('user_data', None)

                flash("✅ User registered successfully!", "success")
                return redirect(url_for('home'))
            except Exception as e:
                flash(f"❌ Database error: {e}", "error")
        else:
            flash("❌ Invalid OTP!", "error")

    return render_template('verify_otp.html')
# End Signup

# Start Admin DashBoard
# admin candidate page
@app.route('/admin/candidate_page', methods=['GET', 'POST'])
def admin_candidate_page():
    if request.method == 'POST':
        username = request.form['firstname']
        gender = request.form['gender']
        idcard = request.form['idcard']
        email = request.form['email']
        party_name = request.form['party_name'] 
        profile_pic = request.files.get('profile_pic')
        party_logo = request.files.get('party_logo')

        # save uploaded images
        profile_pic_filename = None
        party_logo_filename = None

        if profile_pic and allowed_file(profile_pic.filename):
            profile_pic_filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename))

        if party_logo and allowed_file(party_logo.filename):
            party_logo_filename = secure_filename(party_logo.filename)
            party_logo.save(os.path.join(app.config['UPLOAD_FOLDER'], party_logo_filename))

        # generate OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['user_data'] = {
            'username': username,
            'gender': gender,
            'idcard': idcard,
            'email': email,
            'party_name': party_name,
            'party_logo': party_logo_filename,
            'profile_pic': profile_pic_filename
        }

        # send OTP via email
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Your OTP Verification Code'
            msg['From'] = "shmurtazaahmad334@gmail.com"
            msg['To'] = email
            msg.set_content(f"Your OTP code is: {otp}")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("shmurtazaahmad334@gmail.com", "lhmv zrnz ecqk ajke")  # Gmail App Password
                smtp.send_message(msg)

            flash("📧 OTP sent to your email!", "info")
        except Exception as e:
            flash(f"❌ Error sending OTP: {e}", "error")

        return redirect(url_for('verify_candidate_otp'))

    return render_template('admin/candidate_page.html')

# admin verify otp candidate
@app.route('/admin/verify_candidate_otp', methods=['GET', 'POST'])
def verify_candidate_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if entered_otp == session.get('otp'):
            data = session.get('user_data')
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO candidate (candidate_name, gender, id_card, email, profile_pic, party_logo, party_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    data['username'],
                    data['gender'],
                    data['idcard'],
                    data['email'],
                    data['profile_pic'],
                    data['party_logo'],
                    data['party_name']
                ))
                conn.commit()
                cursor.close()
                conn.close()

                session.pop('otp', None)
                session.pop('user_data', None)

                flash("✅ Candidate registered successfully!", "success")
                return redirect(url_for('admin_candidate_page'))
            except Exception as e:
                flash(f"❌ Database error: {e}", "error")
        else:
            flash("❌ Invalid OTP!", "error")

    return render_template('/admin/verify_candidate_otp.html')

# admin candidate list page
@app.route('/admin/candidate_list_page')
def admin_candidate_list_page():
    cnic = request.args.get('id_card')
    records = []

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        if cnic:  # agar filter apply ho
            cursor.execute("SELECT * FROM candidate WHERE id_card = %s ORDER BY id DESC", (cnic,))
        else:  # warna sab records show karo
            cursor.execute("SELECT * FROM candidate ORDER BY id DESC")

        records = cursor.fetchall()

    except Exception as e:
        print("Error:", e)

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return render_template('/admin/candidate_list_page.html', records=records, cnic=cnic)

# Route for export candidate list CSV
@app.route('/export_candidate_csv')
def export_candidate_csv():    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM candidate ORDER BY id DESC")
        records = cursor.fetchall()

    except Exception as e:
        print("Error:", e)
        records = []

    finally:
        cursor.close()
        conn.close()
       
    si = [] 
    header = ["ID", "Candidate Name", "Gender", "ID Card", "Email", "Party Name", "Party Logo", "Profile Pic"]

    si.append(header)
    for r in records:
        si.append([
            r['id'],
            r['candidate_name'],
            r['gender'],
            f'="{r["id_card"]}"',
            r['email'],
            r['party_name'],
            r['party_logo'],
            r['profile_pic']
        ])

    # Convert to CSV string
    output = ""
    for row in si:
        output += ",".join(map(str, row)) + "\n"

    return Response(
        output,
        mimetype="text/csv",    
        headers={"Content-Disposition": "attachment; filename=candidate_data.csv"}
    )

# Route to delete a voter record
@app.route('/delete/<string:cnic>', methods=['GET'])
def candidate_record(cnic):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidate WHERE id_card = %s", (cnic,))
        conn.commit()
        flash("✅ Record deleted successfully.", 'success')
    except Exception as e:
        flash("❌ Error deleting record.", 'danger')
        print("Delete error:", e)
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_candidate_list_page'))

# admin voter list page
@app.route('/admin/voter_list_page', methods=['GET'])
def admin_voter_list_page():
    cnic = request.args.get('id_card')
    records = []

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        if cnic:  # agar filter apply ho
            cursor.execute("SELECT * FROM signup WHERE id_card = %s ORDER BY id DESC", (cnic,))
        else:  # warna sab records show karo
            cursor.execute("SELECT * FROM signup ORDER BY id DESC")

        records = cursor.fetchall()

    except Exception as e:
        print("Error:", e)

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return render_template('/admin/voter_list_page.html', records=records, cnic=cnic)

# Route for export voter list CSV
@app.route('/export_voter_csv')
def export_voter_csv():    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM signup ORDER BY id DESC")
        records = cursor.fetchall()

    except Exception as e:
        print("Error:", e)
        records = []

    finally:
        cursor.close()
        conn.close()

    si = [] 
    header = ["ID", "User Name", "Gender", "ID Card", "Email", "Password", "Confirm Password", "Role"]

    si.append(header)
    for r in records:
        si.append([
            r['id'],
            r['user_name'],
            r['gender'],
            f'="{r["id_card"]}"',
            r['email'],
            r['password'],
            r['confirm_password'],
            r['role']
        ])

    # Convert to CSV string
    output = ""
    for row in si:
        output += ",".join(map(str, row)) + "\n"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=voter_data.csv"}
    )

# Route to delete a voter record
@app.route('/delete/<string:cnic>', methods=['GET'])
def voter_record(cnic):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signup WHERE id_card = %s", (cnic,))
        conn.commit()
        flash("✅ Record deleted successfully.", 'success')
    except Exception as e:
        flash("❌ Error deleting record.", 'danger')
        print("Delete error:", e)
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_voter_list_page'))

# admin_see_results
@app.route('/admin/see_results')
def admin_see_result():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # count total votes per candidate
    query = """
        SELECT party_name, candidate_name, COUNT(*) as total_votes
        FROM votes_full
        GROUP BY party_name, candidate_name
        ORDER BY total_votes DESC;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('/admin/see_results.html', results=results)
# End Admin DashBoard

# Start Candidate DashBoard
# Upload config
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# helper function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Candidate Registration
@app.route('/candidate/candidate_page', methods=['GET', 'POST'])
def candidate_candidate_page():
    if request.method == 'POST':
        username = request.form['firstname']
        gender = request.form['gender']
        idcard = request.form['idcard']
        email = request.form['email']
        party_name = request.form['party_name'] 
        profile_pic = request.files.get('profile_pic')
        party_logo = request.files.get('party_logo')

        # save uploaded images
        profile_pic_filename = None
        party_logo_filename = None

        if profile_pic and allowed_file(profile_pic.filename):
            profile_pic_filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename))

        if party_logo and allowed_file(party_logo.filename):
            party_logo_filename = secure_filename(party_logo.filename)
            party_logo.save(os.path.join(app.config['UPLOAD_FOLDER'], party_logo_filename))

        # generate OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['user_data'] = {
            'username': username,
            'gender': gender,
            'idcard': idcard,
            'email': email,
            'party_name': party_name,
            'party_logo': party_logo_filename,
            'profile_pic': profile_pic_filename
        }

        # send OTP via email
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Your OTP Verification Code'
            msg['From'] = "shmurtazaahmad334@gmail.com"
            msg['To'] = email
            msg.set_content(f"Your OTP code is: {otp}")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("shmurtazaahmad334@gmail.com", "lhmv zrnz ecqk ajke")  # Gmail App Password
                smtp.send_message(msg)

            flash("📧 OTP sent to your email!", "info")
        except Exception as e:
            flash(f"❌ Error sending OTP: {e}", "error")

        return redirect(url_for('candidate_verify_candidate_otp'))

    return render_template('candidate/candidate_page.html')

# ✅ Candidate OTP Verification
@app.route('/candidate/verify_candidate_otp', methods=['GET', 'POST'])
def candidate_verify_candidate_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if entered_otp == session.get('otp'):
            data = session.get('user_data')
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO candidate (candidate_name, gender, id_card, email, profile_pic, party_logo, party_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    data['username'],
                    data['gender'],
                    data['idcard'],
                    data['email'],
                    data['profile_pic'],
                    data['party_logo'],
                    data['party_name']
                ))
                conn.commit()
                cursor.close()
                conn.close()

                session.pop('otp', None)
                session.pop('user_data', None)

                flash("✅ Candidate registered successfully!", "success")
                return redirect(url_for('candidate_candidate_page'))
            except Exception as e:
                flash(f"❌ Database error: {e}", "error")
        else:
            flash("❌ Invalid OTP!", "error")

    return render_template('candidate/verify_candidate_otp.html')

# candidate list
@app.route('/candidate/candidate_list', methods=['GET'])
def candidate_voter_list_page():
    cnic = request.args.get('id_card')
    records = []

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        if cnic:  # agar filter apply ho
            cursor.execute("SELECT * FROM candidate WHERE id_card = %s ORDER BY id DESC", (cnic,))
        else:  # warna sab records show karo
            cursor.execute("SELECT * FROM candidate ORDER BY id DESC")

        records = cursor.fetchall()

    except Exception as e:
        print("Error:", e)

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return render_template('/candidate/candidate_list.html', records=records, cnic=cnic)

# candidate result screen
@app.route('/candidate/see_results')
def candidate_see_result():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # count total votes per candidate
    query = """
        SELECT party_name, candidate_name, COUNT(*) as total_votes
        FROM votes_full
        GROUP BY party_name, candidate_name
        ORDER BY total_votes DESC;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('/candidate/see_results.html', results=results)
# End Candidate DashBoard

# Start Voter DashBoard
# VOTING REGISTRATION 
@app.route('/voter/voteing_registration', methods=['GET', 'POST'])
def voter_voteing_registration():
    if request.method == 'POST':
        idcard = request.form['idcard']
        email = request.form['email']

        # generate OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['user_data'] = {
            'idcard': idcard,
            'email': email
        }

        try:
            msg = EmailMessage()
            msg['Subject'] = 'Voting OTP Verification'
            msg['From'] = "shmurtazaahmad334@gmail.com"
            msg['To'] = email
            msg.set_content(f"Your voting OTP is: {otp}")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("shmurtazaahmad334@gmail.com", "lhmv zrnz ecqk ajke")
                smtp.send_message(msg)

            flash("📧 OTP sent to your email. Please verify.", "info")
            return redirect(url_for('voting_verify_voting_otp'))
        except Exception as e:
            flash(f"❌ Error sending OTP: {e}", "error")

    # 🟢 deadline inject kar do frontend me
    return render_template('/voter/voteing_registration.html')

# verify otp voting registration
@app.route('/voter/verify_voting_otp', methods=['GET', 'POST'])
def voting_verify_voting_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            data = session.get('user_data')
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO voting_registration (id_card, email)
                    VALUES (%s, %s)
                """, (data['idcard'], data['email']))
                conn.commit()
                cursor.close()
                conn.close()

                session.pop('otp', None)
                session.pop('user_data', None)

                return redirect(url_for('voter_voting_page'))
            except Exception as e:
                flash(f"❌ Database error: {e}", "error")
        else:
            flash("❌ Invalid OTP!", "error")

    return render_template('/voter/verify_voting_otp.html')

# voting page
@app.route('/voter/voting_page', methods=['GET', 'POST'])
def voter_voting_page():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Candidate data fetch
        cursor.execute("""
            SELECT candidate_name, gender, id_card, email, party_name, party_logo, profile_pic 
            FROM candidate
        """)
        candidates = cursor.fetchall()

        if request.method == 'POST':
            selected_id = request.form.get('selected_candidate')
            if not selected_id:
                flash("❌ Please select a candidate!")
                return redirect(url_for('voter_voting_page'))

            # Candidate find by id_card
            selected = next((c for c in candidates if c['id_card'] == selected_id), None)

            if not selected:
                flash("❌ Invalid candidate selected!")
                return redirect(url_for('voter_voting_page'))

            # ✅ Correct insert (5 columns → 5 values)
            cursor2 = conn.cursor()
            cursor2.execute("""
                INSERT INTO votes_full 
                (candidate_name, gender, id_card, email, party_name, party_logo, profile_pic, vote_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                selected['candidate_name'],
                selected['gender'],
                selected['id_card'],
                selected['email'],
                selected['party_name'],
                selected['party_logo'],
                selected['profile_pic']
            ))
            conn.commit()
            cursor2.close()

            flash("✅ Your vote has been recorded successfully!")
            return redirect(url_for('voter_voting_page'))

        cursor.close()
        conn.close()

    except Exception as e:
        flash(f"❌ Database error: {e}")
        return redirect(url_for('voter_voting_page'))

    return render_template('/voter/voting_page.html', candidates=candidates)

# Result screen
@app.route('/voter/see_results')
def voter_results():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # count total votes per candidate
    query = """
        SELECT party_name, candidate_name, COUNT(*) as total_votes
        FROM votes_full
        GROUP BY party_name, candidate_name
        ORDER BY total_votes DESC;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('/voter/see_results.html', results=results)
# End Voter DashBoard

# admin page
@app.route('/admin/admin_page', methods=['GET', 'POST'])
def admin_page():
    return render_template('/admin/admin_page.html')

# admin page
@app.route('/candidate/candidate_home_page', methods=['GET', 'POST'])
def candidate_candidate_home_page():
    return render_template('/candidate/candidate_home_page.html')

# Voter home page
@app.route('/voter/voter_home_page')
def voter_voter_home_page():
    return render_template('/voter/voter_home_page.html')

# Flask App Run
if __name__ == '__main__':
    app.run(host="192.168.100.10", port=5000, debug=True)
    # app.run(debug=True)