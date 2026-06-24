# FROM nginx:alpine
FROM nginx:1.28.0

ARG ENV=production
ENV NODE_ENV=${ENV}

# 清理默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制所有静态文件到 Nginx 根目录
COPY dist/ /usr/share/nginx/html/

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 设置权限（确保 Nginx 可读）
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
