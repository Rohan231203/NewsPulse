import pandas as pd
import numpy as np
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from pymongo import MongoClient, errors
import logging
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Connection
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["news_article_recommendation_db"]
    history_collection = db["user_history"]
    logging.info("✅ Successfully connected to MongoDB")
except errors.ServerSelectionTimeoutError as e:
    logging.error(f"❌ MongoDB connection error: {e}")
    db = None
except Exception as e:
    logging.exception(f"❌ A MongoDB error occurred: {e}")
    db = None

# Load articles dataset
json_file_path = "C:/Users/HP/Desktop/news_article_recommendation/News_Category_Dataset_v3.json"
model_file_path = "tfidf_knn_model.pkl"
vectorizer_file_path = "tfidf_vectorizer.pkl"

articles = []
with open(json_file_path, "r", encoding="utf-8") as file:
    for line in file:
        articles.append(json.loads(line.strip()))

logging.info(f"✅ Successfully loaded {len(articles)} articles")
data = pd.DataFrame(articles)

# Check required columns
expected_columns = {"headline", "short_description", "category", "link"}
if not expected_columns.issubset(data.columns):
    logging.error("❌ Dataset is missing required columns!")
    exit()

# Load or train the model
if os.path.exists(model_file_path) and os.path.exists(vectorizer_file_path):
    logging.info("🔄 Loading trained model...")
    try:
        with open(vectorizer_file_path, "rb") as file:
            vectorizer = pickle.load(file)
        with open(model_file_path, "rb") as file:
            nn_model = pickle.load(file)
    except Exception as e:
        logging.error(f"❌ Error loading the trained model: {e}")
        exit()
else:
    logging.info("🆕 Training new model...")
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(data["headline"] + " " + data["short_description"])

    nn_model = NearestNeighbors(metric="cosine", algorithm="brute")
    nn_model.fit(tfidf_matrix)

    try:
        with open(vectorizer_file_path, "wb") as file:
            pickle.dump(vectorizer, file)
        with open(model_file_path, "wb") as file:
            pickle.dump(nn_model, file)
    except Exception as e:
        logging.error(f"❌ Error saving the model: {e}")
        exit()
    logging.info("✅ Model training completed and saved.")

# Fetch user history
def get_user_history(user_id):
    if db is None:
        return set(), set()
    
    try:
        user_data = history_collection.find_one(
            {"user_id": user_id}, 
            {"_id": 0, "seen_articles": 1, "recommended_articles": 1}
        )

        seen_articles = set()
        recommended_articles = set()

        if user_data:
            seen_articles = {(article['link'], article.get('headline', 'Untitled')) for article in user_data.get("seen_articles", [])}
            recommended_articles = {(article['link'], article.get('headline', 'Untitled')) for article in user_data.get("recommended_articles", [])}

        return seen_articles, recommended_articles
    except Exception as e:
        logging.error(f"❌ Error fetching user history: {e}")
        return set(), set()

def update_user_history(user_id, seen_articles, recommended_articles):
    if db is None:
        return
    
    try:
        history_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "seen_articles": [{"link": link, "headline": headline} for link, headline in seen_articles],
                    "recommended_articles": [{"link": link, "headline": headline} for link, headline in recommended_articles]
                }
            },
            upsert=True
        )
    except Exception as e:
        logging.error(f"❌ Error updating user history: {e}")


def recommend_articles(user_id, user_read_articles, num_recommendations=5, page=1):
    logging.debug(f"Starting recommendation process for user_id={user_id}")
    print(f"Received: user_id={user_id}, user_read_articles={user_read_articles}, page={page}")

    if data.empty:
        logging.warning("⚠️ No articles found!")
        return {"error": "No articles available"}

    # Retrieve user history
    seen_articles, recommended_articles = get_user_history(user_id)
    read_links = set(user_read_articles)
    seen_articles.update(read_links)

    user_read_indices = data[data["link"].isin(read_links)].index.tolist()

    if not user_read_indices:
        available_articles = data[~data["link"].isin(seen_articles)]
    else:
        user_profile_vector = np.asarray(vectorizer.transform(
            data.loc[user_read_indices, "headline"] + " " + data.loc[user_read_indices, "short_description"]
        ).mean(axis=0)).reshape(1, -1)

        distances, indices = nn_model.kneighbors(user_profile_vector, n_neighbors=len(data))
        recommended_indices = [idx for idx in indices.flatten() if data.iloc[idx]["link"] not in seen_articles]

        available_articles = data.iloc[recommended_indices]

    total_articles = len(available_articles)

    if total_articles == 0:
        return {"message": "No new recommendations available", "articles": []}

    # Pagination logic
    total_pages = (total_articles // num_recommendations) + (1 if total_articles % num_recommendations else 0)
    start_idx = (page - 1) * num_recommendations
    end_idx = start_idx + num_recommendations

    paginated_articles = available_articles.iloc[start_idx:end_idx]

    # Store both `link` and `headline`
    recommended_list = paginated_articles[["headline", "category", "short_description", "link"]].to_dict(orient="records")

    if not recommended_list:
        return {"message": "No more recommendations on this page", "articles": []}

    # Convert to set of tuples (link, headline) for updating history
    seen_articles.update((article["link"], article["headline"]) for article in recommended_list)

    update_user_history(user_id, seen_articles, [(article["link"], article["headline"]) for article in recommended_list])

    response = {
        "total_articles": total_articles,
        "total_pages": total_pages,
        "current_page": page,
        "articles": recommended_list
    }

    logging.debug(f"Returning recommendations: {json.dumps(response, indent=4)}")  # Log output
    return response



def refresh_recommendations(user_id):
    if db is None:
        return
    
    try:
        history_collection.update_one(
            {"user_id": user_id},
            {"$set": {"recommended_articles": []}},
            upsert=True
        )
        logging.info(f"✅ Recommendations refreshed for user_id={user_id}")
    except Exception as e:
        logging.error(f"❌ Error refreshing recommendations: {e}")


def register_read_article(user_id, article_link, article_headline):
    if db is None:
        return
    
    try:
        history_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"seen_articles": {"link": article_link, "headline": article_headline}}},
            upsert=True
        )
        logging.info(f"✅ Article marked as read: {article_link} ({article_headline}) for user_id={user_id}")
    except Exception as e:
        logging.error(f"❌ Error registering read article for user_id={user_id}: {e}")


# Clear user history
def clear_user_history(user_id):
    if db is None:
        return  # If db is not available, do nothing
    
    try:
        history_collection.update_one(
            {"user_id": user_id},
            {"$set": {"seen_articles": []}},  # Clears seen articles
            upsert=True  # Ensures the document exists
        )
        logging.info(f"✅ User history cleared for user_id={user_id}")
    except Exception as e:
        pass  # Silently ignore errors

