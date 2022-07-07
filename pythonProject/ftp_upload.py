import ftplib
import os


def upload(filename, username, password, host):
    session = ftplib.FTP(host, username, password)
    file = open(filename, 'rb')
    session.cwd("www")
    try:
        session.mkd("anime_reports")
    except ftplib.error_perm as e:
        if not e.args[0].startswith('550'):
            raise
    session.cwd("anime_reports")
    session.storbinary(f'STOR {os.path.basename(filename)}', file)
    file.close()
    session.quit()
