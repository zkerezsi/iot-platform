FROM node:18.16-alpine3.17 AS install
WORKDIR /app
COPY package.json .
COPY package-lock.json .
RUN npm ci

FROM node:18.16-alpine3.17 AS build
WORKDIR /app
COPY --from=install /app/node_modules /app/node_modules
COPY . .
RUN npm run build

FROM nginx:1.24-alpine
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html