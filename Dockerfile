FROM nikolaik/python-nodejs:python3.8-nodejs16

LABEL "com.github.actions.name"="Comment Webpage Screenshot"
LABEL "com.github.actions.description"="Capture Webpage Screenshots and Comment on Pull Request."
LABEL "com.github.actions.icon"="image"
LABEL "com.github.actions.color"="blue"

LABEL "repository"="https://github.com/saadmk11/comment-webpage-screenshot"
LABEL "homepage"="https://github.com/saadmk11/comment-webpage-screenshot"
LABEL "maintainer"="saadmk11"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wget \
       gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       fonts-liberation \
       libappindicator3-1 \
       libasound2 \
       libatk-bridge2.0-0 \
       libatk1.0-0 \
       libc6 \
       libcairo2 \
       libcups2 \
       libdbus-1-3 \
       libexpat1 \
       libfontconfig1 \
       libgbm1 \
       libgcc1 \
       libglib2.0-0 \
       libgtk-3-0 \
       libnspr4 \
       libnss3 \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libstdc++6 \
       libx11-6 \
       libx11-xcb1 \
       libxcb1 \
       libxcomposite1 \
       libxcursor1 \
       libxdamage1 \
       libxext6 \
       libxfixes3 \
       libxi6 \
       libxrandr2 \
       libxrender1 \
       libxss1 \
       libxtst6 \
       lsb-release \
       xdg-utils \
       libxshmfence-dev \
       google-chrome-stable  \
       fonts-ipafont-gothic \
       fonts-wqy-zenhei \
       fonts-thai-tlwg \
       fonts-kacst \
       fonts-freefont-ttf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --global capture-website-cli

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "/scripts/main.py"]
