from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 📌 Tell Flask where the database file will be stored
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 📌 Create the database object
db = SQLAlchemy(app)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_to_guess = db.Column(db.String(100), nullable=False)
    guessed_letters = db.Column(db.String(100), default="")
    incorrect_guesses = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="ongoing")

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
        letter = request.form.get('letter').lower()
        if letter not in game.guessed_letters:
            game.guessed_letters += letter
            if letter not in game.word_to_guess:
                game.incorrect_guesses += 1
        
        # Update status
        if all(l in game.guessed_letters for l in set(game.word_to_guess)):
            game.status = 'You won!'
        elif game.incorrect_guesses >= 12:
            game.status = (f"Ran out of tries! Word: {game.word_to_guess}")
        
        db.session.commit()

    return render_template('game.html', game=game)

if __name__ == '__main__':
    app.run(debug=True)