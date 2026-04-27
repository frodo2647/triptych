FROM node:20

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages matplotlib numpy scipy sympy plotly pandas

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm install -g @anthropic-ai/claude-code@latest

# Create workspace directories (server expects them to exist)
RUN mkdir -p workspace/output workspace/files workspace/snapshots workspace/research

EXPOSE 3000

CMD ["npx", "tsx", "server/index.ts"]
