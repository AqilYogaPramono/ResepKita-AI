from typing import List
import asyncio
import aiomysql
from rapidfuzz import process
from database.db import get_db

def _fuzzy_match(words: List[str], dictionary: List[str], threshold: int) -> List[str]:
    matched = []
    for word in words:
        match, score, _ = process.extractOne(word, dictionary)
        if score >= threshold:
            matched.append(match)
    return list(set(matched))

async def extract_ingredients(text: str, threshold: int = 78) -> List[str]:
    async with get_db() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT DISTINCT name FROM ingredients")
            rows = await cursor.fetchall()
            dictionary = [row[0].lower() for row in rows]

    if not dictionary:
        return []

    words = text.lower().split()
    matched = await asyncio.to_thread(_fuzzy_match, words, dictionary, threshold)
    return matched

async def find_recipes_by_ingredients(ingredients: List[str], current_user_id: int) -> List[dict]:
    if not ingredients:
        return []

    async with get_db() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            placeholder = ",".join(["%s"] * len(ingredients))
            sql = f"""SELECT r.id, r.title, r.user_id AS creator_id, u.nickname, u.photo_profile, (SELECT rp.photo_url FROM recipe_photos rp WHERE rp.recipe_id = r.id LIMIT 1) AS recipe_photo, COUNT(t.id) AS testimonial_count, CASE WHEN f.user_id IS NOT NULL THEN 'TRUE' ELSE 'FALSE' END AS is_saved FROM recipes r JOIN ingredients ing ON r.id = ing.recipe_id LEFT JOIN users u ON r.user_id = u.id LEFT JOIN testimonials t ON r.id = t.recipe_id LEFT JOIN favorites f ON r.id = f.recipe_id AND f.user_id = %s WHERE ing.name IN ({placeholder}) AND r.user_id != %s AND r.status = 'approved' AND r.id NOT IN (SELECT recipe_id FROM favorites WHERE user_id = %s) GROUP BY r.id ORDER BY RAND()"""
            params = [current_user_id] + ingredients + [current_user_id, current_user_id]
            await cursor.execute(sql, params)
            results = await cursor.fetchall()

    return results
