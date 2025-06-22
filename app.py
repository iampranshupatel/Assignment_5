from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from models import db, User, Event

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Ensure tables are created at startup (works with any Flask version)
with app.app_context():
    db.create_all()

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if User.query.filter_by(username=uname).first():
            flash('Username already exists.', 'danger')
        else:
            user = User(username=uname)
            user.set_password(pwd)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname).first()
        if user and user.check_password(pwd):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    events = Event.query.filter_by(user_id=current_user.id) \
                        .order_by(Event.date, Event.time).all()
    return render_template('index.html', events=events)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        e = Event(
            title=request.form['title'],
            description=request.form['description'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            time=datetime.strptime(request.form['time'], '%H:%M').time(),
            location=request.form['location'],
            user_id=current_user.id
        )
        db.session.add(e)
        db.session.commit()
        flash('Event added.', 'success')
        return redirect(url_for('index'))
    return render_template('add_event.html')


@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    e = Event.query.get_or_404(event_id)
    if e.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        e.title = request.form['title']
        e.description = request.form['description']
        e.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        e.time = datetime.strptime(request.form['time'], '%H:%M').time()
        e.location = request.form['location']
        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('index'))

    return render_template('edit_event.html', event=e)


@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    e = Event.query.get_or_404(event_id)
    if e.user_id == current_user.id:
        db.session.delete(e)
        db.session.commit()
        flash('Event deleted.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)