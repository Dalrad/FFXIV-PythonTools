from pyautogui import *
import pyautogui
import time
import keyboard
import numpy as np
import random
import win32api, win32con
import requests
import json

def callItemSearchAPI(item):
    url = "https://xivapi.com/search?string=" + item
    headers = {"User-Agent": "&lt;User-Agent&gt;"}
    body = {"indexes": "Recipe"}

    try:
        response = requests.get(url, headers=headers, json=body)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print("Error:", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None


def callRecipeAPI(itemRecipeUrl):
    url = "https://xivapi.com" + itemRecipeUrl
    headers = {"User-Agent": "&lt;User-Agent&gt;"}

    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print("Error:", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None


def recursiveItemRecipeSearch(itemName):
    results = callItemSearchAPI(itemName)
    if len(results.get("Results")) == 0:
        print("This item had no results")
        return None

    if "Url" not in results.get("Results")[0]:
        print("This recipe had a missing URL")
        return None

    return recursiveRecipeLookup(recipeURL=results.get("Results")[0].get("Url"))


def recursiveRecipeLookup(dataset=dict(), recipeURL=""):
    if recipeURL == "":
        return dataset

    recipeApiResult = callRecipeAPI(recipeURL)
    print(recipeApiResult.get("Name_en"))
    for i in range(0, 8):
        if recipeApiResult.get("AmountIngredient" + str(i)) != 0:
            recipeName = recipeApiResult.get("ItemIngredient" + str(i)).get("Name")

            if recipeName not in dataset:
                dataset[recipeName] = {
                    "name": recipeApiResult.get("ItemIngredient" + str(i)).get(
                        "Name_en"
                    ),
                    "price": 0,
                    "id": recipeApiResult.get("ItemIngredient" + str(i)).get("ID"),
                    "quantity": recipeApiResult.get("AmountIngredient" + str(i)),
                    "childIngredientsDict": dict(),
                }
            else:
                dataset[recipeName] = {
                    "name": recipeName,
                    "price": dataset.get(recipeName).get("price"),
                    "id": dataset.get(recipeName).get("id"),
                    "quantity": dataset.get(recipeName).get("quantity"),
                    "childIngredients": dataset.get(recipeName).get("childIngredients"),
                }

            if recipeApiResult.get("ItemIngredientRecipe" + str(i)) is not None:
                for item in recipeApiResult.get("ItemIngredientRecipe" + str(i)):
                    dataset[recipeName]["childIngredientsDict"] = recursiveRecipeLookup(
                        dataset=dataset[recipeName]["childIngredientsDict"],
                        recipeURL=item.get("Url"),
                    )

    return dataset


def callCurrentPriceUniversalis(itemRecipeArray):
    url = "https://universalis.app/api/v2/aggregated/North-America/" + itemRecipeArray
    try:
        response = requests.get(url)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print("Error:", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

shoppingList = recursiveItemRecipeSearch("Facet Turban of Scouting")

itemIdArray = ""
for item in shoppingList:

    itemIdArray += str(shoppingList[item]["id"]) + ","
    # Bundle items by minimum quantities (maybe)
    # 20req/s limit

print(itemIdArray[:-1])
