FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN COOKIE_SECRET=build-placeholder npm run build
ENV NODE_ENV=production
ENV PORT=3002
EXPOSE 3002
CMD ["npm", "start"]
