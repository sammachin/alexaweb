# alexaweb

Alexa in The Browser, see https://alexaweb.herokuapp.com for a demo

## Notes
The client uses getUserMedia to access the microphone, this mean it will only work in Chrome, Firefox, Opera and Edge, no IE and no Safari Support, also the latest version of Chrome requires that the page be served via https for anything other than localhost, running from Heroku is therefore useful ;)

## Setup
This app was built for Heroku, if you want to run locally or on another platform you will require Python 2.7 and a local install of Redis, you will then need to install the modules listed in requirements.txt
### Download this repo

`git clone git@github.com:sammachin/alexaweb.git`

make a note of your app name and if you want to rename it with
`heroku apps:rename [yourappname]`

### Create a new Heroku app (optional)

`heroku create`
 Add redis
 `heroku addons:create heroku-redis:hobby-dev`

### Get AVS Credentials

Next you need to obtain a set of credentials from Amazon to use the Alexa Voice service, login at http://developer.amazon.com and Goto Alexa then Alexa Voice Service

You need to create a new product type as an Application, for the ID use something like samsalexaweb, create a new security profile and under the web settings allowed origins put http://localhost:5000 and as a return URL put  http://localhost:5000/code also if you are deploying to heroku add the heroku app url in addition to localhost:5000

Once you've got the security credentials put them into the creds.py file.

### Deploy

`git add creds.py
git commit -m "updated creds"
git push heroku master`

### Run
`heroku open`

## Enjoy
