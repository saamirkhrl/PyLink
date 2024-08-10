from flask import Flask, redirect, request, url_for, render_template, abort
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from flask_sqlalchemy import SQLAlchemy
import requests
import random, string
from urllib.parse import urlparse
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(1000)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

WEBHOOK_URL = "you_will_have_to_make_your_own_webhook_for_this_feature_to_work"

db = SQLAlchemy(app)

class Link(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    original_link = db.Column(db.String())
    short_link = db.Column(db.String())

    def __repr__(self):
        return f'ID: {self.id}, Original Link: {self.original_link}, Shortened Link: {self.short_link}'

class LinkInputForm(FlaskForm):
    link_input = StringField('', validators=[DataRequired()], render_kw={"placeholder": "Enter your original here.."})
    submit = SubmitField("Generate short link")

def normalize_url(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        return 'http://' + url
    elif parsed_url.scheme not in ['http', 'https']:
        return 'https://' + parsed_url.path
    return url

def send_webhook_message(id, original_url, short_url):
    data = {
        "embeds": [{
            "title": "New URL Created",
            "fields": [
                {"name": "ID", "value": str(id)},
                {"name": "Original URL", "value": original_url},
                {"name": "Short URL", "value": short_url}
            ]
        }]
    }
    requests.post(WEBHOOK_URL, json=data)

@app.route('/', methods=['GET', 'POST'])
def home():
    form = LinkInputForm()
    shortened_link = None
    original_link_input = None

    if request.method == "POST":
        original_link_input = request.form.get('link_input')
        
        original_link_input = normalize_url(original_link_input)
        
        db_link = Link.query.filter_by(original_link=original_link_input).first()
        
        if db_link:
            shortened_link = db_link.short_link
        else:
            while True:
                shortened_link = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5))
                if not Link.query.filter_by(short_link=shortened_link).first():
                    break
            
            new_link = Link(original_link=original_link_input, short_link=shortened_link)
            db.session.add(new_link)
            db.session.commit()

    return render_template('index.html', form=form, orig_link=original_link_input, short_link=shortened_link)


@app.route('/<short_url>')
def redirect_to_original(short_url):
    link = Link.query.filter_by(short_link=short_url).first()
    if link:
        if not urlparse(link.original_link).scheme:
            link.original_link = 'http://' + link.original_link
        return redirect(link.original_link)
    else:
        return abort(404)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
