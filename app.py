from fastapi import FastAPI, HTTPException, Form, Depends
from pydantic import BaseModel
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
import os
import jwt
from jwt import PyJWTError
from dotenv import load_dotenv
from rapidfuzz import process
import uvicorn
import aiomysql

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="Public"), name="static")

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

async def get_connection():
    try:
        return await aiomysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
        )
    except aiomysql.MySQLError as err:
        raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class TokenData(BaseModel):
    user_id: int = None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except PyJWTError:
        raise credentials_exception

async def extract_ingredients(text: str, threshold: int = 78) -> List[str]:
    conn = await get_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT DISTINCT name FROM ingredients")
        rows = await cursor.fetchall()
        dictionary = [row[0].lower() for row in rows]
    conn.close()

    words = text.lower().split()
    matched = []
    for word in words:
        match, score, _ = process.extractOne(word, dictionary)
        if score >= threshold:
            matched.append(match)
    return list(set(matched))

async def find_recipes_by_ingredients(ingredients: List[str], current_user_id: int) -> List[dict]:
    if not ingredients:
        return []

    conn = await get_connection()
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        placeholder = ",".join(["%s"] * len(ingredients))
        sql = f"""SELECT r.id, r.title, r.user_id AS creator_id, u.nickname, u.photo_profile, (SELECT rp.photo_url FROM recipe_photos rp WHERE rp.recipe_id = r.id LIMIT 1) AS recipe_photo, COUNT(t.id) AS testimonial_count, CASE WHEN f.user_id IS NOT NULL THEN 'TRUE' ELSE 'FALSE' END AS is_saved FROM recipes r JOIN ingredients ing ON r.id = ing.recipe_id LEFT JOIN users u ON r.user_id = u.id LEFT JOIN testimonials t ON r.id = t.recipe_id LEFT JOIN favorites f ON r.id = f.recipe_id AND f.user_id = %s WHERE ing.name IN ({placeholder}) AND r.user_id != %s AND r.status = 'approved' AND r.id NOT IN (SELECT recipe_id FROM favorites WHERE user_id = %s) GROUP BY r.id ORDER BY RAND()"""
        params = [current_user_id] + ingredients + [current_user_id, current_user_id]
        await cursor.execute(sql, params)
        results = await cursor.fetchall()
    conn.close()
    return results

@app.post("/API/user/searching_recipe_ai")
async def search_recipes_ai(sentence: str = Form(...), current_user_id: int = Depends(get_current_user)):
    recognized = await extract_ingredients(sentence)
    if not recognized:
        return {"message": "Mohon Maaf, bahan yang anda miliki belum memiliki resep :(", "image_url": "/static/Fuuka.png"}
    recipes = await find_recipes_by_ingredients(recognized, current_user_id)
    return {"recognized_ingredients": recognized, "recipes": recipes}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)