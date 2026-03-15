FROM node:20-alpine

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 9002

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
