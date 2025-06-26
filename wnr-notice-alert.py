import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from pathlib import Path


class YachtScoringNotice:

	def __init__(self, notice_data: dict):
		self.notice_data = notice_data
		self.notice_id = self.notice_data['id']
		self.news_body = self.notice_data['newsBody']
		self.news_subject = self.notice_data['newsSubject']
		self.posted_dt = datetime.fromisoformat(self.notice_data['newsDateTime'])


class NoticeBoard:

	_last_sent_path = Path('last-sent-notice.json')
	
	def __init__(self, yachtscoring_url: str):
		# URL as of 2025-06-25: https://api.yachtscoring.com/v1/public/event/50166/news?isNoticeBoard_eq=true&page=1&size=10
		self._yachtscoring_url = yachtscoring_url
		self.notices = []
		if self._last_sent_path.exists():
			self._last_sent_notice = YachtScoringNotice(
				json.loads(self._last_sent_path.read_text())
			)
		else:
			self._last_sent_notice = None

	def fetch(self):
		r = requests.get(self._yachtscoring_url)
		r.raise_for_status()
		notices_data = r.json()
		for notice_data in notices_data['rows']:
			self.notices.append(
				YachtScoringNotice(notice_data)
			)
	
	@property
	def latest_is_sent(self) -> bool:
		if self._last_sent_notice is None:
			return False
		latest_notice = self.notices[0]
		id_match = latest_notice.notice_id == self._last_sent_notice.notice_id
		is_later = latest_notice.posted_dt > self._last_sent_notice.posted_dt
		return id_match and not(is_later)

	def mark_sent(self, notice: YachtScoringNotice):
		self._last_sent_path.write_text(json.dumps(notice.notice_data))
	
	
class EmailSender:
	
	def __init__(self, gmail_user: str, gmail_app_password: str, sender_name: str):
		self._gmail_user = gmail_user
		self._gmail_app_password = gmail_app_password
		self._sender_name = sender_name
		self._from_addr = formataddr(
			(self._sender_name, self._gmail_user)
		)
				  
	def send_message(self, recipients: list[str], subject: str, body: str):
		msg = MIMEMultipart()
		msg['From'] = self._from_addr
		msg['To'] = ','.join(recipients)
		msg['Subject'] = subject
		msg.attach(MIMEText(body, 'html'))
		
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()  # Enable encryption
		server.login(self._gmail_user, self._gmail_app_password)
		server.send_message(msg)
		server.quit()


def main():
	with open('config.json') as f:
		config = json.loads(f.read())
	nb = NoticeBoard(config['yachtscoring_url'])
	nb.fetch()
	if nb.latest_is_sent:
		print('No new notice')
	else:
		print('Sending notice')
		sender = EmailSender(
			config['gmail_user'],
			config['gmail_app_password'],
			config['sender_name'],
		)
		latest_notice = nb.notices[0]
		subject = f'WNR Notice: {latest_notice.news_subject}'
		body = latest_notice.news_body
		sender.send_message(config['recipients'], subject, body)
		nb.mark_sent(latest_notice)
		print('Notice sent')

if __name__ == '__main__':
	main()