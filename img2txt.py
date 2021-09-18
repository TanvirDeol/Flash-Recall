from csv import Sniffer
import cv2
from deskew import determine_skew
import numpy as np
import pandas as pd
import copy
from skimage import io
from skimage.transform import rotate
from skimage.color import rgb2gray
from skimage.util.dtype import img_as_bool
from PIL import Image
from google.cloud import vision,language_v1
import io
import base64

mask = None

#Detects highlighted text using yellow masks
def detect_highlight(img):
    global mask
    #cv2.imshow('pic',img)
    #cv2.waitKey(0)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    write_img(img,'hsv.png')
    lb_yellow = np.array([15,100,150])
    ub_yellow = np.array([75,200,255])
    tmp_mask = cv2.inRange(img,lb_yellow,ub_yellow)
    mask = copy.deepcopy(tmp_mask)
    #show(mask)
    write_img(mask,'mask.png')

# Splits text into sentences
def prep_sentences(text):
    sentences = []
    cur_sent = ''
    for word in text:
        cur_sent+= word+" "
        punc = ".;!?"
        for p in punc: 
            if p in word:
                sentences.append(cur_sent)
                cur_sent=''
    if len(cur_sent)>0:
        sentences.append(cur_sent)
    return sentences

# Generates a question given a sentence
def gen_questions(sent):
    en_client = language_v1.LanguageServiceClient()
    doc = {"content": sent, "type_": language_v1.Document.Type.PLAIN_TEXT, "language": "en"}
    en_resp = en_client.analyze_entities(request = {'document': doc, 'encoding_type': language_v1.EncodingType.UTF8})

    word_sal = {}

    #Define key terms
    mx_sal, word = 0,''
    for ent in en_resp.entities:
        word_sal[ent.name]=float(ent.salience*100)
        if ent.salience > mx_sal:
            mx_sal = ent.salience
            word = ent.name
    if(mx_sal*100>60.0):
        return "Define: "+word+"?" 

    #Fill in the blanks for noun and verbs
    syn_resp = en_client.analyze_syntax(request = {'document': doc, 'encoding_type': language_v1.EncodingType.UTF8})
    
    question =''
    blank = False
    for tk in syn_resp.tokens:
        word_type = tk.part_of_speech.tag
        parts = ["NOUN","VERB"]
        tblank = False
        if language_v1.PartOfSpeech.Tag(word_type).name in parts and word_sal.get(tk.text.content,0)>15:
            question+= "("+ language_v1.PartOfSpeech.Tag(word_type).name + ") "
            blank = True
            tblank = True
        if tblank == False:
            question += tk.text.content +" "

    if blank == True:
        return "Fill in the blanks: "+ question

    #True and False Question
    sentence = sent.split()
    for i in range(len(sentence)):
        sentence[i]= sentence[i].lower()
    words = ["is","have","was","can","had","shall","does","are","do","did"]
    for word in words:
        if word in sentence:
            sentence.remove(word)
            sentence.insert(0,word)
            sentence.append('?')
            tmpq = ''
            for s in sentence:
                tmpq += s+" "
            return "True or false: "+ tmpq  
    # In case none of these word
    return "No question availible"

#return list of words, indicating whether they are highlighted [word,highlight?]
def img_to_text(filename,hlight):
    global mask
    vis_client = vision.ImageAnnotatorClient()
    with io.open(filename, 'rb') as im:
        src_img = im.read()
    img = vision.Image(content=src_img)
    resp = vis_client.document_text_detection(image=img)
    out = ''

    text =[]
    for pg in resp.full_text_annotation.pages:
        for block in pg.blocks:
            for para in block.paragraphs:
                cnt=0
                for word in para.words:
                    w = ''
                    #bounding box for each word
                    mnx,mxx,mny,mxy =1e9,0,1e9,0
                    for box in word.bounding_box.vertices:
                        x,y = box.x,box.y
                        mnx,mxx,mny,mxy = min(mnx,x),max(mxx,x),min(mny,y),max(mxy,y)
                    # the word itself
                    for sym in word.symbols:
                        w+=sym.text
                        
                    #print(w)
                    wi,h = mxx-mnx,mxy-mny
                    #print(mnx,w,mny,h)
                    highlight = False
                    #checks if bounding box is highlighted
                    subimg = mask[mny:mxy,mnx:mxx]
                    try:
                        percent = ((np.sum(subimg==255))/(wi*h))*100
                    except:
                        print("An exception occurred")
                    highlight = False
                    
                    if percent>=30:
                        highlight = True
                    
                    #print(w,percent)
                    #show(subimg)
                    if (hlight == True and highlight == True) or (hlight == False):
                        text.append(w)
                        if word in [",",".","!","?",";",":"]:
                            out+=w
                        else: out += " "+w

    #print(out)
    return text
# Calls preprocessing methods, image to text methods and question methods
def process_img(filename,hlight):
    img = cv2.imread(filename)
    detect_highlight(img)
    text = img_to_text(filename,hlight)
    sentences = prep_sentences(text)
    q = []
    a = []
    for sent in sentences:
        question = gen_questions(sent)
        if question== "No question availible":
            continue
        anss =''
        #for i in sent[0]: anss+=i+" "
        question[0].upper()
        #anss[0].upper()
        q.append(question)
        a.append(sent)
    return [q,a]

def show(img):
    cv2.namedWindow("pic")        
    cv2.moveWindow("pic", 0,0) 
    cv2.imshow("pic", img)
    cv2.waitKey(0)

# write image to dir
def write_img(img,filename):
    cv2.imwrite('C:\\Users\\tanvi\\Desktop\\FlashRecall\\'+filename, img)

# write text file to dir
def write_txt(text,filename):
    file = open(filename+".txt", "w")
    file.write(text)
    file.close()

#Caller function to convert an image into [questions,answers]
def conv_img(filename,hlight):
    dir = '.\\uploads\\images\\'+filename
    #dir = '.\\'+filename
    print(dir)
    [q,a] = process_img(dir,hlight)
    return [q,a]


'''[q,a] = conv_img("imgh2.jpeg",True)
print("")
for i in range(len(q)):
    print(q[i])
    print(a[i])
    print("\n")'''