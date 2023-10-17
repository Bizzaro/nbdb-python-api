took 12 hours to figure this out
- protected by akamai 
- already knew by doing a lookup on the API domain name
- old library used a cloudflare library... which was weird since no FI uses cloudflare, too modern
- they all use akamai (correct)
- tried reverse-engineering the login flow but it is heavily protected via akamai for the login
- for the API routes, there is extra security, not only authorization header but also X-External-User-Context-Token, luckily this one has a longer expiry
- 

crude-attempt at reversing the cookie flow... 
https://www.zenrows.com/blog/bypass-akamai

![Alt text](image-1.png)