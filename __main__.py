import os
from argparse import ArgumentParser

import requests
from clint.textui.progress import Bar as ProgressBar
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


def create_callback(encoder):
    encoder_len = encoder.len
    bar = ProgressBar(expected_size=encoder_len, filled_char="=")

    def callback(monitor):
        bar.show(monitor.bytes_read)

    return callback


class Config:
    def __init__(self) -> None:
        self.token = ""


class Uptobox:
    def __init__(self) -> None:
        self.api_url = "uptobox.com"

        self.endpoints = {
            "upload": f"https://{self.api_url}/api/upload",
            "transco": f"https://{self.api_url}/api/upload/transcode/id?file_code=",
        }

        self.config = Config()

        self.session = requests.Session()

    def get_best_server(self):
        account = {"token": self.config.token}
        return self.session.get(self.endpoints["upload"], params=account).json()

    def upload(self, best_server, input):
        fields = os.path.basename(input), open(input, "rb")
        data = MultipartEncoder({"files": fields})

        callback = create_callback(data)
        monitor = MultipartEncoderMonitor(data, callback)

        headers = {"Content-type": monitor.content_type}

        return self.session.post(
            url=f"https:{best_server}", data=monitor, headers=headers
        ).json()

    def launch_transco(self, file_url):
        file_id = file_url.split("https://uptobox.com/")[1]
        return self.session.get(self.endpoints["transco"] + file_id).json()


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="uptobox-upload-v1",
    )
    parser.add_argument("-i", "--input", help="file to upload")
    args = parser.parse_args()

    if args:
        uptobox = Uptobox()
        best_server = uptobox.get_best_server()

        if "data" in best_server:
            if "uploadLink" in best_server["data"]:
                upload = uptobox.upload(best_server["data"]["uploadLink"], args.input)
                if "files" in upload:
                    if "url" in upload["files"][0]:
                        transco = uptobox.launch_transco(upload["files"][0]["url"])
