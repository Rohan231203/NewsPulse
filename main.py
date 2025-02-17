from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
from model.model import recommend_articles, refresh_recommendations, register_read_article, clear_user_history, get_user_history

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allowing the frontend on localhost:3000
    allow_credentials=True,
    allow_methods=["*"],  # Allowing all methods
    allow_headers=["*"],  # Allowing all headers
)

class UserRequest(BaseModel):
    user_id: str
    user_read_articles: List[Dict[str, str]] = []
    page: int = 1

@app.post("/recommendations/")
async def get_recommendations(request: UserRequest):
    try:
        print(f"Received request for recommendations: {request}")
        recommendations = recommend_articles(request.user_id, request.user_read_articles, page=request.page)

        # ✅ Ensure recommendations is a dictionary and contains the "articles" key
        if isinstance(recommendations, dict) and "articles" in recommendations:
            # ✅ Ensure each recommended article includes both 'headline' and 'link'
            for article in recommendations["articles"]:
                if "headline" not in article or "link" not in article:
                    raise Exception("Missing required fields in recommendations")

            print(f"Recommendations fetched successfully: {recommendations}")
            return recommendations  # ✅ Directly return the dictionary
        else:
            raise Exception("Recommendations format is incorrect")
    except Exception as e:
        print(f"Error occurred while fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in fetching recommendations")



@app.post("/refresh")
async def refresh_user_recommendations(request: UserRequest):
    try:
        print(f"Received request to refresh recommendations for user {request.user_id}")
        
        # ✅ Ensure the user_id is valid
        if not request.user_id:
            raise ValueError("User ID is required")

        # ✅ Update the database to clear recommended articles with both "link" and "headline"
        refresh_recommendations(request.user_id)

        print(f"Recommendations refreshed successfully for user {request.user_id}")
        return {"message": "Recommendations refreshed successfully"}
    
    except ValueError as ve:
        print(f"Validation Error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        print(f"Error occurred while refreshing recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in refreshing recommendations")

@app.post("/mark_read/")
async def mark_article_as_read(request: UserRequest, article_link: str, article_headline: str):
    try:
        print(f"Received request to mark article as read: {article_link} with headline '{article_headline}' for user {request.user_id}")

        # ✅ Ensure all required fields are present
        if not request.user_id or not article_link or not article_headline:
            raise ValueError("User ID, article link, and article headline are required")

        # ✅ Register the article with both "link" and "headline"
        register_read_article(request.user_id, article_link, article_headline)

        print(f"Article '{article_headline}' marked as read for user {request.user_id}")
        return {"message": f"Article '{article_headline}' marked as read"}
    
    except ValueError as ve:
        print(f"Validation Error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        print(f"Error occurred while marking article as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in marking article as read")


@app.post("/clear_history")
async def clear_history(request: UserRequest):
    try:
        print(f"Received request to clear history for user {request.user_id}")

        # ✅ Ensure user_id is provided
        if not request.user_id:
            raise ValueError("User ID is required")

        result = clear_user_history(request.user_id)
        
        if result is None:
            return {"message": "User history was already empty"}

        print(f"History cleared for user {request.user_id}")
        return {"message": "User history cleared"}

    except ValueError as ve:
        print(f"Validation Error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        print(f"Error occurred while clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in clearing user history")


@app.post("/user_history")
async def fetch_user_history(request: UserRequest):
    try:
        print(f"Received request to fetch user history for user {request.user_id}")

        # ✅ Ensure user_id is provided
        if not request.user_id:
            raise ValueError("User ID is required")

        seen_articles = get_user_history(request.user_id)  # Fetch history

        if not seen_articles:
            return {"message": "No history found for the user", "history": []}

        print(f"User history fetched successfully: {seen_articles}")
        return {"history": seen_articles}  # ✅ Now includes both "link" and "headline"

    except ValueError as ve:
        print(f"Validation Error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        print(f"Error occurred while fetching user history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in fetching user history")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
