
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
from keras.models import Sequential
from keras.layers import SimpleRNN, Dense, LSTM, Embedding, Flatten, Dropout,Bidirectional
from keras.preprocessing import sequence
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

"""#**1-  Exploratory Data Analysis**

##**1-1 Import Data**
Yelp reviews - Polarity
- training set
- test set
"""

# Commented out IPython magic to ensure Python compatibility.
# import data
!wget -nc https://s3.amazonaws.com/fast-ai-nlp/yelp_review_polarity_csv.tgz
!tar xvzf yelp_review_polarity_csv.tgz
# %cd yelp_review_polarity_csv/

"""##**1-2 Read Data**
CSV to dataframe\
Set variables' name:
- "lablel" : class of review
 - 1 = negative
 - 2 = positive
- "text" : content of review
"""

yelp_review_train = pd.read_csv("train.csv", header=None, names=["label", "text"])
yelp_review_test = pd.read_csv("test.csv", header=None, names=["label", "text"])

yelp_review_train.head(n=3)

print('train set sample size:\t n = ',len(yelp_review_train))
print('train set labels:\t', np.unique(yelp_review_train.label))

yelp_review_test.head(n=3)

print('test set sample size:\t n = ',len(yelp_review_test))
print('test labels:\t', np.unique(yelp_review_test.label))

"""##**1-3 Evaluate Missing Values**"""

#train set
empty_train_text = [index for index,text in enumerate(yelp_review_train.text.values) 
if str(text).strip() == '']
empty_train_label = yelp_review_train.label.isnull().sum()

# test set
empty_test_text = [index for index,text in enumerate(yelp_review_test.text.values) 
if str(text).strip() == '']
empty_test_label = yelp_review_test.label.isnull().sum()

print('dataset \t Filed \t\t Missing')
print('train \t\t text \t\t', len(empty_train_text))
print('train \t\t label \t\t', empty_train_label)
print('test \t\t text \t\t', len(empty_test_text))
print('test \t\t label \t\t', empty_test_label)

"""##**1-4 Evaluate Class Balance**"""

fig = plt.figure(figsize=(12,3))
ax1=fig.add_subplot(1,2,1)
ax2 = fig.add_subplot(122)
sns.countplot("label", data=yelp_review_train, ax=ax1).set(title='train set')
sns.countplot("label", data=yelp_review_test, ax=ax2).set(title='test set')
plt.show()

"""##**1-5 Visualization - Word Could**"""

# positive reviews
positive= yelp_review_train[yelp_review_train.label.eq(2)]

text = ''
for news in positive.values:
    text += f" {news}"
wordcloud = WordCloud(width = 2000, height = 1000, background_color = 'black',
    stopwords = set(nltk.corpus.stopwords.words("english"))).generate(text)
fig = plt.figure(figsize = (16, 7), facecolor = 'k', edgecolor = 'k')
plt.imshow(wordcloud, interpolation = 'bilinear')
plt.axis('off')
plt.tight_layout(pad=0)
plt.show()

# negative reviews
negative= yelp_review_train[yelp_review_train.label.eq(1)]

text = ''
for news in negative.values:
    text += f" {news}"
wordcloud = WordCloud(width = 2000, height = 1000, background_color = 'black',
    stopwords = set(nltk.corpus.stopwords.words("english"))).generate(text)
fig = plt.figure(figsize = (16, 7), facecolor = 'k', edgecolor = 'k')
plt.imshow(wordcloud, interpolation = 'bilinear')
plt.axis('off')
plt.tight_layout(pad=0)
plt.show()

"""#**2- Input Preparation**

##**2-1 Subset dataset**
"""

review_train = yelp_review_train.sample(frac=0.3, random_state=2021)
print(review_train.shape)

"""##**2-2 Define X and Y**"""

# train set
x_train=yelp_review_train.text
y_train =yelp_review_train.label

# test set
x_test=yelp_review_test.text
y_test =yelp_review_test.label

"""##**2-3 Transform to Binary Class**"""

# train set
y_train =y_train - 1

# test set
y_test =y_test - 1

x_train.head()

y_train.head()

"""##**2-4 Text Cleaning**
Removing StopWords, Punctuations and single-character words
"""

# before cleaning
x_train[0]

