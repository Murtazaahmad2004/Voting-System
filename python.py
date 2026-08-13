import random
import os
from datetime import datetime
from flask import Flask, Response, jsonify, render_template, request, redirect, session, url_for, flash
from flask_cors import CORS
import mysql.connector
import smtplib
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

def get_db_connection():
    conn = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    return conn

# Upload config (single place)
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(to_email: str, subject: str, body: str):
    """Simple helper to send an email using Gmail SMTP (App password required)."""
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = "parkflow101@gmail.com"
        msg['To'] = to_email
        msg.set_content(body)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("parkflow101@gmail.com", "majq teeu gcyr kpgn")  # Gmail App Password
            smtp.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)

def save_uploaded_file(file_storage):
    """Save uploaded file to configured upload folder and return filename or None."""
    if file_storage and allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_storage.save(dest)
        return filename
    return None

def insert_candidate_to_db(data):
    """Insert candidate dict into candidate table. Expects keys:
       username, gender, idcard, email, party_name, profile_pic, party_logo
    """
    conn = None
    cursor = None
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
            data.get('profile_pic'),
            data.get('party_logo'),
            data.get('party_name')
        ))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# HOME 
@app.route('/')
def home():
    return render_template('login.html')

# Support
@app.route('/support')
def support():
    return render_template('support.html')

# Privacy
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Terms
@app.route('/terms')
def terms():
    return render_template('terms.html')

# LOGIN 
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        idcard = request.form['idcard']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT * FROM signup 
                WHERE id_card = %s AND password = %s
            """, (idcard, password))
            user = cursor.fetchone()

            if user:
                cursor2 = conn.cursor()
                cursor2.execute(
                    "INSERT INTO login (id_card, password) VALUES (%s, %s)",
                    (idcard, password)
                )
                conn.commit()
                cursor2.close()

                role = user.get("role")
                if role == "candidate":
                    return redirect(url_for('candidate_candidate_home_page'))
                elif role == "voter":
                    return redirect(url_for('voter_voter_home_page'))
                elif role == "admin":
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

# SIGNUP 
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

        if role not in ['voter', 'candidate']:
            role = 'voter'

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

        ok, err = send_email(email, 'Your OTP Verification Code', f"Your OTP code is: {otp}")
        if ok:
            flash("📧 OTP sent to your email!", "info")
        else:
            flash(f"❌ Error sending OTP: {err}", "error")

        return redirect(url_for('verify_otp'))

    return render_template('signup.html')

# signup verify otp
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            data = session.get('user_data')
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()

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

# ADMIN candidate list
@app.route('/admin/candidate_list_page')
def admin_candidate_list_page():
    cnic = request.args.get('id_card')
    records = []
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        if cnic:
            cursor.execute("SELECT * FROM candidate WHERE id_card = %s ORDER BY id DESC", (cnic,))
        else:
            cursor.execute("SELECT * FROM candidate ORDER BY id DESC")
        records = cursor.fetchall()
    except Exception as e:
        print("Error:", e)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return render_template('admin/candidate_list_page.html', records=records, cnic=cnic)

# ADMIN: delete candidate (route name changed to avoid conflict)
@app.route('/admin/delete_candidate/<string:cnic>', methods=['GET'])
def delete_candidate_record(cnic):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidate WHERE id_card = %s", (cnic,))
        conn.commit()
        flash("✅ Candidate record deleted successfully.", 'success')
    except Exception as e:
        flash("❌ Error deleting record.", 'danger')
        print("Delete error:", e)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return redirect(url_for('admin_candidate_list_page'))

# ADMIN voter list page
@app.route('/admin/voter_list_page', methods=['GET'])
def admin_voter_list_page():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        id_card = request.args.get('id_card')
        if id_card:
            cursor.execute("SELECT * FROM signup WHERE id_card = %s", (id_card,))
        else:
            cursor.execute("SELECT * FROM signup")
        records = cursor.fetchall()
    except Exception as e:
        flash("❌ Error fetching records.", "danger")
        print("Fetch error:", e)
        records = []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return render_template('admin/voter_list_page.html', records=records)

# ADMIN: delete voter (route name changed to avoid conflict)
@app.route('/admin/delete_voter/<string:cnic>', methods=['GET'])
def delete_voter_record(cnic):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signup WHERE id_card = %s", (cnic,))
        conn.commit()
        flash("✅ Voter record deleted successfully.", 'success')
    except Exception as e:
        flash("❌ Error deleting record.", 'danger')
        print("Delete error:", e)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return redirect(url_for('admin_voter_list_page'))

# ADMIN see results (shared query)
@app.route('/admin/see_results')
def admin_see_result():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
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
    return render_template('admin/see_results.html', results=results)

# Create new election
@app.route('/admin/create_election', methods=['GET', 'POST'])
def create_election():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        rules = request.form['rules']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO elections (title, description, start_date, end_date, rules, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, start_date, end_date, rules, False))
            conn.commit()
            cursor.close()
            conn.close()
            flash("✅ Election created successfully!", "success")
        except Exception as e:
            flash(f"❌ Error creating election: {e}", "danger")

        return redirect(url_for('list_elections'))

    return render_template('admin/create_election.html')

# admin election list
@app.route('/admin/elections')
def list_elections():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM elections")
        elections = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        elections = []
        flash(f"❌ Database error: {e}", "danger")

    return render_template('admin/elections.html', elections=elections)

# admin toggle election 
@app.route('/admin/toggle_election/<int:election_id>')
def toggle_election(election_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT is_active FROM elections WHERE id = %s", (election_id,))
        election = cursor.fetchone()
        new_status = not election['is_active']
        cursor.execute("UPDATE elections SET is_active = %s WHERE id = %s", (new_status, election_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Election status updated!", "success")
    except Exception as e:
        flash(f"❌ Error updating status: {e}", "danger")

    return redirect(url_for('list_elections'))

# Notifications System
def add_notification(message, user_role="admin"):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (message, user_role, is_read)
            VALUES (%s, %s, %s)
        """, (message, user_role, False))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Notification error:", e)

