FROM nginx:1.28.0

ARG ENV=production
ENV NODE_ENV=${ENV}

RUN rm /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
