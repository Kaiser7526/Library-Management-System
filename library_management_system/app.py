# app.py (Backend - Flask)
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    published_date = db.Column(db.Date)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='book', lazy=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='member', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(days=14))

@app.route('/')
def index():
    return render_template('index.html',
                         book_count=Book.query.count(),
                         member_count=Member.query.count(),
                         overdue_count=Transaction.query.filter(Transaction.return_date == None,
                                                              Transaction.due_date < datetime.now()).count())

@app.route('/books')
def books():
    search_query = request.args.get('q', '')
    if search_query:
        books = Book.query.filter(Book.title.contains(search_query) | 
                                Book.author.contains(search_query) |
                                Book.isbn.contains(search_query))
    else:
        books = Book.query.all()
    return render_template('books.html', books=books)

@app.route('/members')
def members():
    members = Member.query.all()
    return render_template('members.html', members=members)

@app.route('/transactions')
def transactions():
    transactions = Transaction.query.filter_by(return_date=None).all()
    books = Book.query.filter(Book.quantity > 0).all()  # Fetch available books
    members = Member.query.all()  # Fetch all members
    return render_template('transactions.html', transactions=transactions, books=books, members=members)

@app.route('/add_book', methods=['POST'])
def add_book():
    new_book = Book(
        title=request.form['title'],
        author=request.form['author'],
        isbn=request.form['isbn'],
        published_date=datetime.strptime(request.form['published_date'], '%Y-%m-%d'),
        quantity=request.form['quantity']
    )
    db.session.add(new_book)
    db.session.commit()
    return redirect(url_for('books'))

@app.route('/checkout', methods=['POST'])
def checkout():
    transaction = Transaction(
        book_id=request.form['book_id'],
        member_id=request.form['member_id']
    )
    db.session.add(transaction)
    book = Book.query.get(request.form['book_id'])
    book.quantity -= 1
    db.session.commit()
    return redirect(url_for('transactions'))

@app.route('/return_book/<int:transaction_id>')
def return_book(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    transaction.return_date = datetime.utcnow()
    book = Book.query.get(transaction.book_id)
    book.quantity += 1
    db.session.commit()
    return redirect(url_for('transactions'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)