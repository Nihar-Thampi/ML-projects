from flask import Flask, render_template, request, redirect, jsonify, Response
from keras.models import load_model
from keras.preprocessing import image
from keras.utils import load_img
from keras.utils import img_to_array
import numpy as np
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS


app=Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
model =load_model('final.h5')

UPLOAD_FOLDER="uploads" 

model.make_predict_function()


def predict_label(img_path):
    img = load_img(img_path, target_size=(351, 351))
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    a = np.argmax(model.predict(x), axis=1)
    class_names = ['African Leopard', 'Caracal', 'Cheetah', 'Clouded leopard', 'Jaguar', 'Lions', 'Ocelot', 'Puma', 'Snow Leopard', 'Tiger']
    y_pred = model.predict(x)
    class_idx = np.argmax(y_pred, axis=1)[0]
    class_name = class_names[class_idx]
    return class_name



@app.route("/",methods=['GET','POST'])
def main():
    return render_template('index.html')

@app.route("/home",methods=['GET','POST'])
def predict():
    return render_template('home.html')

@app.route('/prediction', methods=['GET','POST'])
def prediction():
    if request.method=='POST':
        file = request.files.get("file")
        if file:
            filename = secure_filename(file.filename)       
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            p = predict_label(file_path)
            return render_template('predict.html', prediction=p, img_path=file_path, img=filename)
    return render_template('form.html')

if __name__=='__main__':
    app.run(debug = False)