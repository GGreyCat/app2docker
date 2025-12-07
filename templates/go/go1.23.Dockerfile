# Go 1.23 应用 Dockerfile
# 多阶段构建，优化镜像大小
# 使用阿里云镜像源加速下载

# 构建阶段
FROM golang:1.23-alpine AS builder

# 设置工作目录
WORKDIR /build

# 设置 Go 环境变量
ENV GO111MODULE=on \
    GOPROXY=https://goproxy.cn,direct \
    CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64

# 安装必要的构建工具
RUN apk add --no-cache git

# 复制 go.mod 和 go.sum（如果存在）
COPY go.mod go.sum* ./

# 下载依赖
RUN if [ -f go.mod ]; then go mod download; fi

# 复制源代码
COPY . .

# 编译应用
RUN go build -ldflags="-s -w" -o /app/main .

# 运行阶段
FROM alpine:latest

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apk del tzdata

# 安装 ca-certificates（用于 HTTPS 请求）
RUN apk add --no-cache ca-certificates

# 设置工作目录
WORKDIR /app

# 从构建阶段复制编译好的二进制文件
COPY --from=builder /app/main .

# 暴露端口
EXPOSE {{EXPOSE_PORT:8080}}

# 运行应用
CMD ["./main"]
