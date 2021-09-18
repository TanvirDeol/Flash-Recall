from flask import Flask, render_template,request
from flask_wtf import FlaskForm
from wtforms import FileField
from flask_uploads import configure_uploads, IMAGES, UploadSet
import img2txt

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisisasecret'
app.config['UPLOADED_IMAGES_DEST'] = 'uploads/images'

images = UploadSet('images', IMAGES)
configure_uploads(app, images)


class MyForm(FlaskForm):
    image = FileField('image')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MyForm()
    print(form.image.__class__)
    if form.validate_on_submit():
        filename = images.save(form.image.data)
        resp = request.form.get("chk")
        hlight = True
        if resp==None:
            hlight = False
        print("HERE ",hlight)
        print(filename)
        #call method that takes img directory, opens it, converts it and runs it thru method and returns text.
        [q,a] = img2txt.conv_img(filename,hlight)
        #print the text on html
        return render_template('cards.html', cssdir = "static/style.css", jsdir = "static/script.js", questions=q,answers =a,N=len(q))
    return render_template('index.html', form = form, cssdir = "static/style.css", logodir="static/translogo.png",jsdir = "static/script.js")
if __name__==('__main__'):    app.run(debug=True)
