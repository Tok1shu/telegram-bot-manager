# Telegram Bot Manager ❗MVP❗

This bot was made for subdomain redirects. (like `rickroll.r.tokishu.net` -> `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
I made this bot relatively long ago, just for testing, and did not check it on CloudFlare, so I do not guarantee its functionality, but in theory it should work.
## Instructions
download these 4 files, then customize the config for yourself, create a bot and insert its API key, specify your domain in the `*.r.yourdomain.com` format, and also `r.yourdomain.com`.
after that start the bot, and try connect by domain `test.r.yourdomain.com`, if you see this
![image](https://github.com/user-attachments/assets/b7caf60c-7c4b-4a18-9ce7-9596924f8e01) <br>
then it working, try create redirect, and use it :3

## And API
I almost forgot, also bot have API
`GET r.yourdomain.com/health` - Check bot status
Returns
```json
{
    "status": "healthy",
    "timestamp": "2025-02-15T02:11:49.610564"
}
```

and `GET r.yourdomain.com/stats/{subdomain}` - Get stats (with administrator API key)
HEADER: `X-API-Key` -> `your api key`
returns
```json
{
    "subdomain": "test",
    "url": "https://tokishu.net",
    "stats": {
        "clicks": 0,
        "last_click": null,
        "referrers": {},
        "user_agents": {},
        "countries": {}
    }
}
```

##
REMEMBER!
This bot has a some bugs! Maybe i'll fix it, but not now
---

## EXAMPLE
### Creating redirect
![Bot1](https://github.com/user-attachments/assets/fa753eba-e9e0-4363-9c4b-19df1bd42afb)

### Using redirect

![Bot2](https://github.com/user-attachments/assets/da800abb-658b-47aa-9d45-724510b79902)

### Stats

![image](https://github.com/user-attachments/assets/2760b7b5-414d-465b-82ea-83bc67d3cc45)

### 404 Page

![image](https://github.com/user-attachments/assets/aa50c375-c3d5-4672-abc3-5462958d99e1)
