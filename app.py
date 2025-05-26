from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from rapidfuzz import process
import mysql.connector
from typing import List
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="Public"), name="static")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "db_resepkita"
}

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

def find_recipes_by_ingredients(ingredients: List[str], limit: int = 3) -> List[dict]:
    if not ingredients:
        return []
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    placeholder = ",".join(["%s"] * len(ingredients))
    sql = f"""SELECT r.id, r.title AS recipe_title, u.nickname AS author, MIN(rp.photo_url) AS recipe_photo, COUNT(t.id) AS testimonial_count FROM recipes r JOIN ingredients ing ON r.id = ing.recipe_id LEFT JOIN recipe_photos rp ON r.id = rp.recipe_id LEFT JOIN users u ON r.user_id = u.id LEFT JOIN testimonials t ON r.id = t.recipe_id WHERE ing.name IN ({placeholder}) GROUP BY r.id ORDER BY RAND() LIMIT %s"""
    cursor.execute(sql, ingredients + [limit])
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

@app.post("/API/user/searching_recipe_ai")
def search_recipes_ai(sentence: str = Form(...)):
    recognized = extract_ingredients(sentence)
    if not recognized:
        return {
            "message": "Mohon Maaf, bahan yang anda miliki belum memiliki resep :(",
            "image_url": "/static/Fuuka.png"
            }
    recipes = find_recipes_by_ingredients(recognized)
    return {
        "recognized_ingredients": recognized,
        "recipes": recipes
    }