# List all notifications for admin
@app.route('/admin/notification_alert')
def admin_notification_alert():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE user_role = 'admin'
            ORDER BY created_at DESC
        """)
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        notifications = []
        flash(f"❌ Database error: {e}", "danger")

    return render_template('admin/notification_alert.html', notifications=notifications)

# Mark notification as read
@app.route('/admin/mark_read/<int:notif_id>')
def mark_read(notif_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notif_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Notification marked as read.", "success")
    except Exception as e:
        flash(f"❌ Error updating notification: {e}", "danger")

    return redirect(url_for('admin_notification_alert'))

# Candidate routes (voter-facing candidate registration)
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

        profile_pic_filename = save_uploaded_file(profile_pic)
        party_logo_filename = save_uploaded_file(party_logo)

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

        ok, err = send_email(email, 'Your OTP Verification Code', f"Your OTP code is: {otp}")
        if ok:
            flash("📧 OTP sent to your email!", "info")
        else:
            flash(f"❌ Error sending OTP: {err}", "error")

        return redirect(url_for('candidate_verify_candidate_otp'))

    return render_template('candidate/candidate_page.html')

# candidate verify candidate otp
@app.route('/candidate/verify_candidate_otp', methods=['GET', 'POST'])
def candidate_verify_candidate_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            data = session.get('user_data')
            ok, err = insert_candidate_to_db(data)
            if ok:
                session.pop('otp', None)
                session.pop('user_data', None)
                flash("✅ Candidate registered successfully!", "success")
                return redirect(url_for('candidate_candidate_page'))
            else:
                flash(f"❌ Database error: {err}", "error")
        else:
            flash("❌ Invalid OTP!", "error")

    return render_template('candidate/verify_candidate_otp.html')

# candidate candidate list
@app.route('/candidate/candidate_list', methods=['GET'])
def candidate_voter_list_page():
    cnic = request.args.get('id_card')
    records = []
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        if cnic:
            cursor.execute("SELECT * FROM candidate WHERE id_card = %s ORDER BY id DESC", (cnic,))
        else:
            cursor.execute("SELECT * FROM candidate ORDER BY id DESC")
        records = cursor.fetchall()
    except Exception as e:
        print("Error:", e)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return render_template('candidate/candidate_list.html', records=records, cnic=cnic)

# candidate see result
@app.route('/candidate/see_results')
def candidate_see_result():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Latest active election
        cursor.execute("SELECT * FROM elections WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")
        election = cursor.fetchone()

        if not election:
            return render_template(
                'candidate/see_results.html',
                results=None,
                election=None,
            )

        # Current time
        now = datetime.now()

        # Check if election not started
        if now < election['start_date']:
            return render_template(
                'candidate/see_results.html',
                results=None,
                election=election,
                message="⏳ Results will be available after voting starts."
            )

        # Check if election still running
        if now < election['end_date']:
            return render_template(
                'candidate/see_results.html',
                results=None,
                election=election,
                message="🗳️ Results will be available after voting ends."
            )

        # ✅ Election ended → show results
        query = """
            SELECT party_name, candidate_name, COUNT(*) as total_votes
            FROM votes_full
            GROUP BY party_name, candidate_name
            ORDER BY total_votes DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()

        return render_template(
            'candidate/see_results.html',
            results=results,
            election=election,
            message=None
        )

    except Exception as e:
        print("Error fetching results:", e)
        return render_template(
            'candidate/see_results.html',
            results=None,
            election=None,
            message="❌ Error loading results."
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Voter registration & voting
@app.route('/voter/voteing_registration', methods=['GET', 'POST'])
def voter_voteing_registration():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM elections 
            WHERE is_active = TRUE 
            ORDER BY start_date DESC 
            LIMIT 1
        """)
        election = cursor.fetchone()

        election_active = False
        election_start = None
        election_end = None

        if election:
            election_start = election['start_date']
            election_end = election['end_date']
            now = datetime.now()
            if election_start <= now <= election_end:
                election_active = True

        if request.method == 'POST':
            if not election_active:
                flash("❌ Registration is closed because election is not active.", "danger")
                return redirect(url_for('voter_voteing_registration'))

            idcard = request.form['idcard']
            email = request.form['email']

            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['user_data'] = {'idcard': idcard, 'email': email}

            ok, err = send_email(email, 'Voting OTP Verification', f"Your voting OTP is: {otp}")
            if ok:
                flash("📧 OTP sent to your email. Please verify.", "info")
                return redirect(url_for('voting_verify_voting_otp'))
            else:
                flash(f"❌ Error sending OTP: {err}", "danger")

        cursor.close()
        conn.close()

    except Exception as e:
        flash(f"❌ Database error: {e}", "danger")

    return render_template(
        'voter/voteing_registration.html',
        election_active=election_active,
        election_start=election_start,
        election_end=election_end
    )

# voter verify otp
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

    return render_template('voter/verify_voting_otp.html')

# voter voting page
@app.route('/voter/voting_page', methods=['GET', 'POST'])
def voter_voting_page():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM elections 
            WHERE is_active = TRUE 
            ORDER BY start_date DESC 
            LIMIT 1
        """)
        election = cursor.fetchone()

        election_active = False
        election_start = None
        election_end = None

        if election:
            election_start = election['start_date']
            election_end = election['end_date']
            now = datetime.now()
            if election_start <= now <= election_end:
                election_active = True

        cursor.execute("""
            SELECT candidate_name, gender, id_card, email, party_name, party_logo, profile_pic 
            FROM candidate
        """)
        candidates = cursor.fetchall()

        if request.method == 'POST':
            if not election_active:
                flash("❌ Voting is closed!", "danger")
                return redirect(url_for('voter_voting_page'))

            selected_id = request.form.get('selected_candidate')
            if not selected_id:
                flash("❌ Please select a candidate!", "danger")
                return redirect(url_for('voter_voting_page'))

            selected = next((c for c in candidates if c['id_card'] == selected_id), None)
            if not selected:
                flash("❌ Invalid candidate selected!", "danger")
                return redirect(url_for('voter_voting_page'))

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
            flash("✅ Your vote has been recorded successfully!", "success")
            return redirect(url_for('voter_voting_page'))

        cursor.close()
        conn.close()

    except Exception as e:
        flash(f"❌ Database error: {e}", "danger")
        return redirect(url_for('voter_voting_page'))

    return render_template(
        'voter/voting_page.html',
        candidates=candidates,
        election_active=election_active,
        election_start=election_start,
        election_end=election_end
    )

