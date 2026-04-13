FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN yarn install

COPY . .

# REACT_APP_* vars must be set at build time for CRA
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

EXPOSE 3000

CMD ["yarn", "start"]