def clean(x):
  M = []
  stop_words = set(nltk.corpus.stopwords.words("english"))
  tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
  lemmatizer = nltk.WordNetLemmatizer() 
  for par in x:
      tmp = []
      sentences = nltk.sent_tokenize(par)
      for sent in sentences:
          sent = sent.lower()
          tokens = tokenizer.tokenize(sent)
          filtered_words = [w.strip() for w in tokens
                            if w not in stop_words and len(w) > 1 
                            and not w.isdigit()]
          tmp.extend(filtered_words)
          lem = ' '.join([lemmatizer.lemmatize(w) for w in tmp])
      M.append(lem)
  return (M)

x_train_clean =clean(x_train)
x_test_clean =clean(x_test)


# ______________________________________________________________________________
# from google.colab import drive
# drive.mount('/gdrive')

# x_train_clean = pd.read_csv("/gdrive/My Drive/clean_train.csv")
# https://drive.google.com/file/d/1yc2Qy0dZC4Coj9RwiDVENhNTGQSLPXyq/view?usp=sharing

# x_test_clean = pd.read_csv("/gdrive/My Drive/clean_train.csv")
# https://drive.google.com/file/d/1MDGXRl5_OHGDOt1pnBn1RyZFZwF_1udv/view?usp=sharing

# after cleaning
x_train_clean[0]

"""##**2-5 Text to Vector**

Vectorizing the text corpus, by turning each
review text into a sequence of integers where each integer being the index of a token in a dictionary (based on the training set vocabulary list).
"""

tokenizer = Tokenizer()
tokenizer.fit_on_texts(x_train_clean)
print('vocabulary size =', len(tokenizer.word_index))
# vocab_size = len(tokenizer.word_index) + 1

"""Training set has a very large vocabulary size (209,526 unique words in corpus).\
In order to reduce run time, a lower vocabulary size is used for the next steps.


**with # & no lem= 224,754
"""

vocab_size = 10000
tokenizer = Tokenizer(vocab_size)
tokenizer.fit_on_texts(x_train_clean)

"""Transforming each review  text to a sequence of integers. Only words known by the tokenizer will be taken into account."""

x_train = tokenizer.texts_to_sequences(x_train_clean)
x_test = tokenizer.texts_to_sequences(x_test_clean)

list(tokenizer.word_index.items())[0:10]

np.array(x_train[0])

"""##**2-6 Padding**"""

# Evaluate review length after cleaning
plt.hist([len(x) for x in x_train], bins=500)
plt.show()

myx = np.array([len(x) for x in x_train])
print('\n',round(100 *len(myx[myx < 200])/len(x_train),1), 
      '% of reviews have less than 200 words')
print('\n longest review has', max(myx), 'words')

# apply padding with max length of 200
maxlen = 200
x_train = sequence.pad_sequences(x_train, maxlen=maxlen, padding='post', truncating='post')
x_test = sequence.pad_sequences(x_test, maxlen=maxlen, padding='post', truncating='post')

x_train[1]

"""#**3- Model Training**
1- Sequential input: Temporal dependency between words in a review

2- Different input length

3- Long text inputs (200 words after truncation): Long term dependencies

4- Binary output

**=> Sequential Neural Network with Many???to???One Recurrent Architecture and LSTM layer**
- Positive  review\
![picture](https://drive.google.com/uc?id=1hG0kTg4dU5Jw_QE0mkJAgT56dt0DC8ZZ)

- Negative  review\
![picture](https://drive.google.com/uc?id=16iOc2wamVldrRWEYJXF07CE_hhql_P2Q)





"""

# Embedding Output Dimension
dim = 64

# Early Stopping
early_stop = EarlyStopping(monitor='val_loss', patience=1, restore_best_weights=True)

# Plot training history

def history_plt(history):

  history_dict = history.history
  acc = history_dict['acc']
  val_acc = history_dict['val_acc']
  loss = history_dict['loss']
  val_loss = history_dict['val_loss']
  epochs = history.epoch

  plt.figure(figsize=(20,6))
  plt.subplot(1, 2, 1)
  plt.plot(epochs, loss, 'g', label='Training loss')
  plt.plot(epochs, val_loss, 'b', label='Validation loss')
  plt.title('Training and validation loss', size=15)
  plt.xlabel('Epochs', size=15)
  plt.ylabel('Loss', size=15)
  plt.legend(prop={'size': 15})

  plt.subplot(1, 2, 2)
  plt.plot(epochs, acc, 'g', label='Training accuracy')
  plt.plot(epochs, val_acc, 'b', label='Validation accuracy')
  plt.title('Training and validation accuracy', size=15)
  plt.xlabel('Epochs', size=15)
  plt.ylabel('Accuracy', size=15)
  plt.legend(prop={'size': 15})
  plt.ylim((0.5,1))

  return plt.show()

