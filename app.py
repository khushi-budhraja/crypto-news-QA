import os
import logging
from flask import Flask, request, render_template
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores.redis import Redis
from langchain.embeddings import OpenAIEmbeddings
import openai
import redis
from scrap import main


def configure_app():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logging.error("OPENAI_API_KEY not found in environment variables.")
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    openai.api_key = openai_api_key
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    return embeddings


path = "./clean.csv"


def check_file(path):
    if not os.path.isfile(path):
        main(path)


def vectorize(index, embeddings):
    loader = CSVLoader(path)
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    texts = text_splitter.split_documents(data)
    Redis.from_documents(
        texts,
        embeddings,
        redis_url=os.getenv("REDIS_URL"),
        password=os.getenv("REDIS_PASSWORD"),
        index_name=index,
    )
    document_store = Redis.from_existing_index(
        index_name=index,
        redis_url=os.getenv("REDIS_URL"),
        password=os.getenv("REDIS_PASSWORD"),
        embedding=embeddings,
    )
    return document_store


def load_data(index, embeddings):
    print("Loading Index")
    try:
        document_store = Redis.from_existing_index(
            index_name=index,
            redis_url=os.getenv("REDIS_URL"),
            password=os.getenv("REDIS_PASSWORD"),
            embedding=embeddings,
        )
        print(f"Data loaded from existing index {index}")
    except:
        document_store = vectorize(index, embeddings)
        print(f"Data inserted for index {index}")
    return document_store


def perform_search(ques, data_store):
    data_store = data_store
    related_doc = data_store.similarity_search(ques, k=3)
    content = [doc.page_content for doc in related_doc]
    knowledge = "\n".join(content)
    query = (
        "Based on the below knowledge answer this question." + ques + "\n" + knowledge
    )

    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an incredible AI who can answer any question accurately, in an unique way.",
            },
            {"role": "user", "content": query},
        ],
    )

    ans = chat["choices"][0]["message"]["content"]
    return ans


def create_app():
    app = Flask(__name__)
    check_file(path)
    embeddings = configure_app()
    data_store = load_data("cryptonews", embeddings)
    return app, path, embeddings, data_store


app, path, embeddings,  data_store = create_app()


@app.route("/", methods=["GET", "POST"])
def search_pdf():
    if request.method == "POST":
        search_query = request.form["query"]
        results = perform_search(search_query, data_store)
        return render_template("index.html", result=results)
    else:
        return render_template("index.html")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)


