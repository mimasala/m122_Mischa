import datetime
import os
import random

import dotenv
import requests as requests
from dotenv import load_dotenv, dotenv_values
import logging
import pydf

import build_report
import pdf_report


def currentDateTime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


logging.basicConfig(filename="request.log", level=logging.INFO)
config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
}
logging.info("Starting... "+currentDateTime())


def clear_temp_files():
    for file in os.listdir(config["temp_dir"]):
        file_path = os.path.join(config["temp_dir"], file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logging.error(f"{currentDateTime()}: {e}")


def set_and_get_current_id(lastId: int):
    load_dotenv(".env.secret")
    dotenv.set_key(".env.secret", "LAST_ID", str(lastId))
    return os.environ["LAST_ID"]


def validate_response(request):
    if request.status_code == 200:
        return True
    else:
        return False


def get_response(randomInt: int):
    query = '''
    query ($random: Int) {
      Page(page: $random, perPage: 1) {
        pageInfo {
            total
        }
        media(type: ANIME, isAdult: false, status_not: NOT_YET_RELEASED) {
          id,
          title {
              romaji,
              english,
              native,
          }
          bannerImage,
          coverImage {
              medium,
              color,
          },
          genres,
          description,
          characters{
          edges{
            node{
              id,
              name{
                full
              },
              image{
                medium
                },
              description(asHtml: true),
              age,
              }
            }
          },
        }
      }
    }
    '''

    if randomInt == -1:
        request = requests.post(config["url"], json={'query': query})
    else:
        request = requests.post(config["url"], json={'query': query, 'variables': {'random': randomInt}})

    if validate_response(request):
        set_and_get_current_id(request.json()["data"]["Page"]["media"][0]["id"])
        return request.json()
    else:
        logging.error(f"{currentDateTime()}: {request.status_code}: {request.json()['errors'][0]['message']}")
        return False


def get_random_anime():
    max_random_int = get_response(-1)
    if not max_random_int:
        return
    max_random_int = max_random_int["data"]["Page"]["pageInfo"]["total"]
    random_int = random.randint(1, max_random_int)
    logging.info(f"{currentDateTime()}: anime request ID: {random_int}")
    return get_response(random_int)["data"]["Page"]["media"][0]


clear_temp_files()

random_anime = get_random_anime()

report = build_report.build_report(random_anime, "template/report_template.html")
simpleReport = build_report.build_report(random_anime, "template/simple_report_template.html")
pdf_report.generate_report_pdf(simpleReport, "simple_report.pdf")
print(report)

logging.info("Created report HTML"+currentDateTime())


logging.info("Finished... "+currentDateTime())
