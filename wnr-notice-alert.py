import requests
import json
import smtplib
from email.message import Message
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from pathlib import Path


class YachtScoringNotice:

	def __init__(self, notice_data: dict):
		self._notice_data = notice_data
		self.notice_id = self._notice_data['id']
		self.news_body = self._notice_data['newsBody']
		self.news_subject = self._notice_data['newsSubject']
		self.posted_dt = datetime.fromisoformat(self._notice_data['newsDateTime'])

	def to_email(self) -> MIMEText:
		msg = MIMEText(self.news_body, 'html')
		msg['Subject'] = f'WNR Notice: {self.news_subject}'
		return msg

class NoticeBoard:

	_last_sent_path = Path('data/last-sent-notice.json')
	
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
		for notice_data in r.json()['rows']:
			self.notices.append(
				YachtScoringNotice(notice_data)
			)
	
	@property
	def new_notice_available(self) -> bool:
		if self._last_sent_notice is None:
			return True
		latest_notice = self.notices[0]
		return \
			latest_notice.notice_id != self._last_sent_notice.notice_id \
			and \
			latest_notice.posted_dt > self._last_sent_notice.posted_dt

	def mark_sent(self, notice: YachtScoringNotice):
		self._last_sent_path.write_text(json.dumps(notice._notice_data))
	
	
class EmailSender:
	
	def __init__(self, gmail_user: str, gmail_app_password: str, sender_name: str):
		self._gmail_user = gmail_user
		self._gmail_app_password = gmail_app_password
		self._sender_name = sender_name
		self._from_addr = formataddr(
			(self._sender_name, self._gmail_user)
		)
		self._server = smtplib.SMTP('smtp.gmail.com', 587)
		self._server.starttls()
		self._server.login(self._gmail_user, self._gmail_app_password)
				  
	def send_message(self, msg: Message, recipients: list[str]):
		msg['From'] = self._from_addr
		msg['To'] = ','.join(recipients)
		self._server.send_message(msg)


def main():
	config_path = Path('data/config.json')
	config = json.loads(config_path.read_text())
	nb = NoticeBoard(config['yachtscoring_url'])
	nb.fetch()
	if nb.new_notice_available:
		sender = EmailSender(
			config['gmail_user'],
			config['gmail_app_password'],
			config['sender_name'],
		)
		latest_notice = nb.notices[0]
		sender.send_message(latest_notice.to_email(), config['recipients'], )
		nb.mark_sent(latest_notice)
		print(f'Notice sent: {latest_notice.news_subject}')
	else:
		print('No new notice')

if __name__ == '__main__':
	main()