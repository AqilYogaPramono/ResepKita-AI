from fastapi import FastAPI, HTTPException, Form, Depends
from pydantic import BaseModel
from rapidfuzz import process
import mysql.connector
from typing import List
from fastapi.staticfiles import StaticFiles
import os
import jwt
from jwt import PyJWTError
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
app.mount("/static", StaticFiles(directory="Public"), name="static")

SECRET_KEY = os.getenv("JWT_SECRET", "iamsimpkita")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "db_resepkita"
}

class SearchRequest(BaseModel):
    sentence: str

class TokenData(BaseModel):
    user_id: int = None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except PyJWTError:
        raise credentials_exception

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise HTTPException(500, f"Database connection error: {err}")

def extract_ingredients(text: str, threshold: int = 78) -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM ingredients")
    dictionary = [row[0].lower() for row in cursor]
    cursor.close()
    conn.close()

    words = text.lower().split()
    matched = []
    for word in words:
        match, score, _ = process.extractOne(word, dictionary)
        if score >= threshold:
            matched.append(match)
    return list(set(matched))

def find_recipes_by_ingredients(ingredients: List[str], current_user_id: int) -> List[dict]:
    if not ingredients:
        return []
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    placeholder = ",".join(["%s"] * len(ingredients))
    sql = f"""SELECT r.id, r.title, u.nickname, (SELECT rp.photo_url FROM recipe_photos rp WHERE rp.recipe_id = r.id LIMIT 1) AS recipe_photo,COUNT(t.id) AS testimonial_count FROM recipes r JOIN ingredients ing ON r.id = ing.recipe_id LEFT JOIN recipe_photos rp ON r.id = rp.recipe_id LEFT JOIN users u ON r.user_id = u.id LEFT JOIN testimonials t ON r.id = t.recipe_id WHERE ing.name IN ({placeholder}) AND r.user_id != %s GROUP BY r.id ORDER BY RAND()"""
    params = ingredients + [current_user_id]
    cursor.execute(sql, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

@app.post("/API/user/searching_recipe_ai")
def search_recipes_ai(sentence: str = Form(...), current_user_id: int = Depends(get_current_user)):
    recognized = extract_ingredients(sentence)
    if not recognized:
        return {
            "message": "Mohon Maaf, bahan yang anda miliki belum memiliki resep :(",
            "image_url": "/static/Fuuka.png"
            }
    recipes = find_recipes_by_ingredients(recognized, current_user_id)
    return {
        "recognized_ingredients": recognized,
        "recipes": recipes
    }
