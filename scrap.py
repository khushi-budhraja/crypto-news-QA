from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime
import time

def extract_url(lst_soup):
    url_soup = lst_soup.find("h3",class_="media-heading")
    a_tag = url_soup.find('a')
    url = a_tag['href']
    return url

def exctract_time(lst_soup):
    day_time = []
    time_soup = lst_soup.find("div",class_="entry-meta")
    span_tag = time_soup.find_all('span')
    for i in span_tag:
        day_time.append(i.text)
    return day_time

def check_range(day_time):
    date_string = " ".join(day_time[:2])
    date_format = "%b %d, %Y %H:%M"
    date_object = datetime.strptime(date_string, date_format)
    news_timestamp = int(date_object.timestamp())
    current_timestamp = int(time.time())
    if (current_timestamp - news_timestamp) < 24*60*60*15:
        return True
    else:
        return False
    
details = []
def exctract_data(url):
    response = requests.get(url)
    soup1 = BeautifulSoup(response.content,"html.parser")

    #TITLE
    title = soup1.find('span',class_="breadcrumb_last")

    #CONTENT
    data = []
    content = soup1.find("div",class_="coincodex-content")
    para = content.find_all(['p','h2'])  
    for i in para:
        data.append(i.text)

    #TAGS
    tag = soup1.find('div',class_="entry-tags")
    tags = []
    if tag:
        a_tag = tag.find_all('a')
        for i in a_tag:
            tags.append(i.text)

    #TIME
    time = soup1.find('span',class_ = "last-modified-timestamp")
    day_time = time.text
    day_time_list = day_time.split("@")
    
    #CATEGORY
    category_line = soup1.find("header",class_="entry-header")
    div_tag = category_line.find('div')
    span_tag = div_tag.find('span')
    category = span_tag.text.split(" » ")

    details.append([title.text, "".join(data), ",".join(tags), day_time_list[0], day_time_list[1], category[1]])

def main(file_name):
    page = 1
    flag = True
    urls = []
    while flag:
        res = requests.get(f"https://cryptopotato.com/category/crypto-news/page/{page}/")
        soup = BeautifulSoup(res.content,"html.parser")
        lst = soup.find_all("div",class_="media-body")
        for i in lst:
            day_time = exctract_time(i)
            range = check_range(day_time)
            if range:
                print(f"Page : {page}")
                url = extract_url(i)
                urls.append(url)
                exctract_data(url)
            else:
                print(f"Last page = {page}")
                flag = False
                break
        if page == 5:
            break
        page+=1

    # Create a DataFrame and clean the data
    df = pd.DataFrame(details, columns=["Title","Content","Tags","Day","Time", "Category"])
    df = df.replace(r'[^\w\s]+', '', regex=True)

    # Save the cleaned data
    df.to_csv(file_name, index=False)

if __name__ == "__main__":
    main("clean.csv")