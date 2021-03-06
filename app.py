from flask import Flask,render_template,request
import joblib
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from pattern.en import sentiment
from pattern.en import parse, Sentence
from pattern.en import modality, mood

DIM_REDUCTION = True



clf = joblib.load('model_Fake_Satire.pkl')

app = Flask(__name__)

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/predict',methods=['POST'])
def predict():

    message = request.form['message']
    data = [message]
    df = pd.DataFrame(data, columns=['Text'])

    classifier = joblib.load('model_Fake_Satire.pkl')
    pca = joblib.load('PCA.pkl')

    # adding bert features
    model = SentenceTransformer('stsb-bert-base')
    embbed_text = df['Text'].apply(lambda x: model.encode(x))
    embbed_text = np.array(embbed_text.tolist())
    embbed_df = pd.DataFrame(embbed_text)
    df = pd.concat([df, embbed_df], axis=1)

    # add number of words
    df['word_num'] = df['Text'].apply(lambda s: len(s.split()))

    # add sentiment and mood and modality
    df['polarity'], df['subjectivity'] = sentiment(df['Text'][0])
    row = parse(df['Text'][0], lemmata=True)
    row = Sentence(row)
    df['modality'] = modality(row)
    #build some sort of a one hot encoding for the mood.
    mood_series = pd.Series(['indicative', 'imperative', 'conditional', 'subjunctive'])
    vals = (mood_series == mood(row)).astype(int)
    temp = pd.DataFrame([mood_series, vals])
    temp.columns = temp.iloc[0]
    temp.drop(0, axis=0, inplace=True)
    temp = temp.reset_index(drop=True)
    df = pd.concat([df, temp], axis=1)

    # drop text column
    df.drop('Text', axis=1, inplace=True)

    # #using PCA
    x_pca = pca.transform(df)

    my_prediction = classifier.predict(x_pca)
    return render_template('result.html', prediction=my_prediction)



if __name__ == '__main__':
    app.run(debug=True)