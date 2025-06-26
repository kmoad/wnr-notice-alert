# Running

Create a subdirectory `data`. Place file `config.json` in it.

Format of config.json

```json
{
	"yachtscoring_url": "https://api.yachtscoring.com/v1/public/event/50166/news?isNoticeBoard_eq=true&page=1&size=10",
	"gmail_user": "you@example.com",
	"gmail_app_password": "See https://support.google.com/mail/answer/185833?hl=en",
	"sender_name": "Your name (for email display)",
	"recipients": [
		"person1@example.com",
		"person2@example.com"
	]
}
```

Either run it natively 

```bash
python3 wnr-notice-alert.py
```

Or using docker

```bash
docker compose run --rm wnr-notice-alert
```

The last sent notice will be stored in `data/last-sent-notice.json`. Remove it to resend the same message.
