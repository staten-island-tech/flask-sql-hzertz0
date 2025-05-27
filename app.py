from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 📌 Tell Flask where the database file will be stored
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hangman.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 📌 Create the database object
db = SQLAlchemy(app)

# 📌 Custom Jinja filter to sort and join guessed letters
@app.template_filter('sort_letters')
def sort_letters(s):
    return sorted(set(s))  # Removes duplicates and sorts letters

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_to_guess = db.Column(db.String(100), nullable=False)
    guessed_letters = db.Column(db.String(100), default="")
    incorrect_guesses = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="Playing")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    word = request.form.get('word').lower()  # Later you can automate random words
    new_game = Game(word_to_guess=word)
    db.session.add(new_game)
    db.session.commit()
    return redirect(url_for('play_game', game_id=new_game.id))

@app.route('/game/<int:game_id>', methods=['GET', 'POST'])
def play_game(game_id):
    game = Game.query.get_or_404(game_id)

    if request.method == 'POST':
        letter = request.form.get('letter', '').lower()

        # ✅ Accept only a–z guesses; ignore punctuation/space submits
        if letter.isalpha() and letter not in game.guessed_letters:
            game.guessed_letters += letter
            if letter not in game.word_to_guess.lower():
                game.incorrect_guesses += 1

    # ✅ Re‑compute game status every request
    letters_to_guess = {c.lower() for c in game.word_to_guess if c.isalpha()}
    if letters_to_guess.issubset(set(game.guessed_letters)):
        game.status = 'You won!'
    elif game.incorrect_guesses >= 6:
        game.status = f'Ran out of tries! Word: {game.word_to_guess}'
    else:
        game.status = 'Playing'

    db.session.commit()
    return render_template('game.html', game=game)

import json
import random
from flask import session

app.secret_key = 'idk_what_this_is'

@app.route('/single_player', methods=['GET'])
def single_player():
    with open('words.json') as f:
        words = json.load(f)['words']

    # Get last word safely
    last_word = session.get('last_word')

    # Try to exclude the last word, if it's valid and there are other options
    available_words = words.copy()
    if last_word and len(words) > 1:
        available_words = [word for word in words if word != last_word]

    # Pick a new word from available list
    random_word = random.choice(available_words)

    # Save this word to session to prevent repeat next time
    session['last_word'] = random_word

    # Start a new game
    new_game = Game(word_to_guess=random_word)
    db.session.add(new_game)
    db.session.commit()
    return redirect(url_for('play_game', game_id=new_game.id))

# Change this to a secure password
ADMIN_PASSWORD = "freeadmin2019"

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Incorrect password"
    return render_template('admin_login.html', error=error)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        word = request.form.get('new_word').lower()
        with open('words.json', 'r+') as f:
            data = json.load(f)
            if word not in data['words']:
                data['words'].append(word)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        return redirect(url_for('admin_panel'))

    return render_template('admin.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
