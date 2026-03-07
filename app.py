from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re
import secrets
from datetime import datetime, timedelta
import smtplib
import ssl
import os
# Database functions
from CardioCare.db import (
    create_tables,
    insert_user,
    get_user_by_email,
    insert_prediction,
    get_user_predictions,
    update_reset_token,
    get_user_by_reset_token,
    update_password,
    get_user_by_id,
    update_user_profile,
)

app = Flask(__name__)
app.secret_key = "cardiocare_secret_key"

# ---------------- EMAIL CONFIG ----------------
# Set these as environment variables in your system
EMAIL_HOST = os.getenv("CARDIO_EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("CARDIO_EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("CARDIO_EMAIL_USER")  # e.g. your Gmail address
EMAIL_PASS = os.getenv("CARDIO_EMAIL_PASS")  # e.g. app password
EMAIL_FROM = os.getenv("CARDIO_EMAIL_FROM", EMAIL_USER or "")


def send_reset_email(to_email, reset_url):
    """
    Send password reset email with link.
    Uses basic SMTP so you don't need extra libraries.
    Configure credentials via environment variables.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        # Email not configured; fail silently but inform user via flash in route
        return False

    subject = "CardioCare - Password Reset"
    body = f"""
Dear CardioCare user,

We received a request to reset the password for your CardioCare account.

To reset your password, click the link below (or copy-paste it into your browser):

{reset_url}

This link will expire in 1 hour. If you did not request this, you can ignore this email.

Best regards,
CardioCare Team
"""
    message = f"Subject: {subject}\nTo: {to_email}\nFrom: {EMAIL_FROM}\n\n{body}"

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, to_email, message.encode("utf-8"))
        return True
    except Exception:
        return False

# Create database tables at startup
create_tables()

# ---------------- HOME ----------------
@app.route('/login.html')



# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()

        # Backend validation
        errors = []
        
        # Name validation
        if not name:
            errors.append("Name is required")
        elif len(name) < 2:
            errors.append("Name must be at least 2 characters")
        elif not re.match(r'^[a-zA-Z\s]+$', name):
            errors.append("Name can only contain letters and spaces")
        
        # Email validation - Gmail only
        if not email:
            errors.append("Email is required")
        elif not email.endswith('@gmail.com'):
            errors.append("Only Gmail addresses (@gmail.com) are allowed")
        elif not re.match(r'^[a-zA-Z0-9._+-]+@gmail\.com$', email):
            errors.append("Invalid email format")
        
        # Password validation
        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters")
        elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', password):
            errors.append("Password must contain at least one uppercase letter, one lowercase letter, and one number")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Age validation
        if age:
            try:
                age_int = int(age)
                if age_int < 1 or age_int > 120:
                    errors.append("Age must be between 1 and 120")
            except ValueError:
                errors.append("Age must be a valid number")
        
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('register'))

        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash("Email already registered")
            return redirect(url_for('register'))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user
        age_int = int(age) if age else None
        insert_user(name, email, hashed_password, age_int, gender)

        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Validation
        if not email:
            flash("Email is required")
            return redirect(url_for('login'))
        if not password:
            flash("Password is required")
            return redirect(url_for('login'))

        user = get_user_by_email(email)

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password")
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    records = get_user_predictions(user_id)

    total_predictions = len(records)
    last = records[0] if records else None
    prev = records[1] if len(records) > 1 else None

    last_risk_level = last['risk_level'] if last else None
    last_risk_score = last['risk_score'] if last else None
    previous_risk_level = prev['risk_level'] if prev else None
    previous_risk_score = prev['risk_score'] if prev else None

    comparison_change = None
    if last_risk_score is not None and previous_risk_score is not None:
        comparison_change = round(last_risk_score - previous_risk_score, 2)

    # Chart data: oldest → newest
    history_labels = []
    history_scores = []
    for r in reversed(records):
        history_labels.append(r['prediction_date'])
        history_scores.append(r['risk_score'])

    # Notifications based on latest risk and trend
    notifications = []
    if last_risk_level == 'High':
        notifications.append({
            "icon": "fas fa-triangle-exclamation",
            "title": "High heart disease risk",
            "message": "Please consult a cardiologist as soon as possible and follow the recommended actions."
        })
    elif last_risk_level == 'Moderate':
        notifications.append({
            "icon": "fas fa-circle-exclamation",
            "title": "Moderate risk detected",
            "message": "You are at moderate risk. Focus on exercise, diet, and stress management."
        })
    elif last_risk_level == 'Low' and total_predictions > 0:
        notifications.append({
            "icon": "fas fa-circle-check",
            "title": "Low risk – keep it up",
            "message": "Your heart health looks good. Continue maintaining your healthy lifestyle."
        })

    if comparison_change is not None and previous_risk_score is not None:
        if comparison_change < 0:
            notifications.append({
                "icon": "fas fa-arrow-down-long",
                "title": "Risk improved",
                "message": f"Your risk score decreased by {abs(comparison_change)}%. Great progress – keep going!"
            })
        elif comparison_change > 0:
            notifications.append({
                "icon": "fas fa-arrow-up-long",
                "title": "Risk increased",
                "message": f"Your risk score increased by {comparison_change}%. Review your lifestyle habits carefully."
            })

    # Simple static article cards
    articles = [
        {
            "title": "Benefits of Regular Exercise",
            "description": "Discover how daily activity can significantly improve your heart health.",
            "image": "https://images.pexels.com/photos/3757376/pexels-photo-3757376.jpeg",
            "link": "https://www.who.int/news-room/fact-sheets/detail/physical-activity",
        },
        {
            "title": "Healthy Diet for Heart Care",
            "description": "Learn which foods protect your heart and which ones to avoid.",
            "image": "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg",
            "link": "https://www.heart.org/en/healthy-living/healthy-eating",
        },
        {
            "title": "How Stress Affects Your Heart",
            "description": "Understand the link between chronic stress and heart disease.",
            "image": "https://images.pexels.com/photos/4109996/pexels-photo-4109996.jpeg",
            "link": "https://www.heart.org/en/healthy-living/healthy-lifestyle/stress-management",
        },
    ]

    return render_template(
        'dashboard.html',
        last_risk_level=last_risk_level,
        last_risk_score=last_risk_score,
        total_predictions=total_predictions,
        previous_risk_level=previous_risk_level,
        previous_risk_score=previous_risk_score,
        comparison_change=comparison_change,
        history_labels=history_labels,
        history_scores=history_scores,
        notifications=notifications,
        articles=articles,
    )


# ---------------- FORGOT PASSWORD ----------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash("Email is required")
            return redirect(url_for('forgot_password'))
        
        if not email.endswith('@gmail.com'):
            flash("Only Gmail addresses are allowed")
            return redirect(url_for('forgot_password'))
        
        user = get_user_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)  # Token valid for 1 hour
            update_reset_token(email, token, expiry)

            # Build reset URL and send email
            reset_url = url_for('reset_password', token=token, _external=True)
            email_sent = send_reset_email(email, reset_url)

            if email_sent:
                flash("Password reset link has been sent to your email.")
                return redirect(url_for('login'))
            else:
                # Dev fallback: show reset link so you can still test
                flash("Email server is not configured on this machine. "
                      "Use the link below to reset your password (for testing only):")
                flash(reset_url)
                return redirect(url_for('reset_password', token=token))
        else:
            flash("Email not found")
            return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')


# ---------------- RESET PASSWORD ----------------
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = get_user_by_reset_token(token)
    
    if not user:
        flash("Invalid or expired reset token")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not password:
            flash("Password is required")
            return render_template('reset_password.html', token=token)
        
        if len(password) < 8:
            flash("Password must be at least 8 characters")
            return render_template('reset_password.html', token=token)
        
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', password):
            flash("Password must contain at least one uppercase letter, one lowercase letter, and one number")
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash("Passwords do not match")
            return render_template('reset_password.html', token=token)
        
        # Update password
        hashed_password = generate_password_hash(password)
        update_password(user['id'], hashed_password)
        
        flash("Password reset successful. Please login.")
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)


# ---------------- PREDICTION (RULE-BASED, USING USER INPUT DIRECTLY) ----------------
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        errors = []

        # -------------------------------
        # 1. RAW FORM DATA WITH VALIDATION
        # -------------------------------
        try:
            age = int(request.form.get('age', 0))
            if age < 1 or age > 120:
                errors.append("Age must be between 1 and 120")
        except (ValueError, TypeError):
            errors.append("Age must be a valid number")

        sex_text = request.form.get('sex', '').strip()
        if not sex_text or sex_text not in ['Male', 'Female']:
            errors.append("Please select a valid gender")

        chest_pain_text = request.form.get('chest_pain', '').strip()
        if not chest_pain_text or chest_pain_text not in ['Typical', 'Atypical', 'Non-anginal', 'Asymptomatic']:
            errors.append("Please select a valid chest pain type")

        heart_rate = request.form.get('heart_rate', '').strip()
        if not heart_rate:
            errors.append("Heart rate is required")

        bp_text = request.form.get('bp', '').strip()
        if not bp_text or bp_text not in ['Low', 'Normal', 'High']:
            errors.append("Please select a valid blood pressure level")

        smoking_text = request.form.get('smoking', '').strip()
        if not smoking_text or smoking_text not in ['yes', 'no']:
            errors.append("Please select smoking status")

        exercise_text = request.form.get('exercise', '').strip()
        if not exercise_text or exercise_text not in ['yes', 'no']:
            errors.append("Please select exercise status")

        diet_text = request.form.get('diet', '').strip()
        if not diet_text or diet_text not in ['Poor', 'Average', 'Healthy']:
            errors.append("Please select a valid diet option")

        stress_text = request.form.get('stress', '').strip()
        if not stress_text or stress_text not in ['Low', 'Medium', 'High']:
            errors.append("Please select a valid stress level")

        genetics_text = request.form.get('genetics', '').strip()
        if not genetics_text or genetics_text not in ['yes', 'no']:
            errors.append("Please select genetics status")

        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('predict'))

        # -------------------------------
        # 2. RULE-BASED RISK SCORING (YOUR ORIGINAL LOGIC)
        # -------------------------------
        risk_score = 0

        # Use lowercase for comparisons
        smoking_lower = smoking_text.lower()
        exercise_lower = exercise_text.lower()
        diet_lower = diet_text.lower()
        stress_lower = stress_text.lower()
        genetics_lower = genetics_text.lower()

        if smoking_lower == 'yes':
            risk_score += 2
        if exercise_lower == 'no':
            risk_score += 2
        if bp_text == 'High':
            risk_score += 2
        # Map diet: Poor ~ Unhealthy in your original logic
        if diet_lower == 'poor':
            risk_score += 1
        if stress_lower == 'High' or stress_lower == 'high':
            risk_score += 1
        if genetics_lower == 'yes':
            risk_score += 2
        if age > 45:
            risk_score += 1

        # -------------------------------
        # 3. RISK LEVEL FROM SCORE
        # -------------------------------
        if risk_score >= 7:
            risk_level = "High"
            color = "red"
        elif risk_score >= 4:
            risk_level = "Moderate"
            color = "yellow"
        else:
            risk_level = "Low"
            color = "green"

        # Convert to percentage-like score for UI (0–10 -> 0–100)
        risk_score_percent = round(min(risk_score, 10) / 10 * 100, 2)

        # -------------------------------
        # 4. PERSONALIZED RECOMMENDATIONS
        # -------------------------------
        recommendations = []
        health_tips = []

        if risk_level == "High":
            recommendations = [
                "Schedule an immediate consultation with a cardiologist",
                "Start medication as prescribed by your doctor",
                "Monitor your blood pressure daily",
                "Get an ECG and stress test done as soon as possible",
                "Avoid intense physical activity until cleared by a doctor"
            ]
            health_tips = [
                "Avoid all forms of smoking and tobacco products",
                "Eliminate alcohol consumption completely",
                "Follow a strict low-sodium, low-fat diet",
                "Take medications exactly as prescribed",
                "Keep emergency contact numbers handy"
            ]
        elif risk_level == "Moderate":
            recommendations = [
                "Book a comprehensive heart checkup within a month",
                "Consult with a cardiologist for preventive care",
                "Start a regular exercise routine after medical advice",
                "Monitor your blood pressure regularly"
            ]
            health_tips = [
                "Aim for 30-45 minutes of moderate exercise daily",
                "Increase intake of fruits, vegetables, and whole grains",
                "Limit junk food, sugary drinks, and salty snacks",
                "Practice stress-reduction techniques like yoga or meditation"
            ]
        else:
            recommendations = [
                "Continue your regular annual health checkups",
                "Maintain your current healthy lifestyle",
                "Stay active and keep monitoring your heart health"
            ]
            health_tips = [
                "Maintain a balanced diet rich in nutrients",
                "Avoid smoking and limit alcohol consumption",
                "Get 7-8 hours of quality sleep every night",
                "Stay physically and socially active"
            ]

        # -------------------------------
        # 5. STORE IN DATABASE
        # -------------------------------
        insert_prediction(
            session['user_id'],
            age,
            sex_text,
            chest_pain_text,
            int(heart_rate) if heart_rate else None,
            bp_text,
            smoking_text,
            diet_text,
            exercise_text,
            stress_text,
            genetics_text,
            risk_level,
            risk_score_percent
        )

        # -------------------------------
        # 6. SHOW RESULT
        # -------------------------------
        return render_template(
            "result.html",
            risk_score=risk_score_percent,
            risk_level=risk_level,
            color=color,
            recommendations=recommendations,
            health_tips=health_tips
        )

    return render_template("predict.html")

# ---------------- PROFILE ----------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age_raw = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()

        age = None
        if age_raw:
            try:
                age = int(age_raw)
            except ValueError:
                flash("Age must be a valid number")

        if not name:
            flash("Name is required")
        else:
            update_user_profile(session['user_id'], name, age, gender)
            session['user_name'] = name
            flash("Profile updated successfully")

        user = get_user_by_id(session['user_id'])

    return render_template('profile.html', user=user)


# ---------------- HISTORY ----------------
@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    records = get_user_predictions(session['user_id'])

    history_labels = []
    history_scores = []
    for r in reversed(records):
        history_labels.append(r['prediction_date'])
        history_scores.append(r['risk_score'])

    return render_template(
        'history.html',
        records=records,
        history_labels=history_labels,
        history_scores=history_scores,
    )

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for('login'))


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    # Configure for multiple concurrent users
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.run(debug=True, threaded=True)  # threaded=True allows concurrent requests

