"""
Upload emails from an MBOX archive to Loop
"""
import base64
from argparse import ArgumentParser, FileType
from email.utils import parsedate_to_datetime
from mailbox import mbox

from requests import post


def main() -> None:
    """
    Entrypoint for script
    """
    parser = ArgumentParser(
        description="Upload emails from an MBOX archive to Loop",
        allow_abbrev=False,
    )
    parser.add_argument(
        "mbox_archive",
        help="the MBOX archive to upload",
        type=FileType("r"),
    )
    parser.add_argument(
        "--endpoint",
        help="the Loop endpoint to target",
        required=True,
    )
    parser.add_argument(
        "--username",
        help="the username to use to authenticate to Loop",
        required=True,
    )
    parser.add_argument("--password", help="the password to use to authenticate to Loop", required=True)
    args = parser.parse_args()

    mailbox = mbox(args.mbox_archive.name, create=False)

    interesting_emails = []

    for mail in mailbox:
        if "dse_NA3@docusign.net" in mail.get("From"):
            for part in mail.walk():
                if part.get_content_type() in [
                    "application/pdf",
                    "application/octet-stream",
                ]:
                    print("Adding email from " + mail.get("Date"))
                    interesting_emails.append(mail)
                    break

    interesting_emails.sort(key=lambda m: parsedate_to_datetime(m.get("Date")))  # type: ignore

    for mail in interesting_emails:
        postmark_format = {
            "Subject": mail.get("Subject"),
            "Attachments": [],
            "Date": mail.get("Date"),
        }
        for part in mail.walk():
            if part.get_content_type() in [
                "application/pdf",
                "application/octet-stream",
            ]:
                postmark_format["Attachments"].append(
                    {
                        "Name": part.get_filename(),
                        "Content": base64.b64encode(part.get_payload(decode=True)).decode("utf-8"),
                    }
                )
        loop_response = post(args.endpoint, json=postmark_format, auth=(args.username, args.password), timeout=10)
        print(loop_response.text)
        if input("Send next envelope? ") != "y":
            print("Exiting")
            break


if __name__ == "__main__":
    main()
