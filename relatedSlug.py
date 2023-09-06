'''
模組: 輸入已有['combined_description']欄的DataFrame, 計算slugs之間相關性並另存至MySQL
使用方法:
>>> import relatedSlug
>>> relatedSlug.find(DataFrame)
'''

import re
# third-party module
import pandas as pd
import mysql.connector
from mysql.connector import errorcode
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
# custom module
import database


def find(df: pd.DataFrame):
    # 文字->TF-IDF
    tf = TfidfVectorizer(analyzer='word', ngram_range=(
        1, 3), min_df=0.05, max_df=0.5, stop_words='english')
    tfidf_matrix = tf.fit_transform(df['translated-description'])

    # 算相似
    cosine_similarities = linear_kernel(tfidf_matrix.toarray(), tfidf_matrix)

    # 結果儲存到sql
    db = database.connectToDatabase()
    mycursor = db.cursor()
    for i, row in df.iterrows():
        similar_indices = cosine_similarities[i].argsort()[:-100:-1]
        similar_items = [df['collection_slug'][j] for j in similar_indices]
        print(f'{row["collection_slug"]}:', [(cosine_similarities[i]
              [j], df['collection_slug'][j]) for j in similar_indices[:5]])
        results = similar_items[1:]
        # 上傳到sql
        relatedSlugToSql(row['collection_slug'], results, mycursor)
    db.commit()
    print('related slugs saved to MySQL: ', mycursor.rowcount)
    db.close()
    return


def relatedSlugToSql(slug, list, cursor):
    saveSql = 'UPDATE collection_details SET related_slugs = %s WHERE collection_slug = %s'
    output = str()
    for i in list:
        output += i
        output += '|'
    val = (output, slug)
    cursor.execute(saveSql, val)
    return
