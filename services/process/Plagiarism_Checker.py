"""
Plagiarism_Checker_System_JSON_ver.py: Checking the content of uploaded work in the case of plagiarism in any form, whether it is accidental or intentional

Args:
    fiction_id (str): the story id of all work in database.
    chapter_id (str): the chapter id of all work in database.
    story (str): the content of the story of all work in database.

Returns:
    final (json): final similarity score and whether the file is safe to be uploaded or not.
    details (json): lines with high similarity and the related works.
"""

import json
import re
import requests
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
nltk.download('punkt')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
#ignore the warning
from tensorflow.keras.preprocessing.text import Tokenizer

import warnings
warnings.filterwarnings('ignore')

def request(story_url='https://readscape.live/pdftodatabase'):
    """
    Requesting and loading data from database.

    Args:
        story_url (str): url of database.

    Returns:
        story (pd.Dataframe): data loaded from database.
    """
    story = requests.get(story_url)
    story = story.json()
    story = pd.DataFrame(story['data'])
    return story, story_url
    
def remove(text):
    """
    Cleaning the unnecessary symbols inside the text.

    Args:
        text (str): text to be cleaned.

    Returns:
        words (str): cleaned text.
    """
    pattern = r'[“”‘’:;"?_\',.()\[\]]'
    sub_text = re.sub(pattern, '', text)
    pattern = r'[\-\–]'
    sub_text = re.sub(pattern, ' ', sub_text)
    token_text = word_tokenize(sub_text)
    words = [word for word in token_text if word]
    words = ' '.join(words)
    return words

def text_list(story_data):
    """
    Creating the text array.

    Args:
        story_data (pd.Dataframe): story texts from database.

    Returns:
        lists (array): list of cleaned texts.
    """
    lists = []
    for _, row in story_data.iterrows():
        list_arr = []
        text_to_line = sent_tokenize(row[-4].lower())
        for text in text_to_line:
            list_arr.append(remove(text))
        lists.append(list_arr)
    return lists

def tokenizing(flat_text, text):
    """
    Tokenizing the texts.

    Args:
        flat_text (array): flatted texts from all story.
        text (array): original array of the texts.

    Returns:
        tokenid (array): tokenized texts.
    """
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(flat_text)
    word_index = tokenizer.word_index
    tokenid = []
    for i in text:
        tokens = tokenizer.texts_to_sequences(i)
        tokenid.append(tokens)
    return tokenid

def vecTfid(flat_text, text):
    """
    Vectorizing the texts.

    Args:
        flat_text (array): flatted texts from all story.
        text (array): original array of the texts.

    Returns:
        vecarr (array): vectorized texts.
    """
    vec = TfidfVectorizer()
    vec.fit(flat_text)
    vecarr = []
    for i in text:
        transform = vec.transform(i).toarray()
        vecarr.append(transform)
    return vecarr

def add_values(story_dict, key, values, id):
    """
    Creating the similar text lines dictionary.

    Args:
        story_dict (dictionary): the dictionary to be used.
        key (str): text line of the story being checked.
        values (array): array of the text lines from the other story that has high similarity with key line.
        id (array): fiction_id and chapter_id of the other story.

    Returns:
        story_dict (dictionary): the dictionary filled with new values.
    """
    fic_id, chap_id = id

    story_dict.setdefault(key, {}).setdefault(fic_id, {}).setdefault(chap_id, [])

    for line in values:
        if line not in story_dict[key][fic_id][chap_id]:
            story_dict[key][fic_id][chap_id].append(line)

