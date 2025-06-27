import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils import get_subscribers
from dotenv import load_dotenv
from sendgrid.helpers.mail import Asm
import sys
import json
from jinja2 import Environment, FileSystemLoader
from premailer import transform





def prepare_newsletter():
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("newsletter_template.html")
    with open("movies_data.json", "r", encoding="utf-8") as f:
        movie_data = json.load(f)


    with open("shows_data.json", "r", encoding="utf-8") as f:
        shows_data = json.load(f)
    

    rendered_html = template.render(movies=movie_data, shows=shows_data)
    inlined_html = transform(rendered_html)

    output_file = "newsletter.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(inlined_html)

    print(f"✅ Newsletter generated: {output_file}")


def send_newsletter(is_test: bool = False):

    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    LIST_ID = os.getenv("LIST_ID") 
    recipients = [os.getenv("TEST_EMAIL_RECIPIENT")]
    with open("newsletter.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    subject = "The Final Cut Newsletter"
    if not is_test:
        recipients = get_subscribers(SENDGRID_API_KEY, LIST_ID)

    print(f"Sending newsletter to: {recipients}")
    for recipient in recipients:
        message = Mail(
            from_email=os.getenv("FROM_EMAIL"),
            to_emails=recipient,
            subject=subject,
            html_content=html_content
        )
        message.asm = Asm(group_id=int(os.getenv("UNSUBSCRIBE_GROUP_ID")))
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(f"✅ Sent to {recipient} | Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending to {recipient}: {e}")


if __name__ == "__main__":
    load_dotenv(override=True)
    is_test = False
    if len(sys.argv) > 1:
        is_test = sys.argv[1] == "test"

    try: 
        prepare_newsletter()
    except Exception as e:
        print(f"❌ Error preparing newsletter: {e}")

    send_newsletter(is_test)