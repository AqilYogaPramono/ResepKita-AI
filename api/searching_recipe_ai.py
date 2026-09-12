from fastapi import APIRouter, Form, Depends
from core.jwt import get_current_user
from services.recipe_service import extract_ingredients, find_recipes_by_ingredients

router = APIRouter(tags=["Recipes AI"])

@router.post("/API/user/searching_recipe_ai")
async def search_recipes_ai(
    sentence: str = Form(...), 
    current_user_id: int = Depends(get_current_user)
):
    recognized = await extract_ingredients(sentence)
    if not recognized:
        return {
            "message": "Mohon Maaf, bahan yang anda miliki belum memiliki resep :(", 
            "image_url": "/static/Fuuka.png"
        }
    recipes = await find_recipes_by_ingredients(recognized, current_user_id)
    return {"recognized_ingredients": recognized, "recipes": recipes}