# voter see result
@app.route('/voter/see_results')
def voter_results():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Get the latest active election
        cursor.execute("SELECT * FROM elections WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")
        election = cursor.fetchone()

        # If no active election
        if not election:
            return render_template('voter/see_results.html', results=None, election_start=None, election_end=None)

        now = datetime.now()
        # If election hasn't ended yet, do not show results
        if now < election['end_date']:
            return render_template(
                'voter/see_results.html',
                results=None,
                election_start=election['start_date'],
                election_end=election['end_date']
            )

        # Election ended → fetch results
        cursor.execute("""
            SELECT party_name, candidate_name, COUNT(*) as total_votes
            FROM votes_full
            GROUP BY party_name, candidate_name
            ORDER BY total_votes DESC;
        """)
        results = cursor.fetchall()

        return render_template(
            'voter/see_results.html',
            results=results,
            election_start=election['start_date'],
            election_end=election['end_date']
        )

    except Exception as e:
        print("Error fetching results:", e)
        return render_template('voter/see_results.html', results=None, election_start=None, election_end=None)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Votes per candidate
@app.route("/chart/votes")
def votes_chart():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT candidate_name, COUNT(*) AS total_votes
            FROM votes_full
            WHERE candidate_name IS NOT NULL
              AND candidate_name != ''
            GROUP BY candidate_name
            ORDER BY total_votes DESC
        """)

        rows = cursor.fetchall()

        labels = [row[0] for row in rows]
        votes = [int(row[1]) for row in rows]

        return jsonify({
            "labels": labels,
            "votes": votes
        })

    except Exception as e:
        print("Votes chart error:", e)

        return jsonify({
            "labels": [],
            "votes": [],
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()

# Votes per parties
@app.route("/chart/parties")
def parties_chart():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT party_name, COUNT(*) AS total_votes
            FROM votes_full
            WHERE party_name IS NOT NULL
              AND party_name != ''
            GROUP BY party_name
            ORDER BY total_votes DESC
        """)

        rows = cursor.fetchall()

        labels = [row[0] for row in rows]
        votes = [int(row[1]) for row in rows]

        return jsonify({
            "labels": labels,
            "votes": votes
        })

    except Exception as e:
        print("Party chart error:", e)

        return jsonify({
            "labels": [],
            "votes": [],
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()

# Candidates Total
@app.route("/dashboard-stats")
def dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Candidates
    cursor.execute("""
        SELECT COUNT(*) 
        FROM candidate
    """)
    total_candidates = cursor.fetchone()[0]

    # Total Voters
    cursor.execute("""
        SELECT COUNT(*) 
        FROM voting_registration
    """)
    total_voters = cursor.fetchone()[0]

    # Total Votes Cast
    cursor.execute("""
        SELECT COUNT(*)
        FROM votes_full
    """)
    votes_cast = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({
        "total_candidates": total_candidates,
        "total_voters": total_voters,
        "votes_cast": votes_cast
    })

# Winner Party
@app.route("/winner-party")
def winner_party():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT party_name, COUNT(*) AS total_votes
        FROM votes_full
        WHERE party_name IS NOT NULL
          AND party_name != ''
        GROUP BY party_name
        ORDER BY total_votes DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # Agar votes table empty hai
    if not rows:
        return jsonify({
            "winner_parties": [],
            "total_votes": 0
        })

    # Highest votes
    max_votes = int(rows[0][1])

    # Jitni parties ke votes highest ke equal hain
    winner_parties = [
        row[0]
        for row in rows
        if int(row[1]) == max_votes
    ]

    return jsonify({
        "winner_parties": winner_parties,
        "total_votes": max_votes
    })

# DashBoard Route
@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin/dashboard.html")

# admin admin home ppage
@app.route('/admin/admin_page', methods=['GET', 'POST'])
def admin_page():
    return render_template('admin/admin_page.html')

# candidate candidate home page
@app.route('/candidate/candidate_home_page', methods=['GET', 'POST'])
def candidate_candidate_home_page():
    return render_template('candidate/candidate_home_page.html')

# voter voter home page
@app.route('/voter/voter_home_page')
def voter_voter_home_page():
    return render_template('voter/voter_home_page.html')

# voter polling station location
@app.route('/voter/polling_station_location')
def voter_polling_station_location():
    return render_template('voter/polling_station_location.html')

# Flask App Run
if __name__ == '__main__':
    app.run(debug=True)