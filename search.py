from flask import Flask, request, jsonify, render_template
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores.redis import Redis
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
import openai
import redis
import os

openai.api_key = os.getenv('OPEN_API_KEY')
openai_api_key=os.getenv('OPEN_API_KEY')

embeddings = OpenAIEmbeddings(openai_api_key = openai_api_key)
redis_instance = redis.Redis(host = "127.0.0.1",port = "6379")

app = Flask(__name__)
path = "C:\\Users\\Khushi Budhraja\\news_scrap\\cleaned_file.csv"

@app.route('/search-news', methods=['GET','POST'])
def search_pdf():
    if request.method == 'POST':
        #search_query = request.form.get('query')
        search_query = request.form['query']
        results = perform_search(search_query)
        return render_template('index.html',result=results)
    else:
        return render_template('index.html')

def vectorize(index):
    loader = CSVLoader(path)
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    texts = text_splitter.split_documents(data)
    #create index for the first time
    Redis.from_documents(
        texts,
        embeddings,
        redis_url = "redis://127.0.0.1:6379",
        index_name = index
    )
    document_store = Redis.from_existing_index(
            index_name = index,
            redis_url = "redis://127.0.0.1:6379",
            embedding = OpenAIEmbeddings(openai_api_key = openai_api_key)
        )
    return document_store

def load_data(index):
    try:
        #to load if index alredy exist
        document_store = Redis.from_existing_index(
            index_name = index,
            redis_url = "redis://127.0.0.1:6379",
            embedding = OpenAIEmbeddings(openai_api_key = openai_api_key)
        )
        print(f"Data loaded from existing index {index}")
    except:
        #to insert if index is new
        document_store = vectorize(index)
        print(f"Data inserted for index {index}")
    return document_store

def perform_search(ques):
    data_store = load_data("cryptonews")

    #similarity search
    related_doc = data_store.similarity_search(ques,k=3)
    content = [ doc.page_content for doc in related_doc]
    knowledge = "\n".join(content)
    query =  "Based on the below knowledge answer this question." + ques + "\n" + knowledge

    chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = [
                {
                "role": "system",
                "content": "You are an incredible AI who can answer any question accurately, in an unique way."
                },
                {
                    "role": "user",
                    "content" : query
                }
            ]
        )

    ans = chat["choices"][0]["message"]["content"]
    return ans

if __name__ == '__main__':
    app.run(debug=True)