def count_flag(token1, token2, tf1, tf2, story_dict, text1, text2, id):
    """
    Detecting lines with high similarity.

    Args:
        token1 (array): the tokenized array of the story being checked.
        token2 (array): the tokenized array of the other story.
        tf1 (array): the vectorized array of the story being checked.
        tf2 (array): the vectorized array of the other story.
        story_dict (dictionary): the dictionary to be called in add_values function
        text1 (str): text of the story being checked.
        text2 (str): text of the other story.
        id (array): fiction_id and chapter_id of the other story

    Returns:
        plag_tf_token (int): number of lines with similarity >0.35 and <0.9999
        di (int): total number of line in the story being checked.
        hs (int): number of line with vectorized similarity >0.9999
        cp (int): number of line with tokenized similarity >0.9999
    """
    plag_tf_token = 0
    di = len(tf1)
    token_cos = []
    cp = 0
    hs = 0

    # Getting the similarity on Tokenized text and Vectorized text
    tf_cos = cosine_similarity(tf1,tf2)
    for i in range(len(token1)):
        cos_line= []
        for j in range(len(token2)):
            cos = len(set(token1[i])&set(token2[j]))/len(list(set(token1[i]+token2[j])))
            cos_line.append(cos)
        token_cos.append(cos_line)

    for i in range(di):
        tf = 0
        token = 0

        # For high similarity checking
        if any(vals >= 0.9999 for vals in tf_cos[i]):
            tryis = [index for index, vals in enumerate(tf_cos[i]) if vals >= 0.9999]
            add_values(story_dict, text1[i],[text2[i] for i in tryis], id)
            hs+=1
        elif any(0.35 < vals < 0.9999 for vals in tf_cos[i]):
            tryis = [index for index, vals in enumerate(tf_cos[i]) if 0.35 < vals < 0.9999]
            add_values(story_dict, text1[i],[text2[i] for i in tryis], id)
            tf = 1
        else:
            tf = 0

        # For high structure similarity checking
        if any(vals >= 0.9999 for vals in token_cos[i]):
          tryis = [index for index, vals in enumerate(token_cos[i]) if vals >= 0.9999]
          add_values(story_dict, text1[i],[text2[i] for i in tryis], id)
          cp+=1
        elif any(0.7 < vals < 0.9999 for vals in token_cos[i]):
          tryis = [index for index, vals in enumerate(token_cos[i]) if 0.7 < vals < 0.9999]
          add_values(story_dict, text1[i],[text2[i] for i in tryis], id)
          token = 1
        else:
          token = 0

        # For plagiarism checking score (other than copy-pasted or 99% similarity)
        if token + tf > 1:
          plag_tf_token += 1

    return plag_tf_token, di, hs, cp

def main_code(story_data, text_list):
    """
    Main code of the system, checking the newly uploaded story checked against other stories in database.

    Args:
        story_data (pd.DataFrame): Data loaded from database.
        text_list (array): list of cleaned text.

    Returns:
        final (json): final similarity score and whether the file is safe to be uploaded or not.
        details (json): lines with high similarity and the related works.
    """
    flat_text = [line for text in text_list for line in text]

    tfid = vecTfid(flat_text, text_list)
    token = tokenizing(flat_text, text_list)

    plag_score = 0
    fin_plag_score = 0
    verdict = ""
    YN = 0
    story_dict = {}

    for j in range(len(token)):
        if story_data.iloc[-1, 1] != story_data.iloc[j, 1]:
            plag_ft, di, hs, cp = count_flag(token[-1], token[j], tfid[-1], tfid[j], story_dict, text_list[-1],
                                             text_list[j], story_data.iloc[j, 1:3])
            plag_score = (plag_ft + (hs + cp) / 2) / di
        if plag_score > fin_plag_score:
            fin_plag_score = plag_score

    if fin_plag_score >= 0.3:
        YN = 1
        verdict = "Unfortunately, your plagiarism score has exceeded the maximum percentage. Please revise and try again."
    else:
        YN = 0
        verdict = "Congratulations, your plagiarism score is within safe percentage! You may upload your work!"

    if len(story_dict) == 0:
        add_values(story_dict, '-', '-', ['-', '-'])

    data = [{'Original Line': key, 'Fiction_id': fic_id, 'Chapter_id': chap_id, 'Similar Line': value}
            for key, file_dict in story_dict.items()
            for fic_id, chap_dict in file_dict.items()
            for chap_id, value in chap_dict.items()]
    
    df = pd.DataFrame(data)
    df_e = df.explode('Similar Line')
    df_e.reset_index(drop=True, inplace=True)

    final = {'Final Plagiarism Score': [fin_plag_score*100], 'Y/N': YN, 'Verdict': verdict, 
             'Original Fiction_id': story_data.iloc[-1,1], 'Matched Fiction_id': [id['Fiction_id'] for id in data]}

    details = df_e.to_json()
    final = json.dumps(final)

    return final, details

def Plagiarism_Checker(data=request()):
    """
    Function to call the main code and post result.

    Args:
        data (pd.DataFrame): data loaded from database.

    Returns:
        show_arr (json): contain final and details json from main code.
    """
    final, detail = main_code(data[0], text_list(data[0]))

    return final

print(Plagiarism_Checker())

#owo owo