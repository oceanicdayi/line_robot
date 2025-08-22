# 使用輕量級的 Python 3.10 作為基礎映像
FROM python:3.10-slim

# 將工作目錄設定為 /code
WORKDIR /code

# 複製 requirements.txt 並安裝依賴套件
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 複製所有專案檔案到容器的 /code 目錄中
COPY . /code/

# [修正] 設定啟動指令，並增加 --timeout 參數
# 將逾時時間延長至 120 秒，以允許 AI 模型在 CPU 上有足夠的時間載入
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:7860", "--timeout", "120", "app:app"]
