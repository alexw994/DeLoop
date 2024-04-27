# Build Deloop frontend
FROM node:17.9.1-alpine AS builder

WORKDIR /web
COPY src/web /web
RUN npm install && \
    npm run build

CMD ["npm", "run", "preview"]