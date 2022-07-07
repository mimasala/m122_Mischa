import base64
import datetime
import os
import random

import dotenv
from dotenv import load_dotenv, dotenv_values
import logging
from sendgrid import FileContent, FileName, FileType, Disposition

import build_report
import email_sender
import ftp_upload
import pdf_report
from sendgrid.helpers.mail import Attachment
import yaml
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


def currentDateTime(isfile: bool = False):
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") \
        if not isfile \
        else datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# initialize config and environment variables and project files
# load environment variables
logging.basicConfig(filename="request.log", level=logging.INFO)
env = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
}
logging.info("Starting... " + currentDateTime())

# load config file
with open(env["config"]) as file:
    proj_config = yaml.load(file, Loader=yaml.FullLoader)
    file.close()

# get sendgrid API key
sendgrid_api_key = env["SENDGRID_API_KEY"] if env["SENDGRID_API_KEY"] is not None \
    else proj_config['email']['sendgrid']['api_key'] if proj_config['email']['sendgrid']['api_key'] is not None \
    else None

# check if sendgrid api key is set
if sendgrid_api_key is None:
    logging.error("Sendgrid API key not found")
    exit(1)
logging.info("Sendgrid API key found")

# delete runtime files
for f in os.listdir(proj_config['runtime']['dir']):
    file_path = os.path.join(proj_config['runtime']['dir'], f)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        logging.error(f"{currentDateTime()}: {e}")


# end initialize config and environment variables and project files


def set_and_get_current_id(lastId: int):
    load_dotenv(".env.shared")
    dotenv.set_key(".env.shared", "LAST_ID", str(lastId))
    return os.environ["LAST_ID"]


def load_query(path):
    with open(path) as f:
        data = f.read()
        f.close()
    return gql(data)


# send actual request
def get_response(randomInt: int):
    query = load_query("graphql/query.graphql")
    try:
        transport = AIOHTTPTransport(url=proj_config['api']['url'])
        client = Client(transport=transport)
        response = client.execute(
            query,
            variable_values={"random": randomInt if randomInt != -1 else None}
        )
        return response
    except Exception as excep:
        logging.error(f"{currentDateTime()}: {excep}")
        print(excep)
        return False


def get_random_anime():
    max_random_int = get_response(-1)
    if not max_random_int:
        return
    max_random_int = max_random_int["Page"]["pageInfo"]["total"]
    random_int = random.randint(1, max_random_int)
    logging.info(f"{currentDateTime()}: anime request ID: {random_int}")
    return get_response(random_int)["Page"]["media"][0]


# filename to attachment object
def create_attachment(fileName):
    with open(fileName, 'rb') as f:
        file_data = f.read()
        f.close()
    encoded_file = base64.b64encode(file_data).decode()
    return Attachment(
        FileContent(encoded_file),
        FileName(fileName),
        FileType('application/pdf'),
        Disposition('attachment')
    )


# execution starts here
# get random anime json
random_anime = get_random_anime()

# generate report HTML string
report = build_report.build_report(random_anime, proj_config['files']['templates']['reportTemplate'])

# generate report HTML string for PDF
simpleReport = build_report.build_report(random_anime, proj_config['files']['templates']['simpleReportTemplate'])

# generate PDF file for email
pdf_report_fileName = f"{proj_config['runtime']['dir']}{currentDateTime(True)}_simple_report.pdf" \
    if proj_config["files"]["pdf"]["name"] is None else proj_config["files"]["pdf"]["name"]

# generate PDF file for PDF
pdf_report.generate_report_pdf(simpleReport, pdf_report_fileName)

logging.info("Created report HTML" + currentDateTime())

# create Attachment for email and send email
email_sender.send_email(
    proj_config['email']['to'] if proj_config['email']["to"] is not None else env['email_to'],
    "API Report" if proj_config['email']['subject'] is None else proj_config['email']['subject'],
    report,
    sendgrid_api_key,
    [create_attachment(pdf_report_fileName)]
)

ftp_upload.upload(
    pdf_report_fileName,
    proj_config['ftp']['username'],
    proj_config['ftp']['password'],
    proj_config['ftp']['host']
)

logging.info("Finished... " + currentDateTime())