"""##**3-1 Model 1: RNN**
- one Embedding layer
- one RNN layer
- one Dropout layer
- one Dense layer
"""

model_1 = Sequential([Embedding(vocab_size, dim, mask_zero=True),
                   SimpleRNN(64),
                   Dropout(0.3),
                   Dense(1, activation='sigmoid')
                   ])
model_1.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
model_1.summary()

"""###**3-1-1 Fit RNN on training data**"""

history_1 = model_1.fit(x_train, y_train, epochs=3, validation_split=0.3, callbacks=[early_stop])

"""###**3-1-2 RNN Learning progress**
 
 Variation of accuracy and loss at different epochs
"""

history_plt(history_1)

"""##**3-2 Model 2: LSTM**

- one Embedding layer
- one LSTM layer
- one Dense layer

"""

model_2 = Sequential([Embedding(vocab_size, dim, mask_zero=True),
                   LSTM(128),
                   Dense(1, activation='sigmoid')
                   ])
model_2.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
model_2.summary()

"""###**3-2-1 Fit LSTM on Training Data**"""

history_2 = model_2.fit(x_train, y_train, epochs=10,validation_split=0.2, callbacks=[early_stop])

"""###**3-2-2 LSTM Learning Progress**
 
 Variation of accuracy and loss at different epochs
"""

history_plt(history_2)

"""##**3-3 Model 3: Bidirectional**

- one Embedding layer
- two Bidirectional LSTM layers
- one Dropout layer
- two Dense layers
"""

model_3a = Sequential([
    Embedding(vocab_size, dim, mask_zero=True),
    Bidirectional(LSTM(128)),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
    ])

model_3a.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
model_3a.summary()

"""###**3-3-1 Fit Bidirectional on Training Data**"""

history_3a = model_3a.fit(x_train, y_train, validation_split=0.3, epochs=ep, callbacks=[early_stop])

history_3a = model_3a.fit(x_train, y_train, validation_split=0.1, epochs=1, callbacks=[early_stop])

"""###**3-3-2 Bidirectional Learning Progress**
 
 Variation of accuracy and loss at different epochs
"""

history_plt(history_3a)

model_3b = Sequential([
    Embedding(vocab_size, dim, mask_zero=True),
    Bidirectional(LSTM(64,  return_sequences=True)),
    Bidirectional(LSTM(32),
    Dense(32, activation='relu'),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
    ])

model_3b.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
model_3b.summary()

history_3b = model_3b.fit(x_train, y_train, validation_split=0.3, epochs=ep, callbacks=[early_stop])

history_plt(history_3b)

model_3c = Sequential([
    Embedding(vocab_size, dim, mask_zero=True),
    Bidirectional(LSTM(100,  return_sequences=True)),
    Bidirectional(LSTM(64)),
    Dense(32, activation='relu'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
    ])

model_3c.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
model_3c.summary()

history_3c = model_3c.fit(x_train, y_train, validation_split=0.3, epochs=ep, callbacks=[early_stop])

history_plt(history_3c)

"""##**3-4 Model 4: Flatten**

- one Embedding layer
- one Flatten layer
- one Dropout layer
- two Dense layers
"""

# model_4 = Sequential([Embedding(vocab_size, dim),
#                     Flatten(),
#                     Dropout(rate=0.4),
#                     Dense(100, activation='relu'),
#                     Dense(1, activation='sigmoid')])
# model_4.compile(optimizer='adam',
#               loss='binary_crossentropy',
#               metrics=['accuracy'])
# model_4.summary()

"""###**3-4-1 Fit Flatten on training data**"""

# history_4= model_4.fit(x_train, y_train, epochs=ep, validation_split=0.3, callbacks=[early_stop])

"""#**4- Model Selection**

Select the best performing model.
"""

Best_model = model_2
history = history_2

"""#**5- Forecast**
Predict labels on test set with selected model 
"""

pred = (Best_model.predict(x_test) >= 0.5).astype("int")

mat = confusion_matrix(y_test, pred)
sns.set(font_scale=1.4)
sns.heatmap(mat.T, square=True, annot=True, fmt='d', cbar=False, cmap='viridis',
            xticklabels=['negative','positive'], yticklabels=['negative','positive'])
plt.xlabel('True Class')
plt.ylabel('Predicted Class')

print("Accuracy on test set = ", 100*round(accuracy_score(y_test, pred),4), '%\n')
print(classification_report(y_test, pred))
