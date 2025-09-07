import random
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_cors import CORS
import mysql.connector
import smtplib
from email.message import EmailMessage

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


@app.route('/voter_home_page')
def voter_home_page():
    return render_template('voter_home_page.html')


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

        if password != confirm_password:
            flash("❌ Passwords do not match!", "error")
            return redirect(url_for('signup'))

        # generate OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['user_data'] = {
            'username': username,
            'gender': gender,
            'idcard': idcard,
            'email': email,
            'password': password
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
                cursor.execute("""
                    INSERT INTO signup (user_name, gender, id_card, email, password)
                    VALUES (%s, %s, %s, %s, %s)
                """, (data['username'], data['gender'], data['idcard'], data['email'], data['password']))
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

# LOGIN 
@app.route('/login', methods=['GET', 'POST'])
def login():
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

            cursor2 = conn.cursor()
            if user:
                cursor2.execute("INSERT INTO login (id_card, password) VALUES (%s, %s)", (idcard, password,))
                conn.commit()
                return redirect(url_for('voter_home_page'))
            else:
                flash("❌ Invalid idcard or password!", "error")

            cursor.close()
            cursor2.close()
            conn.close()

        except Exception as e:
            flash(f"❌ Database error: {e}", "error")

    return render_template('login.html')

# VOTING REGISTRATION 
@app.route('/voteing_registration', methods=['GET', 'POST'])
def voteing_registration():
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
            return redirect(url_for('verify_voting_otp'))
        except Exception as e:
            flash(f"❌ Error sending OTP: {e}", "error")

    return render_template('voteing_registration.html')

# verify otp voting registration
@app.route('/verify_voting_otp', methods=['GET', 'POST'])
def verify_voting_otp():
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

                flash("✅ Voting Registration successful!", "success")
                return redirect(url_for('voting_page'))
            except Exception as e:
                flash(f"❌ Database error: {e}", "error")
        else:
            flash("❌ Invalid OTP!", "error")

    return render_template('verify_voting_otp.html')

# show timer
@app.route('/voting_page', methods=['GET', 'POST'])
def voting_page():
    # agar user direct voting page hit kare, pehle timer show hoga
    return render_template('voting_timer.html')

# voting registration
@app.route('/voting_start')
def voting_start():
    # yahan aap apna pehle se banaya hua voting_page.html render karoge
    candidates = [
        {"id":1, "party":"Tahreek-e-Labaik Pakistan (TLP)", "candidate":"Khadim Hussain Rizvi",
         "picture":"khadim_rizvi.jpg", "symbol":"tlp.jpg"},
        {"id":2, "party":"Pakistan Tehreek-e-Insaf (PTI)", "candidate":"Imran Khan",
         "picture":"imran.jpg", "symbol":"pti.jpg"},
        {"id":3, "party":"Pakistan Peoples Party (PPP)", "candidate":"Asif Zardari",
         "picture":"zardari.jpg", "symbol":"ppp.jpg"},
        {"id":4, "party":"Pakistan Muslim League (PML-N)", "candidate":"Shahabaz Sharif",
         "picture":"shahbaz.jpg", "symbol":"pmln.jpg"},
        {"id":5, "party":"Pakistan Awami Tehreek (PAT)", "candidate":"Tahir ul Qadri",
         "picture":"tahir_qadri.jpg", "symbol":"pat.jpg"},
        {"id":6, "party":"Pakistan Muslim League – Quaid (PML-Q)", "candidate":"Pervez Elahi",
         "picture":"pervez.jpg", "symbol":"pmlq.jpg"}
    ]

    if request.method == 'POST':
        selected_id = request.form.get('selected_candidate')
        if not selected_id:
            flash("❌ Please select a candidate!")
            return redirect('/voting_page')

        selected = next((c for c in candidates if str(c['id']) == selected_id), None)

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO votes_full (party_name, candidate_name, picture, party_symbol)
                VALUES (%s, %s, %s, %s)
            """, (selected['party'], selected['candidate'], selected['picture'], selected['symbol']))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/voting_page')

        except Exception as e:
            flash(f"❌ Database error: {e}")
            return redirect('/voting_page')

    return render_template('voting_page.html', candidates=candidates)

# Result screen
@app.route('/see_results')
def results():
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

    return render_template('see_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)