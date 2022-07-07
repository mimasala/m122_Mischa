import datetime
import json
import requests
import shutil
from PIL import Image
import os
import glob
from jinja2 import Environment, FileSystemLoader


current_directory = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(current_directory))
templates = glob.glob('*.j2')


# format date and time
def currentDateTime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def render_template(filename, myJSONObj):
    return env.get_template(filename).render(
        title=
        myJSONObj["title"]["romaji"]+" - "+myJSONObj["title"]["english"]+" - "+myJSONObj["title"]["native"],
        # ["romaji"] if myJSONObj["title"]["romaji"] != "None" else
        # myJSONObj["title"]["english"],
        description=myJSONObj["description"],
        coverImage=myJSONObj["coverImage"]["medium"],
        bannerImage=myJSONObj["bannerImage"],
        genres=myJSONObj["genres"],
        character_cards=character_to_html("template/CharacterCard.j2", myJSONObj),
        background_color=myJSONObj["coverImage"]["color"],
        current_date=str(currentDateTime()),
        anime_id=myJSONObj["id"],
        banner_has_overlay="block" if myJSONObj["bannerImage"] != "None" else "none",
    )


# image downloader (not used)
def download_images(myJSONObj):
    if myJSONObj["bannerImage"] != "None":
        download_image(myJSONObj["bannerImage"], "banner")
    if myJSONObj["coverImage"]["medium"] != "None":
        download_image(myJSONObj["coverImage"]["medium"], "cover")
    for character in myJSONObj["characters"]["edges"]:
        if character["node"]["image"]["medium"] != "None":
            download_image(character["node"]["image"]["medium"], "character")


# image downloader (not used)
def download_image(url, img_type):

    if img_type == "banner":
        image_path = "runtimeFiles/banner.jpg"
    elif img_type == "cover":
        image_path = "runtimeFiles/cover.jpg"
    elif img_type == "character":
        image_path = "runtimeFiles/" + str(url.split("/")[-1])
    else:
        return

    if not os.path.exists(image_path):
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(image_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            if img_type == "character":
                image = Image.open(image_path)
                image.thumbnail((200, 200), Image.ANTIALIAS)
                image.save(image_path)
            return True
        else:
            return False
    else:
        return True


# main report generator
def build_report(response, file):
    response = json_values_to_string(response)
    # download_images(response)
    return render_template(file, response)


# makes sure that all values are strings
def json_values_to_string(myJSONObj):
    return json.loads(json.dumps(myJSONObj).replace("null", '"None"'))


# main character card generator
def character_to_html(filename, myJSONObj):
    html = ""
    for character in myJSONObj["characters"]["edges"]:
        html += render_character_template(filename, character["node"])
    return html


# replace character card template with character data
def render_character_template(filename, myJSONObj):
    return env.get_template(filename).render(
        character_id=myJSONObj["id"],
        character_name=myJSONObj["name"]["full"],
        character_image=myJSONObj["image"]["medium"],
        character_description=myJSONObj["description"],
        character_age=myJSONObj["age"],
    )
